"""
AgentComparator — Demo
Compares two agents: a "Reliable Agent" vs a "Flaky Agent"
on the same set of tasks.

Run: python examples/compare_demo.py
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.comparator import AgentComparator

# ── Simulated tools for Agent A (Reliable) ────────────────────────

def reliable_search(query: str) -> str:
    time.sleep(0.3)
    return f"[ReliableAgent] Results for '{query}': Found 8 high-quality articles."

def reliable_summarize(text: str) -> str:
    time.sleep(0.2)
    return f"[ReliableAgent] Summary: {text[:60]}..."

def reliable_analyze(query: str) -> str:
    time.sleep(0.5)
    return f"[ReliableAgent] Analysis complete for: {query}"

# ── Simulated tools for Agent B (Flaky) ───────────────────────────

flaky_call_count = {"search": 0}

def flaky_search(query: str) -> str:
    flaky_call_count["search"] += 1
    if flaky_call_count["search"] % 2 == 1:
        raise ConnectionError("Flaky network — request dropped")
    time.sleep(0.8)
    return f"[FlakAgent] Results for '{query}': Found 3 articles."

def flaky_summarize(text: str) -> str:
    time.sleep(1.2)
    return f"[FlakAgent] Summary: {text[:40]}..."

def flaky_analyze(query: str) -> str:
    raise RuntimeError("Analysis service unavailable")

# ── Run Comparison ─────────────────────────────────────────────────

def run_comparison():
    comparator = AgentComparator(
        agent_a_name="ReliableAgent-v1",
        agent_b_name="FlakyAgent-v1",
        timeout_threshold=5.0,
        max_retries=2,
        retry_delay=0.3,
    )

    # Add same tasks for both agents
    comparator.add_task("web_search",   reliable_search,   flaky_search,   "AI agent trends 2026")
    comparator.add_task("web_search",   reliable_search,   flaky_search,   "enterprise automation tools")
    comparator.add_task("summarize",    reliable_summarize, flaky_summarize, "Agentic AI is transforming how companies build software")
    comparator.add_task("analyze",      reliable_analyze,  flaky_analyze,  "market opportunity sizing")
    comparator.add_task("web_search",   reliable_search,   flaky_search,   "LangChain vs LlamaIndex comparison")

    report = comparator.run_and_compare()

if __name__ == "__main__":
    run_comparison()
