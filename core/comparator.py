"""
AgentComparator — Compare two agents on the same task
Run the same set of steps on Agent A and Agent B, then get a side-by-side report.
"""

import json
import time
from typing import Callable, List, Tuple
from core.observer import AgentObserver


class AgentTask:
    """Represents a single task step to run on both agents."""
    def __init__(self, action: str, func: Callable, *args, **kwargs):
        self.action = action
        self.func = func
        self.args = args
        self.kwargs = kwargs


class AgentComparator:
    """
    Runs the same tasks on two different agents and compares their performance.
    
    Usage:
        comparator = AgentComparator("GPT-Agent", "Claude-Agent")
        comparator.add_task("web_search", search_fn_a, search_fn_b, "AI trends")
        report = comparator.run_and_compare()
    """

    def __init__(
        self,
        agent_a_name: str = "Agent-A",
        agent_b_name: str = "Agent-B",
        timeout_threshold: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        self.agent_a_name = agent_a_name
        self.agent_b_name = agent_b_name
        self.timeout_threshold = timeout_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # List of (action, func_a, func_b, args, kwargs)
        self.tasks: List[Tuple] = []

    def add_task(self, action: str, func_a: Callable, func_b: Callable, *args, **kwargs):
        """Add a task to run on both agents."""
        self.tasks.append((action, func_a, func_b, args, kwargs))

    def run_and_compare(self) -> dict:
        """Run all tasks on both agents and return comparison report."""

        print(f"\n{'='*60}")
        print(f"AGENT COMPARISON: {self.agent_a_name} vs {self.agent_b_name}")
        print(f"{'='*60}\n")

        # Run Agent A
        print(f"▶ Running {self.agent_a_name}...\n")
        observer_a = AgentObserver(
            agent_name=self.agent_a_name,
            timeout_threshold=self.timeout_threshold,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )
        for action, func_a, func_b, args, kwargs in self.tasks:
            observer_a.monitor_step(action, func_a, *args, **kwargs)

        # Run Agent B
        print(f"\n▶ Running {self.agent_b_name}...\n")
        observer_b = AgentObserver(
            agent_name=self.agent_b_name,
            timeout_threshold=self.timeout_threshold,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )
        for action, func_a, func_b, args, kwargs in self.tasks:
            observer_b.monitor_step(action, func_b, *args, **kwargs)

        # Get summaries
        summary_a = observer_a.get_session_summary()
        summary_b = observer_b.get_session_summary()

        # Build comparison report
        report = self._build_report(summary_a, summary_b)

        # Print report
        self._print_report(report)

        # Save report
        self._save_report(report)

        return report

    def _build_report(self, a: dict, b: dict) -> dict:
        """Build a structured comparison report."""

        def parse_rate(rate_str):
            return float(rate_str.replace("%", ""))

        rate_a = parse_rate(a["failure_rate"])
        rate_b = parse_rate(b["failure_rate"])

        # Average step duration
        steps_a = a["steps"]
        steps_b = b["steps"]
        avg_duration_a = sum(s["duration_ms"] for s in steps_a) / len(steps_a) if steps_a else 0
        avg_duration_b = sum(s["duration_ms"] for s in steps_b) / len(steps_b) if steps_b else 0

        # Determine winner per metric
        winner_failure = a["agent_name"] if rate_a < rate_b else (b["agent_name"] if rate_b < rate_a else "tie")
        winner_speed = a["agent_name"] if avg_duration_a < avg_duration_b else (b["agent_name"] if avg_duration_b < avg_duration_a else "tie")
        winner_retries = a["agent_name"] if a["total_retries"] < b["total_retries"] else (b["agent_name"] if b["total_retries"] < a["total_retries"] else "tie")

        # Overall winner — weighted: failure rate (50%) + speed (30%) + retries (20%)
        score_a = 0
        score_b = 0
        if winner_failure == a["agent_name"]: score_a += 50
        elif winner_failure == b["agent_name"]: score_b += 50
        if winner_speed == a["agent_name"]: score_a += 30
        elif winner_speed == b["agent_name"]: score_b += 30
        if winner_retries == a["agent_name"]: score_a += 20
        elif winner_retries == b["agent_name"]: score_b += 20

        overall_winner = a["agent_name"] if score_a > score_b else (b["agent_name"] if score_b > score_a else "tie")

        return {
            "agent_a": {
                "name": a["agent_name"],
                "session_id": a["session_id"],
                "total_steps": a["total_steps"],
                "successful_steps": a["successful_steps"],
                "failed_steps": a["failed_steps"],
                "failure_rate": a["failure_rate"],
                "total_retries": a["total_retries"],
                "avg_duration_ms": round(avg_duration_a, 2),
                "score": score_a,
            },
            "agent_b": {
                "name": b["agent_name"],
                "session_id": b["session_id"],
                "total_steps": b["total_steps"],
                "successful_steps": b["successful_steps"],
                "failed_steps": b["failed_steps"],
                "failure_rate": b["failure_rate"],
                "total_retries": b["total_retries"],
                "avg_duration_ms": round(avg_duration_b, 2),
                "score": score_b,
            },
            "winners": {
                "failure_rate": winner_failure,
                "speed": winner_speed,
                "retries": winner_retries,
                "overall": overall_winner,
            }
        }

    def _print_report(self, report: dict):
        """Print a clean side-by-side comparison."""
        a = report["agent_a"]
        b = report["agent_b"]
        w = report["winners"]

        print(f"\n{'='*60}")
        print(f"COMPARISON REPORT")
        print(f"{'='*60}")
        print(f"  {'METRIC':<22} {'':>2} {a['name']:<18} {b['name']:<18}")
        print(f"  {'-'*56}")

        def row(label, val_a, val_b, winner_name):
            win_a = "👑" if winner_name == a["name"] else "  "
            win_b = "👑" if winner_name == b["name"] else "  "
            print(f"  {label:<22} {win_a} {str(val_a):<18} {win_b} {str(val_b):<18}")

        row("Failure Rate",    a["failure_rate"],    b["failure_rate"],    w["failure_rate"])
        row("Successful Steps",a["successful_steps"],b["successful_steps"],w["failure_rate"])
        row("Failed Steps",    a["failed_steps"],    b["failed_steps"],    w["failure_rate"])
        row("Total Retries",   a["total_retries"],   b["total_retries"],   w["retries"])
        row("Avg Duration(ms)",a["avg_duration_ms"], b["avg_duration_ms"], w["speed"])
        row("Weighted Score",  f"{a['score']}/100",  f"{b['score']}/100",  w["overall"])

        print(f"  {'-'*56}")
        print(f"\n OVERALL WINNER: {w['overall'].upper()}")
        print(f"{'='*60}\n")

    def _save_report(self, report: dict):
        """Save comparison report to JSON."""
        import os
        os.makedirs("logs", exist_ok=True)
        path = f"logs/comparison_{report['agent_a']['session_id']}_vs_{report['agent_b']['session_id']}.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Comparison report saved to {path}")
