"""
HallucinationScorer — Score AI agent outputs for hallucination risk
Returns a 0-100 confidence score. Lower = higher hallucination risk.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class HallucinationReport:
    """Full hallucination analysis report for a single output."""
    text: str
    score: int                    # 0-100, higher = more trustworthy
    risk_level: str               # LOW / MEDIUM / HIGH / CRITICAL
    flags: list                   # list of issues found
    breakdown: dict               # per-dimension scores

    def summary(self) -> str:
        flag_str = "\n    → ".join(self.flags) if self.flags else "None"
        return (
            f"\n  Hallucination Score : {self.score}/100 ({self.risk_level} RISK)"
            f"\n  Flags               : {flag_str}"
            f"\n  Breakdown           : {self.breakdown}"
        )


class HallucinationScorer:
    """
    Scores any text output for hallucination risk using 5 heuristic dimensions.
    No external API needed — runs fully locally.

    Dimensions:
    1. Vagueness        — hedging language like "maybe", "I think"
    2. Contradiction    — opposite claims in same output
    3. Specificity      — presence of concrete facts, numbers, dates
    4. Overconfidence   — strong claims with no supporting evidence
    5. Filler ratio     — long output with low information density
    """

    # ── Signal lists ──────────────────────────────────────────────

    VAGUE_SIGNALS = [
        "maybe", "perhaps", "possibly", "i think", "i believe", "i'm not sure",
        "it could be", "might be", "seems like", "appears to", "probably",
        "roughly", "approximately", "i'm guessing", "not certain", "unclear",
        "i assume", "generally speaking", "in some cases", "it depends",
    ]

    OVERCONFIDENCE_SIGNALS = [
        "definitely", "certainly", "absolutely", "always", "never", "guaranteed",
        "without a doubt", "100%", "it is a fact", "proven", "undeniably",
        "there is no question", "clearly", "obviously", "everyone knows",
    ]

    CONTRADICTION_PAIRS = [
        ("yes", "no"),
        ("true", "false"),
        ("i know", "i don't know"),
        ("found", "cannot find"),
        ("available", "not available"),
        ("confirmed", "unconfirmed"),
        ("always", "never"),
        ("is", "is not"),
        ("can", "cannot"),
        ("does", "does not"),
    ]

    SPECIFIC_PATTERNS = [
        r'\b\d{4}\b',               # years like 2026
        r'\b\d+(\.\d+)?%\b',        # percentages
        r'\$[\d,]+',                 # dollar amounts
        r'\b\d+ (million|billion|thousand)\b',
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        # proper nouns pattern removed — too many false positives
    ]

    FILLER_WORDS = [
        "basically", "essentially", "generally", "in general", "as you know",
        "needless to say", "it goes without saying", "of course", "obviously",
        "as we all know", "in other words", "so to speak",
    ]

    def score(self, text: str) -> HallucinationReport:
        """Score a piece of text. Returns a HallucinationReport."""
        text_lower = text.lower()
        words = text_lower.split()
        total_words = max(len(words), 1)
        flags = []
        breakdown = {}

        # ── Dimension 1: Vagueness (max penalty: 25 points) ──────
        vague_hits = [w for w in self.VAGUE_SIGNALS if w in text_lower]
        vague_count = len(vague_hits)
        vague_penalty = min(vague_count * 5, 25)
        breakdown["vagueness"] = max(25 - vague_penalty, 0)
        if vague_hits:
            flags.append(f"Vague language detected: {vague_hits[:3]}")

        # ── Dimension 2: Contradiction (max penalty: 30 points) ──
        contradiction_hits = []
        for word_a, word_b in self.CONTRADICTION_PAIRS:
            if word_a in text_lower and word_b in text_lower:
                contradiction_hits.append(f"'{word_a}' vs '{word_b}'")
        contradiction_penalty = min(len(contradiction_hits) * 10, 30)
        breakdown["contradiction"] = max(30 - contradiction_penalty, 0)
        if contradiction_hits:
            flags.append(f"Contradictory statements: {contradiction_hits[:2]}")

        # ── Dimension 3: Specificity (bonus up to 20 points) ─────
        specific_hits = 0
        for pattern in self.SPECIFIC_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specific_hits += len(matches)
        specificity_score = min(specific_hits * 3, 20)
        breakdown["specificity"] = specificity_score
        if specific_hits == 0:
            flags.append("No specific facts, numbers, or dates found — hard to verify")

        # ── Dimension 4: Overconfidence (max penalty: 15 points) ─
        overconf_hits = [w for w in self.OVERCONFIDENCE_SIGNALS if w in text_lower]
        overconf_count = len(overconf_hits)
        overconf_penalty = min(overconf_count * 5, 15)
        breakdown["overconfidence"] = max(15 - overconf_penalty, 0)
        if overconf_hits:
            flags.append(f"Overconfident language without evidence: {overconf_hits[:3]}")

        # ── Dimension 5: Filler ratio (max penalty: 10 points) ───
        filler_hits = [w for w in self.FILLER_WORDS if w in text_lower]
        filler_ratio = len(filler_hits) / total_words
        filler_penalty = min(int(filler_ratio * 200), 10)
        breakdown["filler_ratio"] = max(10 - filler_penalty, 0)
        if filler_hits:
            flags.append(f"High filler word density: {filler_hits[:3]}")

        # ── Final score ───────────────────────────────────────────
        raw_score = sum(breakdown.values())
        score = max(0, min(100, raw_score))

        # Risk level
        if score >= 75:
            risk_level = "LOW"
        elif score >= 50:
            risk_level = "MEDIUM"
        elif score >= 25:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return HallucinationReport(
            text=text[:200],
            score=score,
            risk_level=risk_level,
            flags=flags,
            breakdown=breakdown,
        )

    def score_and_print(self, text: str, label: str = "Output") -> HallucinationReport:
        """Score text and print a formatted report."""
        report = self.score(text)

        risk_emoji = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔴", "CRITICAL": "🚨"}
        emoji = risk_emoji.get(report.risk_level, "❓")

        print(f"\n{'─'*55}")
        print(f"🧠  HALLUCINATION SCORER — {label}")
        print(f"{'─'*55}")
        print(f"  Score      : {report.score}/100  {emoji} {report.risk_level} RISK")
        print(f"  Breakdown  : {report.breakdown}")
        if report.flags:
            print(f"  Flags:")
            for flag in report.flags:
                print(f"    → {flag}")
        print(f"{'─'*55}\n")

        return report
