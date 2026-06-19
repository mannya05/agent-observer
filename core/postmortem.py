"""
Postmortem Generator
Takes a failed session log and generates a human-readable explanation using Groq API (free).
"""

import json
import requests


def generate_postmortem(session_summary: dict, api_key: str) -> str:
    """
    Sends the session log to Groq API and gets a human-readable postmortem report.
    Groq is free — no credits needed!
    """

    failed_steps = [s for s in session_summary["steps"] if s["status"] != "success"]

    if not failed_steps:
        return " No failures detected in this session. Agent ran successfully."

    prompt = f"""You are an expert AI agent debugger. Analyze this agent session and write a clear postmortem report.

Agent: {session_summary['agent_name']}
Total Steps: {session_summary['total_steps']}
Failed Steps: {session_summary['failed_steps']}
Failure Rate: {session_summary['failure_rate']}

Failed Steps Details:
{json.dumps(failed_steps, indent=2)}

Write a postmortem report with these sections:
1. **Summary** — What went wrong in one sentence
2. **Root Cause** — Why did it fail (be specific)
3. **Impact** — What was the consequence of this failure
4. **Fix Recommendation** — Exactly what should be changed to prevent this

Keep it concise, technical, and actionable. No fluff."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f" Could not generate postmortem. API error: {response.status_code}\nDetails: {response.text}"


def print_postmortem(session_summary: dict, api_key: str):
    """Print a formatted postmortem report."""
    print("\n" + "="*60)
    print("AGENT OBSERVER — POSTMORTEM REPORT")
    print("="*60)
    print(f"Session ID  : {session_summary['session_id']}")
    print(f"Agent       : {session_summary['agent_name']}")
    print(f"Steps       : {session_summary['total_steps']} total, {session_summary['failed_steps']} failed")
    print(f"Failure Rate: {session_summary['failure_rate']}")
    print("-"*60)
    print(generate_postmortem(session_summary, api_key))
    print("="*60 + "\n")