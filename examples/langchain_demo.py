"""
AgentObserver — LangChain Plugin Demo
Shows how to use AgentObserverCallback with any LangChain agent.
This demo simulates LangChain callbacks without needing an actual LLM API key.

Run: python examples/langchain_demo.py
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.langchain_plugin import AgentObserverCallback
from core.observer import StepStatus
from langchain_core.outputs import LLMResult, Generation


def simulate_langchain_agent():
    """
    Simulates what happens inside a LangChain agent run.
    In real usage, LangChain calls these hooks automatically.
    """

   
    print("   AGENTOBSERVER — LANGCHAIN PLUGIN DEMO")
   

    # ── Initialize the callback ────────────────────────────────────
    callback = AgentObserverCallback(
        agent_name="ResearchAgent-LangChain",
        timeout_threshold=5.0,
        loop_threshold=3,
        hallucination_threshold=50,
    )

    print("Simulating LangChain agent run...\n")

    # ── Simulate: LLM call with trustworthy output ─────────────────
    print("► LLM generating research plan...")
    callback.on_llm_start({}, ["Research AI agent trends in 2026"])
    time.sleep(0.3)
    good_response = LLMResult(generations=[[Generation(
        text="According to Gartner's 2026 report, 78% of companies have AI agent pilots running. "
             "The market is expected to reach $47 billion by 2028, growing at 34% CAGR. "
             "Key players include Anthropic, OpenAI, and Google DeepMind."
    )]])
    callback.on_llm_end(good_response)

    # ── Simulate: Tool call — web search success ───────────────────
    print("► Tool: web_search...")
    callback.on_tool_start({"name": "web_search"}, "AI agent market size 2026")
    time.sleep(0.4)
    callback.on_tool_end("Found 12 relevant articles on AI agent market trends.")

    # ── Simulate: Tool call — tool failure ────────────────────────
    print("► Tool: database_lookup (will fail)...")
    callback.on_tool_start({"name": "database_lookup"}, "enterprise_ai_stats")
    time.sleep(0.1)
    callback.on_tool_error(Exception("Database connection refused — timeout after 30s"))

    # ── Simulate: LLM with hallucination risk ─────────────────────
    print("► LLM generating summary (risky output)...")
    callback.on_llm_start({}, ["Summarize findings"])
    time.sleep(0.2)
    risky_response = LLMResult(generations=[[Generation(
        text="I think maybe AI agents are probably going to be important. "
             "Perhaps companies might possibly adopt this technology. "
             "I'm not sure but it could be significant or maybe not."
    )]])
    callback.on_llm_end(risky_response)

    # ── Simulate: Tool timeout ─────────────────────────────────────
    print("► Tool: slow_analysis (will timeout)...")
    callback.on_tool_start({"name": "slow_analysis"}, "deep market analysis")
    time.sleep(6)  # exceeds 5s threshold
    callback.on_tool_end("Analysis complete.")

    # ── Simulate: Loop detection ───────────────────────────────────
    print("► Tool: web_search repeated 3x (loop)...")
    for _ in range(3):
        callback.on_tool_start({"name": "web_search"}, "same query stuck")
        time.sleep(0.1)
        callback.on_tool_end("Same results as before.")

    # ── Agent finishes ─────────────────────────────────────────────
    from langchain_core.agents import AgentFinish
    callback.on_agent_finish(AgentFinish(
        return_values={"output": "Research complete."},
        log="Agent finished successfully."
    ))

    return callback.get_summary()


if __name__ == "__main__":
    summary = simulate_langchain_agent()
    print("\n Real usage in your LangChain project:")
    print("─" * 50)
    print("""
from core.langchain_plugin import AgentObserverCallback

# Just add this one line to any existing LangChain agent:
callback = AgentObserverCallback(agent_name="MyAgent")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    callbacks=[callback]   # ← that's it!
)

agent.run("Your task here")
""")
