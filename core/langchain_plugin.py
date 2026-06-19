"""
AgentObserver — LangChain Plugin
Drop-in callback handler for any LangChain agent.
Just add AgentObserverCallback() to your agent's callbacks list.

Usage:
    from core.langchain_plugin import AgentObserverCallback

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        callbacks=[AgentObserverCallback()]
    )
"""

import time
import uuid
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from core.hallucination_scorer import HallucinationScorer
from core.observer import StepStatus


class AgentObserverCallback(BaseCallbackHandler):
    """
    LangChain callback handler that automatically monitors any LangChain agent.

    Hooks into:
    - on_tool_start / on_tool_end / on_tool_error  → tool call monitoring
    - on_llm_start / on_llm_end                    → LLM call monitoring
    - on_agent_action / on_agent_finish             → agent step tracking
    - on_chain_error                                → chain-level failure detection

    Auto-detects:
    - Tool failures and errors
    - LLM timeouts
    - Hallucination risk in LLM outputs
    - Repeated tool calls (loop detection)
    """

    def __init__(
        self,
        agent_name: str = "LangChainAgent",
        timeout_threshold: float = 10.0,
        loop_threshold: int = 3,
        hallucination_threshold: int = 50,  # score below this = flag it
        save_log: bool = True,
        log_dir: str = "logs",
        verbose: bool = True,
    ):
        super().__init__()
        self.agent_name = agent_name
        self.timeout_threshold = timeout_threshold
        self.loop_threshold = loop_threshold
        self.hallucination_threshold = hallucination_threshold
        self.save_log = save_log
        self.log_dir = log_dir
        self.verbose = verbose

        # Session state
        self.session_id = str(uuid.uuid4())[:8]
        self.steps = []
        self.tool_call_times = {}       # tool_name → start time
        self.tool_call_history = []     # for loop detection
        self.total_failures = 0
        self.total_retries = 0

        self.scorer = HallucinationScorer()

        if self.verbose:
            print(f"\nAgentObserver active — Session {self.session_id} | Agent: {self.agent_name}\n")

    # ── Tool Hooks ─────────────────────────────────────────────────

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Called when a tool is about to be used."""
        tool_name = serialized.get("name", "unknown_tool")
        self.tool_call_times[tool_name] = time.time()

        # Loop detection — same tool, same input repeated
        self.tool_call_history.append((tool_name, input_str[:100]))
        recent = self.tool_call_history[-self.loop_threshold:]
        if len(recent) == self.loop_threshold:
            if len(set(recent)) == 1:
                self._log_step(
                    action=tool_name,
                    input_data=input_str,
                    output_data=None,
                    status=StepStatus.LOOP_DETECTED,
                    failure_reason=f"Tool '{tool_name}' called {self.loop_threshold}x with identical input — agent stuck in loop",
                    duration=0,
                )

    def on_tool_end(self, output: str, **kwargs):
        """Called when a tool completes successfully."""
        # Find which tool just finished
        if self.tool_call_times:
            tool_name = list(self.tool_call_times.keys())[-1]
            duration = time.time() - self.tool_call_times.pop(tool_name, time.time())

            # Check for timeout
            if duration > self.timeout_threshold:
                self._log_step(
                    action=tool_name,
                    input_data="(see previous on_tool_start)",
                    output_data=output,
                    status=StepStatus.TIMEOUT,
                    failure_reason=f"Tool '{tool_name}' exceeded timeout ({self.timeout_threshold}s). Took {duration:.2f}s",
                    duration=duration,
                )
            else:
                self._log_step(
                    action=tool_name,
                    input_data="(see previous on_tool_start)",
                    output_data=output,
                    status=StepStatus.SUCCESS,
                    failure_reason=None,
                    duration=duration,
                )

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Called when a tool raises an error."""
        tool_name = list(self.tool_call_times.keys())[-1] if self.tool_call_times else "unknown_tool"
        duration = time.time() - self.tool_call_times.pop(tool_name, time.time())

        self._log_step(
            action=tool_name,
            input_data="(see previous on_tool_start)",
            output_data=None,
            status=StepStatus.TOOL_FAILURE,
            failure_reason=f"Tool raised exception: {str(error)}",
            duration=duration,
        )

    # ── LLM Hooks ──────────────────────────────────────────────────

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts generating."""
        self._llm_start_time = time.time()

    def on_llm_end(self, response: LLMResult, **kwargs):
        """Called when LLM finishes — check for hallucination risk."""
        duration = time.time() - getattr(self, "_llm_start_time", time.time())

        # Extract text output
        output_text = ""
        if response.generations:
            output_text = response.generations[0][0].text if response.generations[0] else ""

        # Score for hallucination
        if output_text:
            report = self.scorer.score(output_text)
            if report.score < self.hallucination_threshold:
                self._log_step(
                    action="llm_generation",
                    input_data="(LLM prompt)",
                    output_data=output_text[:200],
                    status=StepStatus.HALLUCINATION_RISK,
                    failure_reason=f"LLM output scored {report.score}/100 hallucination risk. Flags: {report.flags[:2]}",
                    duration=duration,
                )
                if self.verbose:
                    print(f"Hallucination Score: {report.score}/100 ({report.risk_level} RISK)")
            else:
                if self.verbose:
                    print(f"Hallucination Score: {report.score}/100 ")

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Called when LLM raises an error."""
        duration = time.time() - getattr(self, "_llm_start_time", time.time())
        self._log_step(
            action="llm_generation",
            input_data="(LLM prompt)",
            output_data=None,
            status=StepStatus.TOOL_FAILURE,
            failure_reason=f"LLM raised exception: {str(error)}",
            duration=duration,
        )

    # ── Agent Hooks ────────────────────────────────────────────────

    def on_agent_finish(self, finish, **kwargs):
        """Called when agent completes — save final log."""
        if self.verbose:
            print(f"\n{'='*55}")
            print(f"AgentObserver Session Complete — {self.agent_name}")
            print(f"{'='*55}")
            print(f"  Session ID    : {self.session_id}")
            print(f"  Total Steps   : {len(self.steps)}")
            failed = [s for s in self.steps if s["status"] != "success"]
            print(f"  Failed Steps  : {len(failed)}")
            rate = (len(failed) / len(self.steps) * 100) if self.steps else 0
            print(f"  Failure Rate  : {rate:.1f}%")
            print(f"{'='*55}\n")

        if self.save_log:
            self._save_session_log()

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Called when the chain itself errors out."""
        self._log_step(
            action="chain",
            input_data="(chain input)",
            output_data=None,
            status=StepStatus.TOOL_FAILURE,
            failure_reason=f"Chain-level error: {str(error)}",
            duration=0,
        )
        if self.save_log:
            self._save_session_log()

    # ── Internal helpers ───────────────────────────────────────────

    def _log_step(self, action, input_data, output_data, status, failure_reason, duration):
        """Log a step internally and print alert if failure."""
        step = {
            "id": str(uuid.uuid4())[:8],
            "step_number": len(self.steps) + 1,
            "action": action,
            "input": str(input_data)[:200],
            "output": str(output_data)[:200] if output_data else None,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.now().isoformat(),
            "status": status.value,
            "failure_reason": failure_reason,
        }
        self.steps.append(step)

        if status != StepStatus.SUCCESS and self.verbose:
            print(f"\n{'='*55}")
            print(f"AGENT OBSERVER ALERT — {self.agent_name}")
            print(f"{'='*55}")
            print(f"  Step   : #{step['step_number']} — {action}")
            print(f"  Status : {status.value.upper()}")
            print(f"  Reason : {failure_reason}")
            print(f"{'='*55}\n")
            self.total_failures += 1

    def _save_session_log(self):
        """Save session log to JSON."""
        os.makedirs(self.log_dir, exist_ok=True)
        path = f"{self.log_dir}/langchain_session_{self.session_id}.json"
        failed = [s for s in self.steps if s["status"] != "success"]
        summary = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "total_steps": len(self.steps),
            "successful_steps": len(self.steps) - len(failed),
            "failed_steps": len(failed),
            "failure_rate": f"{(len(failed)/len(self.steps)*100):.1f}%" if self.steps else "0%",
            "steps": self.steps,
        }
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"LangChain session log saved to {path}")

    def get_summary(self) -> dict:
        """Get current session summary."""
        failed = [s for s in self.steps if s["status"] != "success"]
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "total_steps": len(self.steps),
            "failed_steps": len(failed),
            "failure_rate": f"{(len(failed)/len(self.steps)*100):.1f}%" if self.steps else "0%",
            "steps": self.steps,
        }
