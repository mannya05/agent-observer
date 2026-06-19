"""
AgentObserver — Live Demo
Shows AgentObserver catching 3 real failure types + retry mechanism:
1. Tool failure with AUTO RETRY (recovers on 2nd attempt)
2. Tool failure with MAX RETRIES EXCEEDED (fails all 3 attempts)
3. Loop detection
4. Timeout

Run: python examples/demo.py
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.observer import AgentObserver
from core.postmortem import print_postmortem

# ── Simulated agent tools ──────────────────────────────────────────

attempt_counter = {"count": 0}

def fake_web_search_flaky(query: str) -> str:
    """Simulates a flaky tool that fails first time but recovers on retry."""
    attempt_counter["count"] += 1
    if attempt_counter["count"] == 1:
        raise ConnectionError("Network timeout — connection dropped")
    attempt_counter["count"] = 0
    return f"Search results for: {query} — Found 5 relevant articles."

def fake_web_search_broken(query: str) -> str:
    """Simulates a tool that always fails — max retries exceeded."""
    raise ConnectionError("Search API is completely down")

def fake_web_search(query: str) -> str:
    """Normal working search."""
    if "error" in query.lower():
        raise ConnectionError("Search API rate limit exceeded")
    return f"Search results for: {query} — Found 5 relevant articles."

def fake_slow_tool(query: str) -> str:
    """Simulates a tool that takes way too long."""
    time.sleep(12)
    return "Finally done."

def fake_summarizer(text: str) -> str:
    """Simulates a summarization tool."""
    return f"Summary: {text[:80]}..."

# ── Demo ───────────────────────────────────────────────────────────

def run_demo():
    print(" AGENT OBSERVER — LIVE DEMO")

    API_KEY = os.getenv("GROQ_API_KEY", "your-api-key-here")

    observer = AgentObserver(
        agent_name="ResearchAgent-v1",
        timeout_threshold=5.0,
        loop_threshold=3,
        max_retries=3,
        retry_delay=0.5,  # short delay for demo purposes
    )

    print("▶ Starting agent session...\n")

    # Step 1 — Flaky tool: fails first, recovers on retry ✅
    print("Step 1: Flaky search (fails once, recovers on retry)...")
    observer.monitor_step("web_search", fake_web_search_flaky, "AI agent trends 2026")

    # Step 2 — Broken tool: fails all retries ❌
    print("\nStep 2: Broken search (fails all retries)...")
    observer.monitor_step("web_search", fake_web_search_broken, "enterprise AI market size")

    # Step 3, 4, 5 — Loop detection
    print("\nStep 3-5: Agent stuck in loop (same search repeated)...")
    for _ in range(3):
        observer.monitor_step("web_search", fake_web_search, "stuck query")

    # Step 6 — Timeout
    print("\nStep 6: Running slow tool (will timeout)...")
    observer.monitor_step("slow_analysis_tool", fake_slow_tool, "analyze everything")

    # Step 7 — Success
    print("\nStep 7: Summarizing results...")
    observer.monitor_step("summarizer", fake_summarizer,
        "AI agents in 2026 are transforming enterprise workflows.")

    # Save log
    summary = observer.save_log("logs/demo_session.json")

    # Print session summary
    print("\n" + "="*55)
    print("SESSION SUMMARY")
    print("="*55)
    print(f"  Total Steps   : {summary['total_steps']}")
    print(f"  Successful    : {summary['successful_steps']}")
    print(f"  Failed        : {summary['failed_steps']}")
    print(f"  Failure Rate  : {summary['failure_rate']}")
    print(f"  Total Retries : {summary['total_retries']}")
    print(f"  Failure Types : {summary['failure_breakdown']}")
    print("="*55)

    # Generate postmortem
    if API_KEY != "your-api-key-here":
        print("\nGenerating AI postmortem report...\n")
        print_postmortem(summary, API_KEY)
    else:
        print("\nSet GROQ_API_KEY env variable to see AI postmortem report.")
        print("    Mac/Linux: export GROQ_API_KEY=your-key-here")
        print("    Windows:   set GROQ_API_KEY=your-key-here\n")


if __name__ == "__main__":
    run_demo()
