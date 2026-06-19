"""
AgentObserver — Core Monitoring Engine
Intercepts every agent step, detects failures, logs behavior.
Now with: Retry mechanism with exponential backoff!
"""

import time
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class StepStatus(Enum):
    SUCCESS = "success"
    LOOP_DETECTED = "loop_detected"
    TOOL_FAILURE = "tool_failure"
    TIMEOUT = "timeout"
    HALLUCINATION_RISK = "hallucination_risk"
    EMPTY_OUTPUT = "empty_output"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class AgentStep:
    def __init__(self, step_number: int, action: str, input_data: Any, output_data: Any, duration: float):
        self.id = str(uuid.uuid4())[:8]
        self.step_number = step_number
        self.action = action
        self.input_data = input_data
        self.output_data = output_data
        self.duration = duration
        self.timestamp = datetime.now().isoformat()
        self.status: StepStatus = StepStatus.SUCCESS
        self.failure_reason: Optional[str] = None
        self.retry_count: int = 0  # how many times this step was retried

    def to_dict(self):
        return {
            "id": self.id,
            "step_number": self.step_number,
            "action": self.action,
            "input": str(self.input_data)[:300],
            "output": str(self.output_data)[:300],
            "duration_ms": round(self.duration * 1000, 2),
            "timestamp": self.timestamp,
            "status": self.status.value,
            "failure_reason": self.failure_reason,
            "retry_count": self.retry_count,
        }


class AgentObserver:
    """
    Wraps any agent function and monitors its behavior step by step.
    Detects: loops, timeouts, tool failures, hallucination risks, empty outputs.
    Retries: automatically retries failed steps with exponential backoff.
    """

    def __init__(
        self,
        agent_name: str = "Agent",
        timeout_threshold: float = 10.0,
        loop_threshold: int = 3,
        max_retries: int = 3,
        retry_delay: float = 1.0,  # base delay in seconds (doubles each retry)
    ):
        self.agent_name = agent_name
        self.timeout_threshold = timeout_threshold
        self.loop_threshold = loop_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.steps: list[AgentStep] = []
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = None
        self.total_failures = 0
        self.total_retries = 0

    def monitor_step(self, action: str, func: Callable, *args, **kwargs) -> Any:
        """
        Wrap any agent tool call with this to monitor it.
        Automatically retries on failure with exponential backoff.
        Usage: result = observer.monitor_step("web_search", search_fn, query="AI agents")
        """
        step_number = len(self.steps) + 1
        input_data = args[0] if args else kwargs
        retry_count = 0
        last_error = None
        output_data = None

        while retry_count <= self.max_retries:
            start = time.time()
            error = None
            output_data = None

            try:
                output_data = func(*args, **kwargs)
            except Exception as e:
                error = str(e)
                last_error = error
                output_data = None

            duration = time.time() - start

            # Create step object
            step = AgentStep(step_number, action, input_data, output_data, duration)
            step.retry_count = retry_count

            # Run failure detection
            self._detect_failures(step, error)

            # If success — log and return
            if step.status == StepStatus.SUCCESS:
                if retry_count > 0:
                    print(f"Step #{step_number} recovered after {retry_count} retry/retries!")
                    self.total_retries += retry_count
                self.steps.append(step)
                return output_data

            # If loop detected — don't retry, it won't help
            if step.status == StepStatus.LOOP_DETECTED:
                self.steps.append(step)
                self.total_failures += 1
                self._print_alert(step)
                return output_data

            # If failed and retries remaining — wait and retry
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)  # exponential backoff: 1s, 2s, 4s
                print(f"Step #{step_number} failed ({step.status.value}) — retrying in {wait_time:.1f}s... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                retry_count += 1

            else:
                # Max retries exceeded
                step.status = StepStatus.MAX_RETRIES_EXCEEDED
                step.failure_reason = f"Failed after {self.max_retries} retries. Last error: {last_error or step.failure_reason}"
                self.steps.append(step)
                self.total_failures += 1
                self.total_retries += retry_count
                self._print_alert(step)
                return output_data

        return output_data

    def _detect_failures(self, step: AgentStep, error: Optional[str]):
        """Core failure detection logic — the heart of AgentObserver."""

        # 1. Tool failure — exception was raised
        if error:
            step.status = StepStatus.TOOL_FAILURE
            step.failure_reason = f"Tool raised exception: {error}"
            return

        # 2. Empty output — agent produced nothing
        if step.output_data is None or str(step.output_data).strip() == "":
            step.status = StepStatus.EMPTY_OUTPUT
            step.failure_reason = "Agent step returned empty or None output"
            return

        # 3. Timeout — step took too long
        if step.duration > self.timeout_threshold:
            step.status = StepStatus.TIMEOUT
            step.failure_reason = f"Step exceeded timeout threshold ({self.timeout_threshold}s). Took {step.duration:.2f}s"
            return

        # 4. Loop detection — same action repeated with same input
        recent_steps = self.steps[-self.loop_threshold:]
        same_action_steps = [s for s in recent_steps if s.action == step.action]
        if len(same_action_steps) >= self.loop_threshold:
            recent_inputs = [str(s.input_data)[:100] for s in same_action_steps]
            if len(set(recent_inputs)) == 1:
                step.status = StepStatus.LOOP_DETECTED
                step.failure_reason = f"Agent repeated '{step.action}' {self.loop_threshold}x with identical input — likely stuck in a loop"
                return

        # 5. Hallucination risk — output contains contradiction signals
        output_str = str(step.output_data).lower()
        contradiction_signals = [
            ("i don't know", "i know"),
            ("no information", "the answer is"),
            ("cannot find", "found that"),
        ]
        for signal_a, signal_b in contradiction_signals:
            if signal_a in output_str and signal_b in output_str:
                step.status = StepStatus.HALLUCINATION_RISK
                step.failure_reason = f"Output contains contradictory statements: '{signal_a}' and '{signal_b}' both present"
                return

    def _print_alert(self, step: AgentStep):
        """Print a clear, human-readable alert when a failure is detected."""
        print(f"\n{'='*55}")
        print(f"AGENT OBSERVER ALERT — {self.agent_name}")
        print(f"{'='*55}")
        print(f"  Step     : #{step.step_number} — {step.action}")
        print(f"  Status   : {step.status.value.upper()}")
        print(f"  Reason   : {step.failure_reason}")
        print(f"  Retries  : {step.retry_count}")
        print(f"  Duration : {step.duration*1000:.0f}ms")
        print(f"  Time     : {step.timestamp}")
        print(f"{'='*55}\n")

    def get_session_summary(self) -> dict:
        """Returns a full summary of the agent session."""
        total = len(self.steps)
        failures = [s for s in self.steps if s.status != StepStatus.SUCCESS]
        failure_types = {}
        for s in failures:
            key = s.status.value
            failure_types[key] = failure_types.get(key, 0) + 1

        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "total_steps": total,
            "successful_steps": total - len(failures),
            "failed_steps": len(failures),
            "failure_rate": f"{(len(failures)/total*100):.1f}%" if total > 0 else "0%",
            "total_retries": self.total_retries,
            "failure_breakdown": failure_types,
            "steps": [s.to_dict() for s in self.steps],
        }

    def save_log(self, path: str = "logs/session.json"):
        """Save full session log to JSON."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        summary = self.get_session_summary()
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Session log saved to {path}")
        return summary
