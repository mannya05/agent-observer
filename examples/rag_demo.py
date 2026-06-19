"""
AgentObserver — RAG Monitor Demo
Tests 3 RAG scenarios: good, medium, and hallucinated.

Run: python examples/rag_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag_monitor import RAGMonitor

def run_demo():
    monitor = RAGMonitor()


    print("   AGENTOBSERVER — RAG MONITOR DEMO")
    

    # ── Scenario 1: Good RAG — faithful and relevant ───────────────
    print("\n\n▶ Scenario 1: Good RAG Pipeline")
    report1 = monitor.evaluate(
        question="What is agentic AI and why are enterprise projects failing?",
        retrieved_docs=[
            "Agentic AI refers to AI systems that can autonomously plan and execute "
            "multi-step tasks without constant human intervention. These systems use "
            "tools, memory, and reasoning to complete complex goals.",

            "According to Gartner's 2026 report, 40% of enterprise agentic AI projects "
            "are expected to fail by 2027. The primary reasons include unobservable "
            "production failures, lack of monitoring, and poor error handling in "
            "multi-step agent pipelines.",
        ],
        generated_answer=(
            "Agentic AI refers to autonomous AI systems that can plan and execute "
            "multi-step tasks independently. Enterprise projects are failing at a 40% "
            "rate according to Gartner 2026, primarily due to unobservable production "
            "failures and lack of proper monitoring in agent pipelines."
        )
    )
    report1.summary()

    # ── Scenario 2: Medium RAG — partially grounded ────────────────
    print("▶ Scenario 2: Partially Grounded RAG")
    report2 = monitor.evaluate(
        question="How do AI agents handle tool failures in production?",
        retrieved_docs=[
            "Production AI agents frequently encounter tool failures such as API "
            "timeouts, rate limits, and connection errors. Robust agents implement "
            "retry mechanisms with exponential backoff to handle transient failures."
        ],
        generated_answer=(
            "AI agents handle tool failures using retry logic. They also use "
            "circuit breakers, fallback strategies, load balancing, distributed "
            "tracing, Kubernetes orchestration, and service mesh architectures "
            "to ensure high availability in production environments."
        )
    )
    report2.summary()

    # ── Scenario 3: Bad RAG — hallucinated answer ──────────────────
    print("▶ Scenario 3: Hallucinated RAG Output")
    report3 = monitor.evaluate(
        question="What is the market size of agentic AI in 2026?",
        retrieved_docs=[
            "Large language models have shown impressive performance on various "
            "benchmarks including MMLU and HumanEval. Recent models achieve "
            "over 90% accuracy on standardized tests."
        ],
        generated_answer=(
            "I think the agentic AI market is probably worth maybe around "
            "500 billion dollars, possibly more. It's definitely the biggest "
            "technology market ever, certainly growing at perhaps 200% annually. "
            "I'm not sure but it could be even larger than that."
        )
    )
    report3.summary()

    # ── Session stats ──────────────────────────────────────────────
    stats = monitor.get_session_stats()
   
    print(" SESSION STATS")
    print(f"  Total Evaluations     : {stats['total_evaluations']}")
    print(f"  Avg Overall Score     : {stats['avg_overall_score']}/100")
    print(f"  Avg Faithfulness      : {stats['avg_faithfulness']}/100")
    print(f"  Avg Retrieval Quality : {stats['avg_retrieval_quality']}/100")
    print(f"  High Risk Pipelines   : {stats['high_risk_count']}")
    print(f"  Low Faithfulness      : {stats['low_faithfulness_count']}")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
