#  AgentObserver

> **Real-time observability, auto-debugging, and evaluation toolkit for AI agents.**

[![PyPI version](https://badge.fury.io/py/agent-observer.svg)](https://pypi.org/project/agent-observer/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

> Inspired by the fact that **40% of enterprise AI agent projects get cancelled** — not because of model quality, but due to unobservable production failures.
> *(Gartner Hype Cycle for Agentic AI, 2026)*

---

## The Problem

AI agents fail silently in production. A loop here, a timeout there, a hallucination nobody caught — and suddenly your agent has rebooked 1,247 passengers onto wrong flights *(Air Canada, Jan 2026)*.

Companies deploying agents have no easy way to:
- Know **when** an agent is stuck or failing
- Understand **why** it failed
- Verify if the output is **grounded or hallucinated**
- Compare **which agent performs better**
- Evaluate if their **RAG pipeline is faithful**

**AgentObserver solves all of this.**

---

## Installation

```bash
pip install agent-observer
```

With LangChain support:
```bash
pip install agent-observer[langchain]
```

---

## Features

| Feature | Description |
|---|---|
|  **Failure Detection** | Detects loops, timeouts, tool errors, empty outputs in real-time |
|  **Auto Retry** | Exponential backoff retry on failed steps |
|  **Hallucination Scorer** | Scores any LLM output 0-100 for hallucination risk |
|  **RAG Monitor** | Evaluates retrieval quality, faithfulness, and answer relevance |
|  **Agent Comparison** | Side-by-side performance comparison of two agents |
|  **AI Postmortem** | Auto-generates human-readable failure reports via Groq API |
|  **Dashboard** | Visual Streamlit dashboard with session analytics |
|  **LangChain Plugin** | Drop-in callback for any LangChain agent |

---

## Quick Start

### 1. Basic Agent Monitoring

```python
from agent_observer import AgentObserver

observer = AgentObserver(
    agent_name="MyAgent",
    timeout_threshold=10.0,
    max_retries=3,
    retry_delay=1.0,
)

# Wrap any function call
result = observer.monitor_step("web_search", search_fn, "AI trends 2026")
result = observer.monitor_step("summarize", summarize_fn, result)

# Save session log
summary = observer.save_log("logs/session.json")
```

**Output when failure detected:**
```
=======================================================
  AGENT OBSERVER ALERT — MyAgent
=======================================================
  Step     : #2 — web_search
  Status   : LOOP_DETECTED
  Reason   : Agent repeated 'web_search' 3x with identical input
  Retries  : 0
  Duration : 234ms
=======================================================
```

---

### 2. Auto Retry with Exponential Backoff

```python
observer = AgentObserver(
    agent_name="MyAgent",
    max_retries=3,
    retry_delay=1.0,  # doubles each retry: 1s → 2s → 4s
)

# Automatically retries on failure
result = observer.monitor_step("api_call", flaky_api, "query")
# ⚠️ Step #1 failed — retrying in 1.0s... (attempt 1/3)
# ⚠️ Step #1 failed — retrying in 2.0s... (attempt 2/3)
# ✅ Step #1 recovered after 2 retries!
```

---

### 3. Hallucination Scorer

```python
from agent_observer import HallucinationScorer

scorer = HallucinationScorer()
report = scorer.score_and_print(llm_output, label="My Output")

# Score      : 92/100  ✅ LOW RISK
# Score      : 30/100  🔴 HIGH RISK
# Score      : 12/100  🚨 CRITICAL RISK
```

**Detects:**
- Vague language — "maybe", "possibly", "I think"
- Contradictions — "I know" + "I don't know" in same output
- Overconfidence — "definitely", "certainly" without evidence
- Missing specifics — no dates, numbers, or facts
- Filler density — verbose output with low information

---

### 4. RAG Monitor

```python
from agent_observer import RAGMonitor

monitor = RAGMonitor()
report = monitor.evaluate(
    question="What is agentic AI?",
    retrieved_docs=["doc1 text...", "doc2 text..."],
    generated_answer="Agentic AI refers to..."
)
report.summary()
```

**Evaluates 4 dimensions:**
- **Retrieval Quality** — are docs relevant to the question?
- **Faithfulness** — is the answer grounded in docs or hallucinated?
- **Answer Relevance** — does the answer address the question?
- **Hallucination Score** — overall output quality

```
============================================================
📚  RAG MONITOR REPORT
============================================================
  Retrieval Quality : 75/100
  Faithfulness      : 72/100
  Answer Relevance  : 100/100
  Hallucination     : 83/100
────────────────────────────────────────────────────────────
  Overall RAG Score : 82/100  ✅ LOW RISK
============================================================
```

---

### 5. Agent Comparison

```python
from agent_observer import AgentComparator

comparator = AgentComparator("GPT-Agent", "Claude-Agent")
comparator.add_task("web_search", gpt_search, claude_search, "AI trends")
comparator.add_task("summarize", gpt_summarize, claude_summarize, "text here")

report = comparator.run_and_compare()
```

**Output:**
```
============================================================
  COMPARISON REPORT
============================================================
  METRIC              GPT-Agent        Claude-Agent
  Failure Rate     👑  0.0%            20.0%
  Avg Duration     👑  320ms           720ms
  Total Retries    👑  0               5
  Weighted Score   👑  100/100         20/100
────────────────────────────────────────────────────────────
  🏆  OVERALL WINNER: GPT-AGENT
============================================================
```

---

### 6. LangChain Plugin

```python
from agent_observer import AgentObserverCallback
from langchain.agents import initialize_agent

# Just add one line to any existing LangChain agent
callback = AgentObserverCallback(
    agent_name="MyLangChainAgent",
    timeout_threshold=10.0,
    hallucination_threshold=50,
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    callbacks=[callback]  # ← that's it!
)

agent.run("Your task here")
```

Automatically monitors:
- Every tool call — failures, timeouts, loops
- Every LLM generation — hallucination scored in real-time
- Full session log saved on completion

---

### 7. AI Postmortem Report

```python
from agent_observer import print_postmortem

summary = observer.save_log("logs/session.json")
print_postmortem(summary, api_key=GROQ_API_KEY)
```

**Output:**
```
📋 POSTMORTEM REPORT
────────────────────────────────────────
1. Summary
   Agent got stuck in an infinite search loop on Step 4.

2. Root Cause
   Search query was not updated between retries — agent had
   no logic to modify query on repeated failure.

3. Impact
   3 redundant API calls, 700ms added latency, no useful output.

4. Fix Recommendation
   Add query variation logic — if same query fails twice,
   rephrase before retrying. Add max_retries=2 guard.
────────────────────────────────────────
```

---

### 8. Dashboard

```bash
python examples/demo.py        # generate a session first
streamlit run dashboard/app.py # launch dashboard
```

Visual analytics including:
- Step log with color-coded pass/fail
- Failure breakdown by type
- Step duration chart
- One-click AI postmortem generation

---

## Running the Examples

```bash
# Core failure detection + retry
python examples/demo.py

# Agent comparison
python examples/compare_demo.py

# Hallucination scoring
python examples/hallucination_demo.py

# LangChain plugin
python examples/langchain_demo.py

# RAG monitoring
python examples/rag_demo.py

# Dashboard
python -m streamlit run dashboard/app.py
```

---

## Failure Types Detected

| Type | Description |
|---|---|
| `tool_failure` | Tool raised an exception |
| `loop_detected` | Same action + same input repeated N times |
| `timeout` | Step exceeded configurable time threshold |
| `empty_output` | Agent returned None or blank output |
| `hallucination_risk` | Output contains contradictory statements |
| `max_retries_exceeded` | Failed after all retry attempts |

---

## Project Structure

```
agent-observer/
├── core/
│   ├── observer.py              # Failure detection + retry engine
│   ├── postmortem.py            # AI postmortem generator (Groq)
│   ├── comparator.py            # Agent comparison
│   ├── hallucination_scorer.py  # Hallucination scoring
│   ├── langchain_plugin.py      # LangChain callback plugin
│   └── rag_monitor.py           # RAG pipeline evaluation
├── dashboard/
│   └── app.py                   # Streamlit dashboard
├── examples/
│   ├── demo.py
│   ├── compare_demo.py
│   ├── hallucination_demo.py
│   ├── langchain_demo.py
│   └── rag_demo.py
├── logs/                        # Auto-generated session logs
└── README.md
```

---

## Environment Variables

```bash
# For AI postmortem reports (free)
export GROQ_API_KEY=your-groq-key-here

# Windows
set GROQ_API_KEY=your-groq-key-here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Research Background

This project addresses open research challenges in agentic AI reliability:

- *"Agentic Uncertainty Quantification"* — arXiv:2601.15703 (2026)
- *"Why AI Agents Fail in Production"* — Gartner Hype Cycle for Agentic AI (2026)
- *"40% of enterprise agentic AI projects expected to fail by 2027"* — Gartner (2026)

---

## Roadmap

- [x] Core failure detection engine
- [x] Auto retry with exponential backoff
- [x] AI-powered postmortem reports
- [x] Hallucination scorer
- [x] RAG pipeline monitor
- [x] Agent comparison
- [x] LangChain plugin
- [x] Streamlit dashboard
- [x] PyPI package

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

Built by [Mannya](https://github.com/mannya05)

⭐ Star this repo if you find it useful!
