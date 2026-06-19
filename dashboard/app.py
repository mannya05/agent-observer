"""
AgentObserver — Dashboard
Run: streamlit run dashboard/app.py
"""

import streamlit as st
import json
import os
import glob
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentObserver",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Background */
.stApp { background-color: #0d0f14; color: #e2e8f0; }
[data-testid="stSidebar"] { background-color: #111318 !important; border-right: 1px solid #1e2330; }

/* Header */
.obs-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    color: #64ffda;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.2rem 0 1.2rem 0;
    border-bottom: 1px solid #1e2330;
    margin-bottom: 1.5rem;
}

/* Metric cards */
.metric-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1;
}
.metric-value.danger { color: #ff6b6b; }
.metric-value.success { color: #64ffda; }
.metric-value.warning { color: #ffd166; }

/* Step log */
.step-row {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    margin-bottom: 0.4rem;
    border-left: 3px solid transparent;
    background: #111318;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}
.step-row.success { border-left-color: #64ffda; }
.step-row.failure { border-left-color: #ff6b6b; background: #1a1118; }

.badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
    white-space: nowrap;
}
.badge.success { background: #0d2b22; color: #64ffda; }
.badge.failure { background: #2b0d0d; color: #ff6b6b; }
.badge.warning { background: #2b220d; color: #ffd166; }

/* Failure type bar */
.ftype-bar {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
}
.ftype-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #a0aec0;
    margin-bottom: 0.4rem;
}
.ftype-track {
    background: #1e2330;
    border-radius: 3px;
    height: 6px;
    width: 100%;
}
.ftype-fill {
    background: #ff6b6b;
    border-radius: 3px;
    height: 6px;
}

/* Postmortem box */
.postmortem-box {
    background: #111318;
    border: 1px solid #1e2330;
    border-left: 3px solid #64ffda;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #cbd5e0;
    white-space: pre-wrap;
}

/* Section titles */
.section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.5rem 0 0.8rem 0;
}

/* Hide streamlit defaults */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stMetric"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Load session logs ──────────────────────────────────────────────
def load_sessions():
    log_files = glob.glob("logs/*.json")
    sessions = []
    for f in log_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["_file"] = os.path.basename(f)
                sessions.append(data)
        except:
            pass
    sessions.sort(key=lambda x: x.get("steps", [{}])[0].get("timestamp", ""), reverse=True)
    return sessions


# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="obs-header">🔭 AgentObserver</div>', unsafe_allow_html=True)
    sessions = load_sessions()

    if not sessions:
        st.warning("No sessions found.\nRun `python examples/demo.py` first.")
        st.stop()

    session_names = [f"#{i+1} — {s.get('agent_name', 'Agent')} ({s.get('failure_rate', '?')} fail)" for i, s in enumerate(sessions)]
    selected_idx = st.selectbox("Session", range(len(sessions)), format_func=lambda i: session_names[i])
    session = sessions[selected_idx]

    st.markdown("---")
    st.markdown(f'<div class="metric-label">Session ID</div><div style="font-family:JetBrains Mono;font-size:0.8rem;color:#64ffda">{session.get("session_id","—")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-label" style="margin-top:0.8rem">Agent</div><div style="font-family:JetBrains Mono;font-size:0.8rem;color:#e2e8f0">{session.get("agent_name","—")}</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Refresh"):
        st.rerun()


# ── Main content ───────────────────────────────────────────────────
steps = session.get("steps", [])
failed_steps = [s for s in steps if s["status"] != "success"]
failure_breakdown = session.get("failure_breakdown", {})
total = session.get("total_steps", 0)
failed = session.get("failed_steps", 0)
rate = session.get("failure_rate", "0%")

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Steps</div>
        <div class="metric-value">{total}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Successful</div>
        <div class="metric-value success">{session.get('successful_steps', 0)}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    color_class = "danger" if failed > 0 else "success"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Failed</div>
        <div class="metric-value {color_class}">{failed}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    rate_num = float(rate.replace("%", ""))
    rate_class = "danger" if rate_num > 20 else "warning" if rate_num > 0 else "success"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Failure Rate</div>
        <div class="metric-value {rate_class}">{rate}</div>
    </div>""", unsafe_allow_html=True)


# Two columns — step log + failure breakdown
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<div class="section-title">Step Log</div>', unsafe_allow_html=True)
    for step in steps:
        is_fail = step["status"] != "success"
        status_class = "failure" if is_fail else "success"
        icon = "🚨" if is_fail else "✅"
        badge_label = step["status"].replace("_", " ").upper()
        reason = f'<div style="color:#718096;margin-top:0.3rem">{step["failure_reason"]}</div>' if is_fail and step.get("failure_reason") else ""
        st.markdown(f"""
        <div class="step-row {status_class}">
            <div style="min-width:1.2rem">{icon}</div>
            <div style="flex:1">
                <div style="display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap">
                    <span style="color:#e2e8f0;font-weight:600">#{step['step_number']} {step['action']}</span>
                    <span class="badge {status_class}">{badge_label}</span>
                    <span style="color:#4a5568">{step['duration_ms']}ms</span>
                </div>
                {reason}
            </div>
        </div>""", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-title">Failure Breakdown</div>', unsafe_allow_html=True)

    if failure_breakdown:
        max_val = max(failure_breakdown.values())
        for ftype, count in failure_breakdown.items():
            pct = int((count / max_val) * 100)
            st.markdown(f"""
            <div class="ftype-bar">
                <div class="ftype-label">{ftype.replace("_", " ").upper()} — {count}x</div>
                <div class="ftype-track"><div class="ftype-fill" style="width:{pct}%"></div></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4a5568;font-size:0.85rem;padding:1rem">No failures detected ✅</div>', unsafe_allow_html=True)

    # Step duration chart
    st.markdown('<div class="section-title">Step Duration (ms)</div>', unsafe_allow_html=True)
    if steps:
        import pandas as pd
        df = pd.DataFrame([{
            "Step": f"#{s['step_number']} {s['action']}",
            "Duration (ms)": s["duration_ms"],
            "Failed": s["status"] != "success"
        } for s in steps])
        st.bar_chart(df.set_index("Step")["Duration (ms)"], color="#64ffda")


# Postmortem section
st.markdown('<div class="section-title">AI Postmortem</div>', unsafe_allow_html=True)

if failed_steps:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        if st.button("⚡ Generate Postmortem"):
            with st.spinner("Analyzing failures..."):
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from core.postmortem import generate_postmortem
                report = generate_postmortem(session, groq_key)
                st.markdown(f'<div class="postmortem-box">{report}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4a5568;font-size:0.85rem;padding:0.8rem;border:1px solid #1e2330;border-radius:6px">Set GROQ_API_KEY to enable AI postmortem generation.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#64ffda;font-size:0.85rem;padding:0.8rem">✅ No failures to analyze.</div>', unsafe_allow_html=True)
