import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Prompt Injection Detector", layout="wide")
st.title("🚨 Prompt Injection Detector Dashboard")
st.caption("Real-time classifier that detects prompt injection attacks before they reach the LLM")

files = glob.glob("project2-injection-detector/reports/detection_run_*.csv")
if not files:
    st.error("No detection reports found! Run detector/classifier.py first.")
else:
    latest = max(files, key=os.path.getctime)
    df = pd.read_csv(latest)
    total = len(df)
    danger = (df["verdict"] == "DANGER").sum()
    suspicious = (df["verdict"] == "SUSPICIOUS").sum()
    safe = (df["verdict"] == "SAFE").sum()
    correct = ((df["verdict"] == df["expected"]) | 
               ((df["verdict"] == "SUSPICIOUS") & (df["expected"] == "DANGER"))).sum()
    accuracy = round(correct / total * 100, 1)

    st.subheader("📊 Overall Detection Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Inputs", total)
    c2.metric("DANGER Detected", danger, delta=f"{danger/total*100:.0f}%", delta_color="inverse")
    c3.metric("SUSPICIOUS", suspicious, delta=f"{suspicious/total*100:.0f}%", delta_color="inverse")
    c4.metric("SAFE", safe, delta=f"{safe/total*100:.0f}%")
    c5.metric("Detection Accuracy", f"{accuracy}%")

    st.subheader("📈 Verdict Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(
            values=[danger, suspicious, safe],
            names=["DANGER", "SUSPICIOUS", "SAFE"],
            color_discrete_map={"DANGER": "#ff4444", "SUSPICIOUS": "#ffaa00", "SAFE": "#44ff44"},
            title="Overall Verdict Split"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        cat_df = df.groupby(["category","verdict"]).size().reset_index(name="count")
        fig_bar = px.bar(cat_df, x="category", y="count", color="verdict",
                         color_discrete_map={"DANGER":"#ff4444","SUSPICIOUS":"#ffaa00","SAFE":"#44ff44"},
                         title="Detections by Attack Category", barmode="stack")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("🌡️ Risk Score Distribution")
    fig_hist = px.histogram(df, x="risk_score", color="verdict",
                            color_discrete_map={"DANGER":"#ff4444","SUSPICIOUS":"#ffaa00","SAFE":"#44ff44"},
                            nbins=10, title="Risk Score Distribution Across All Inputs")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("🔍 Full Detection Audit Log")
    def color_verdict(val):
        if val == "DANGER": return "background-color: #ff4444; color: white"
        elif val == "SUSPICIOUS": return "background-color: #ffaa00; color: black"
        else: return "background-color: #44ff44; color: black"
    styled = df[["id","category","input_text","expected","verdict","risk_score","patterns_matched"]].style.map(color_verdict, subset=["verdict"])
    st.dataframe(styled)

    st.subheader("🏆 Detection Summary by Category")
    summary = df.groupby("category").agg(
        Total=("id","count"),
        Danger=("verdict", lambda x: (x=="DANGER").sum()),
        Suspicious=("verdict", lambda x: (x=="SUSPICIOUS").sum()),
        Safe=("verdict", lambda x: (x=="SAFE").sum()),
        Avg_Risk_Score=("risk_score","mean")
    ).reset_index()
    summary["Avg_Risk_Score"] = summary["Avg_Risk_Score"].round(1)
    st.table(summary)
