"""
app.py
------
Streamlit dashboard for the AI Red-Teaming Agent.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time
from datetime import datetime

from agent.attacker import run_attack_session, get_available_categories
from agent.evaluator import evaluate_session, compute_summary
from agent.session import save_session, load_session, list_sessions

# --- Page Config ---
st.set_page_config(
    page_title="AI Red-Teaming Agent",
    page_icon="🔴",
    layout="wide"
)

# --- Styles ---
st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; color: #ff4b4b; }
    .subtitle { color: #aaa; font-size: 0.95rem; margin-top: -10px; }
    .metric-card { background: #1e1e2e; border-radius: 10px; padding: 15px; text-align: center; }
    .verdict-COMPLIED { color: #ff4b4b; font-weight: bold; }
    .verdict-RESISTED { color: #00cc88; font-weight: bold; }
    .verdict-PARTIAL { color: #ffaa00; font-weight: bold; }
    .verdict-UNCLEAR { color: #aaaaaa; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<p class="main-title">🔴 AI Red-Teaming Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Abimel Codex · Project 3 · Autonomous adversarial testing of LLMs</p>', unsafe_allow_html=True)
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Attack Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Your key is never stored")

    st.subheader("Attack Categories")
    try:
        all_categories = get_available_categories()
    except Exception:
        all_categories = ["jailbreak", "role_play", "prompt_injection", "social_engineering", "indirect_injection"]

    selected_categories = []
    for cat in all_categories:
        label = cat.replace("_", " ").title()
        if st.checkbox(label, value=True, key=f"cat_{cat}"):
            selected_categories.append(cat)

    use_llm_judge = st.toggle("Use LLM Judge (more accurate)", value=True)
    delay = st.slider("Delay between attacks (s)", 0.5, 3.0, 1.0, 0.5)

    st.divider()
    run_button = st.button("🚀 Launch Attack Session", type="primary", use_container_width=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🎯 Live Session", "📊 Analytics", "📁 Past Sessions"])

# --- Session State Init ---
if "session_results" not in st.session_state:
    st.session_state.session_results = []
if "session_summary" not in st.session_state:
    st.session_state.session_summary = {}
if "session_running" not in st.session_state:
    st.session_state.session_running = False

# ==================== TAB 1: LIVE SESSION ====================
with tab1:
    if run_button:
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not selected_categories:
            st.error("Select at least one attack category.")
        else:
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state.session_running = True
            st.session_state.session_results = []
            st.session_state.session_summary = {}

            st.info(f"🔴 Launching attack session across {len(selected_categories)} categories...")

            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()

            raw_results = []

            def progress_callback(i, total, attack_name):
                progress_bar.progress((i + 1) / total)
                status_text.markdown(f"**Attacking:** `{attack_name}` ({i+1}/{total})")

            with st.spinner("Running attacks..."):
                raw_results = run_attack_session(
                    categories=selected_categories,
                    delay=delay,
                    progress_callback=progress_callback
                )

            status_text.markdown("🧠 **Evaluating responses...**")
            evaluated = evaluate_session(raw_results, use_llm_judge=use_llm_judge)
            summary = compute_summary(evaluated)

            st.session_state.session_results = evaluated
            st.session_state.session_summary = summary
            st.session_state.session_running = False

            progress_bar.progress(1.0)
            status_text.markdown("✅ **Session complete!**")

            filepath = save_session(evaluated, summary)
            st.success(f"Session saved to `{os.path.basename(filepath)}`")

    # --- Display Results ---
    if st.session_state.session_results:
        summary = st.session_state.session_summary
        results = st.session_state.session_results

        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Attacks", summary.get("total_attacks", 0))
        with col2:
            st.metric("🔴 Complied", summary.get("complied", 0))
        with col3:
            st.metric("🟢 Resisted", summary.get("resisted", 0))
        with col4:
            st.metric("⚠️ Partial", summary.get("partial", 0))

        col5, col6 = st.columns(2)
        with col5:
            st.metric("Compliance Rate", f"{summary.get('compliance_rate', 0)}%",
                      delta=None, help="% of attacks the model complied with (higher = more vulnerable)")
        with col6:
            st.metric("Resistance Rate", f"{summary.get('resistance_rate', 0)}%",
                      help="% of attacks the model successfully resisted")

        st.divider()

        # Results Table
        st.subheader("📋 Attack Results")
        df = pd.DataFrame([{
            "ID": r["id"],
            "Category": r["category"].replace("_", " ").title(),
            "Attack Name": r["name"],
            "Verdict": r.get("verdict", "UNCLEAR"),
            "Confidence": f"{r.get('confidence', 0):.0%}",
            "Method": r.get("method", "heuristic")
        } for r in results])

        def color_verdict(val):
            colors = {
                "COMPLIED": "color: #ff4b4b; font-weight: bold",
                "RESISTED": "color: #00cc88; font-weight: bold",
                "PARTIAL": "color: #ffaa00; font-weight: bold",
                "UNCLEAR": "color: #aaaaaa"
            }
            return colors.get(val, "")

        st.dataframe(
            df.style.map(color_verdict, subset=["Verdict"]),
            use_container_width=True,
            height=400
        )

        # Detailed Result Expanders
        st.subheader("🔍 Detailed Results")
        for r in results:
            verdict_icon = {"COMPLIED": "🔴", "RESISTED": "🟢", "PARTIAL": "🟡", "UNCLEAR": "⚪"}.get(r.get("verdict"), "⚪")
            with st.expander(f"{verdict_icon} [{r['id']}] {r['name']} — {r.get('verdict', 'UNCLEAR')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**🗡️ Attack Prompt**")
                    st.code(r["prompt"], language=None)
                with col_b:
                    st.markdown("**🤖 Model Response**")
                    st.code(r["response"], language=None)
                st.caption(f"Reason: {r.get('reason', 'N/A')} · Confidence: {r.get('confidence', 0):.0%} · Tokens: {r.get('tokens_used', 0)}")

    elif not st.session_state.session_running:
        st.info("Configure attack parameters in the sidebar and press **Launch Attack Session** to begin.")

# ==================== TAB 2: ANALYTICS ====================
with tab2:
    if not st.session_state.session_results:
        st.info("Run an attack session first to see analytics.")
    else:
        results = st.session_state.session_results
        summary = st.session_state.session_summary

        col1, col2 = st.columns(2)

        # Verdict Pie Chart
        with col1:
            st.subheader("Verdict Distribution")
            verdict_counts = pd.Series([r.get("verdict", "UNCLEAR") for r in results]).value_counts()
            color_map = {
                "COMPLIED": "#ff4b4b",
                "RESISTED": "#00cc88",
                "PARTIAL": "#ffaa00",
                "UNCLEAR": "#888888",
                "ERROR": "#444444"
            }
            fig_pie = px.pie(
                names=verdict_counts.index,
                values=verdict_counts.values,
                color=verdict_counts.index,
                color_discrete_map=color_map,
                hole=0.4
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)

        # Category Compliance Bar Chart
        with col2:
            st.subheader("Compliance by Category")
            cat_data = summary.get("by_category", {})
            if cat_data:
                cat_names = [c.replace("_", " ").title() for c in cat_data.keys()]
                compliance_rates = [
                    round((v["complied"] + v["partial"] * 0.5) / max(v["total"], 1) * 100, 1)
                    for v in cat_data.values()
                ]
                fig_bar = px.bar(
                    x=cat_names,
                    y=compliance_rates,
                    labels={"x": "Category", "y": "Compliance Rate (%)"},
                    color=compliance_rates,
                    color_continuous_scale=["#00cc88", "#ffaa00", "#ff4b4b"]
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # Confidence Distribution
        st.subheader("Evaluator Confidence Distribution")
        confidences = [r.get("confidence", 0) for r in results]
        fig_hist = px.histogram(
            x=confidences,
            nbins=10,
            labels={"x": "Confidence Score", "y": "Count"},
            color_discrete_sequence=["#7c6cff"]
        )
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

# ==================== TAB 3: PAST SESSIONS ====================
with tab3:
    sessions = list_sessions()

    if not sessions:
        st.info("No past sessions found. Run your first attack session to create a report.")
    else:
        st.subheader(f"📁 {len(sessions)} Saved Session(s)")

        for s in sessions:
            with st.expander(f"📄 {s['session_name']} — {s['timestamp'][:16]}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Attacks", s["total_attacks"])
                col2.metric("Compliance Rate", f"{s['compliance_rate']}%")
                col3.metric("File", s["filename"])

                if st.button("Load Session", key=f"load_{s['filename']}"):
                    data = load_session(s["filepath"])
                    st.session_state.session_results = data["results"]
                    st.session_state.session_summary = data["summary"]
                    st.success("Session loaded! Switch to Live Session or Analytics tab.")

                with open(s["filepath"], "r") as f:
                    st.download_button(
                        "⬇️ Download JSON",
                        f.read(),
                        file_name=s["filename"],
                        mime="application/json",
                        key=f"dl_{s['filename']}"
                    )
