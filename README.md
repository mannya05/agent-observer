# AgentObserver

**Real-time observability and auto-debugging for AI agents.**

> Inspired by the fact that 40% of enterprise AI agent projects get cancelled — not because of model quality, but due to unobservable production failures. *(Gartner, 2026)*

---

## The Problem

AI agents fail silently in production. A loop here, a timeout there, a hallucination nobody caught — and suddenly your agent has rebooked 1,247 passengers onto wrong flights *(Air Canada, Jan 2026)*.

Companies deploying agents have no easy way to:
- Know *when* an agent is stuck or failing
- Understand *why* it failed
- Get a human-readable explanation without digging through raw logs

**AgentObserver solves this.**

---

## What It Does

Wrap any agent tool call with `observer.monitor_step()` and get:

-  **Real-time failure alerts** — loops, timeouts, tool errors, empty outputs, hallucination risks
-  **Auto-generated postmortem reports** — powered by Claude API, explains root cause + fix
-  **Session logs** — full JSON trace of every step with status and failure reason
-  **Dashboard** — visual analytics of agent behavior over time

---

## Failure Types Detected

| Failure | Description |
|---|---|
| `loop_detected` | Agent repeating same action with same input N times |
| `tool_failure` | Tool raised an exception |
| `timeout` | Step exceeded configurable time threshold |
| `empty_output` | Agent returned None or blank output |
| `hallucination_risk` | Output contains contradictory statements |

---

## Quick Start

```bash
git clone https://github.com/yourusername/agent-observer
cd agent-observer
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
python examples/demo.py
```

---

## Usage

```python
from core.observer import AgentObserver
from core.postmortem import print_postmortem

# 1. Create observer
observer = AgentObserver(
    agent_name="MyAgent",
    timeout_threshold=10.0,
    loop_threshold=3
)

# 2. Wrap any agent tool call
result = observer.monitor_step("web_search", search_function, query="AI trends")
result = observer.monitor_step("summarize", summarize_function, text=result)

# 3. Get session summary + postmortem
summary = observer.save_log("logs/session.json")
print_postmortem(summary, api_key=ANTHROPIC_API_KEY)
```

**Output when failure detected:**
```
=======================================================
  AGENT OBSERVER ALERT — MyAgent
=======================================================
  Step     : #4 — web_search
  Status   : LOOP_DETECTED
  Reason   : Agent repeated 'web_search' 3x with identical input — likely stuck in a loop
  Duration : 234ms
  Time     : 2026-06-17T14:32:11
=======================================================
```

---

## Postmortem Report (AI-generated)

After each session, AgentObserver uses Claude API to generate:

```
 POSTMORTEM REPORT
────────────────────────────────────────
1. Summary
   Agent got stuck in an infinite search loop on Step 4, 
   causing 3 redundant API calls with no new information.

2. Root Cause
   The search query was not updated between retries — agent 
   had no logic to modify query on repeated failure.

3. Impact
   Wasted 3 API calls, added 700ms latency, no useful output produced.

4. Fix Recommendation
   Add query variation logic — if same query fails twice, 
   rephrase before retrying. Add max_retries=2 guard.
────────────────────────────────────────
```

---

## Project Structure

```
agent-observer/
├── core/
│   ├── observer.py       # Core monitoring engine
│   └── postmortem.py     # AI postmortem generator
├── dashboard/            # Streamlit dashboard (Week 2)
├── examples/
│   └── demo.py           # Live demo with 3 failure scenarios
├── logs/                 # Auto-saved session logs
└── README.md
```

---

## Roadmap

- [x] Core failure detection engine
- [x] AI-powered postmortem reports
- [x] Session logging (JSON)
- [ ] Streamlit dashboard with visual analytics
- [ ] Plug-and-play support for LangChain agents
- [ ] Slack/email alerts integration

---

## Tech Stack

- **Python** — core engine
- **Claude API** — postmortem generation
- **Streamlit** — dashboard (coming Week 2)

---

## Research Background

This project is inspired by open research challenges in agentic AI reliability:
- *"Agentic Uncertainty Quantification"* — arXiv:2601.15703 (Jan 2026)
- *"Why AI Agents Fail in Production"* — Gartner Hype Cycle for Agentic AI (2026)
- *"5 Production Scaling Challenges for Agentic AI"* — MachineLearningMastery (2026)

---

## Author

Built by Mannya — open to contributions, issues, and PRs!
=======
# agent-observer
Real-time observability and auto-debugging toolkit for AI agents
