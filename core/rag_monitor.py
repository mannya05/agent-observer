"""
AgentObserver — RAG Monitor
Monitors RAG pipelines for retrieval quality, faithfulness, and answer relevance.
No external API needed — runs fully locally.

Three dimensions scored:
1. Retrieval Quality  — are the retrieved docs relevant to the question?
2. Faithfulness       — does the answer come from the docs or is it hallucinated?
3. Answer Relevance   — does the answer actually address the question?
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from core.hallucination_scorer import HallucinationScorer


@dataclass
class RAGReport:
    """Full RAG pipeline evaluation report."""
    question: str
    retrieved_docs: List[str]
    generated_answer: str

    retrieval_score: int       # 0-100: how relevant are the docs?
    faithfulness_score: int    # 0-100: does answer come from docs?
    relevance_score: int       # 0-100: does answer address the question?
    hallucination_score: int   # 0-100: from HallucinationScorer
    overall_score: int         # weighted average

    risk_level: str            # LOW / MEDIUM / HIGH / CRITICAL
    flags: List[str]

    def summary(self):
        print(f"\n{'='*60}")
        print(f"RAG MONITOR REPORT")
        print(f"{'='*60}")
        print(f"  Question          : {self.question[:80]}...")
        print(f"  Docs Retrieved    : {len(self.retrieved_docs)}")
        print(f"{'─'*60}")
        print(f"  Retrieval Quality : {self.retrieval_score}/100")
        print(f"  Faithfulness      : {self.faithfulness_score}/100")
        print(f"  Answer Relevance  : {self.relevance_score}/100")
        print(f"  Hallucination     : {self.hallucination_score}/100")
        print(f"{'─'*60}")

        risk_emoji = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔴", "CRITICAL": "🚨"}
        emoji = risk_emoji.get(self.risk_level, "❓")
        print(f"  Overall RAG Score : {self.overall_score}/100  {emoji} {self.risk_level} RISK")

        if self.flags:
            print(f"\n  Flags:")
            for flag in self.flags:
                print(f"    → {flag}")
        print(f"{'='*60}\n")


class RAGMonitor:
    """
    Monitors a RAG pipeline across 4 dimensions:
    1. Retrieval Quality  — keyword overlap between question and docs
    2. Faithfulness       — how much of the answer is grounded in docs
    3. Answer Relevance   — does the answer address the question
    4. Hallucination      — uses HallucinationScorer on the answer

    Usage:
        monitor = RAGMonitor()
        report = monitor.evaluate(
            question="What is agentic AI?",
            retrieved_docs=["doc1 text", "doc2 text"],
            generated_answer="Agentic AI refers to..."
        )
        report.summary()
    """

    def __init__(self):
        self.scorer = HallucinationScorer()
        self.history: List[RAGReport] = []

    def evaluate(
        self,
        question: str,
        retrieved_docs: List[str],
        generated_answer: str,
    ) -> RAGReport:
        """Evaluate a single RAG pipeline run."""

        flags = []

        # ── Dimension 1: Retrieval Quality ────────────────────────
        retrieval_score = self._score_retrieval(question, retrieved_docs, flags)

        # ── Dimension 2: Faithfulness ──────────────────────────────
        faithfulness_score = self._score_faithfulness(generated_answer, retrieved_docs, flags)

        # ── Dimension 3: Answer Relevance ─────────────────────────
        relevance_score = self._score_relevance(question, generated_answer, flags)

        # ── Dimension 4: Hallucination ─────────────────────────────
        hall_report = self.scorer.score(generated_answer)
        hallucination_score = hall_report.score
        if hall_report.flags:
            flags.extend([f"[Hallucination] {f}" for f in hall_report.flags])

        # ── Overall Score (weighted) ───────────────────────────────
        # Faithfulness most important (40%), then hallucination (25%),
        # relevance (25%), retrieval (10%)
        overall = int(
            faithfulness_score * 0.40 +
            hallucination_score * 0.25 +
            relevance_score * 0.25 +
            retrieval_score * 0.10
        )

        # Risk level
        if overall >= 75:
            risk_level = "LOW"
        elif overall >= 50:
            risk_level = "MEDIUM"
        elif overall >= 25:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        report = RAGReport(
            question=question,
            retrieved_docs=retrieved_docs,
            generated_answer=generated_answer,
            retrieval_score=retrieval_score,
            faithfulness_score=faithfulness_score,
            relevance_score=relevance_score,
            hallucination_score=hallucination_score,
            overall_score=overall,
            risk_level=risk_level,
            flags=flags,
        )

        self.history.append(report)
        return report

    def _score_retrieval(self, question: str, docs: List[str], flags: List[str]) -> int:
        """Score how relevant retrieved docs are to the question."""

        if not docs:
            flags.append("No documents retrieved — retrieval failed completely")
            return 0

        # Extract keywords from question (words > 3 chars, ignore stopwords)
        stopwords = {"what", "when", "where", "which", "that", "this", "with",
                     "from", "have", "does", "will", "about", "into", "than",
                     "more", "some", "them", "they", "been", "were", "also"}
        question_words = set(
            w.lower() for w in re.findall(r'\b\w{4,}\b', question)
            if w.lower() not in stopwords
        )

        if not question_words:
            return 50  # can't evaluate

        # Check overlap between question keywords and docs
        combined_docs = " ".join(docs).lower()
        matched = sum(1 for w in question_words if w in combined_docs)
        overlap_ratio = matched / len(question_words)

        score = int(overlap_ratio * 100)

        if score < 30:
            flags.append(f"Low retrieval relevance — only {score}% keyword overlap with question")
        elif score < 60:
            flags.append(f"Medium retrieval relevance — {score}% keyword overlap")

        # Penalty for too few docs
        if len(docs) == 1:
            score = int(score * 0.85)
            flags.append("Only 1 document retrieved — consider increasing top_k")

        return min(score, 100)

    def _score_faithfulness(self, answer: str, docs: List[str], flags: List[str]) -> int:
        """
        Score how grounded the answer is in the retrieved documents.
        Checks if key phrases in the answer appear in the docs.
        """

        if not docs:
            flags.append("Cannot check faithfulness — no documents retrieved")
            return 0

        combined_docs = " ".join(docs).lower()
        answer_lower = answer.lower()

        # Extract meaningful phrases from answer (3+ char words)
        answer_words = set(
            w.lower() for w in re.findall(r'\b\w{4,}\b', answer_lower)
        )

        if not answer_words:
            return 50

        # Count how many answer words appear in docs
        grounded = sum(1 for w in answer_words if w in combined_docs)
        grounding_ratio = grounded / len(answer_words)

        score = int(grounding_ratio * 100)

        if score < 30:
            flags.append(f"Low faithfulness ({score}%) — answer may be hallucinated, not grounded in docs")
        elif score < 60:
            flags.append(f"Medium faithfulness ({score}%) — some answer content not found in retrieved docs")

        # Extra penalty if answer is much longer than docs suggest
        answer_len = len(answer.split())
        docs_len = len(combined_docs.split())
        if answer_len > docs_len * 0.5:
            score = int(score * 0.9)
            flags.append("Answer is verbose relative to retrieved context — risk of confabulation")

        return min(score, 100)

    def _score_relevance(self, question: str, answer: str, flags: List[str]) -> int:
        """Score how well the answer addresses the question."""

        # Extract question keywords
        stopwords = {"what", "when", "where", "which", "that", "this", "with",
                     "from", "have", "does", "will", "about", "into", "than"}
        q_words = set(
            w.lower() for w in re.findall(r'\b\w{4,}\b', question)
            if w.lower() not in stopwords
        )

        if not q_words:
            return 50

        answer_lower = answer.lower()
        matched = sum(1 for w in q_words if w in answer_lower)
        overlap = matched / len(q_words)
        score = int(overlap * 100)

        # Check if answer is too short to be meaningful
        answer_words = len(answer.split())
        if answer_words < 10:
            score = int(score * 0.7)
            flags.append(f"Answer too short ({answer_words} words) — may be incomplete")

        # Check for non-answers
        non_answers = ["i don't know", "i cannot", "no information", "not sure", "unclear"]
        if any(p in answer_lower for p in non_answers):
            score = int(score * 0.5)
            flags.append("Answer contains non-answer phrases — retrieval may have failed")

        if score < 40:
            flags.append(f"Low answer relevance ({score}%) — answer may not address the question")

        return min(score, 100)

    def get_session_stats(self) -> dict:
        """Get aggregate stats across all evaluated RAG runs."""
        if not self.history:
            return {"message": "No evaluations yet"}

        avg_overall = sum(r.overall_score for r in self.history) / len(self.history)
        avg_faithfulness = sum(r.faithfulness_score for r in self.history) / len(self.history)
        avg_retrieval = sum(r.retrieval_score for r in self.history) / len(self.history)
        low_faith = [r for r in self.history if r.faithfulness_score < 50]

        return {
            "total_evaluations": len(self.history),
            "avg_overall_score": round(avg_overall, 1),
            "avg_faithfulness": round(avg_faithfulness, 1),
            "avg_retrieval_quality": round(avg_retrieval, 1),
            "high_risk_count": len([r for r in self.history if r.risk_level in ["HIGH", "CRITICAL"]]),
            "low_faithfulness_count": len(low_faith),
        }
