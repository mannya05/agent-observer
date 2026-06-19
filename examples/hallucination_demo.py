"""
HallucinationScorer — Demo
Tests 4 different outputs ranging from trustworthy to critically hallucinated.

Run: python examples/hallucination_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.hallucination_scorer import HallucinationScorer

def run_demo():
    scorer = HallucinationScorer()

   
    print("   HALLUCINATION SCORER — LIVE DEMO")
   

    # Output 1 — Trustworthy (specific, factual)
    scorer.score_and_print(
        "According to Gartner's 2026 Hype Cycle report published in March 2026, "
        "40% of enterprise AI agent projects are expected to be cancelled by 2027. "
        "The report analyzed 1,200 companies across 15 industries.",
        label="Trustworthy Output"
    )

    # Output 2 — Medium risk (vague but not contradictory)
    scorer.score_and_print(
        "I think AI agents are probably going to be important in the future. "
        "It seems like many companies might be interested in this technology. "
        "Perhaps the market could possibly grow significantly, but I'm not certain.",
        label="Vague Output"
    )

    # Output 3 — High risk (overconfident + no facts)
    scorer.score_and_print(
        "AI agents will definitely replace all software engineers by 2027. "
        "This is absolutely certain and there is no question about it. "
        "Every company will obviously adopt this technology. It is guaranteed.",
        label="Overconfident Output"
    )

    # Output 4 — Critical (contradiction + vague + overconfident)
    scorer.score_and_print(
        "I definitely know the answer but I'm not sure at the same time. "
        "The system is available and not available depending on maybe some factors. "
        "It is certainly true and false that this works. I found the data but cannot find it.",
        label="Hallucinated Output"
    )

if __name__ == "__main__":
    run_demo()
