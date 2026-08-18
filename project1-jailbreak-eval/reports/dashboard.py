import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Jailbreak Eval Suite", layout="wide")
st.title("LLM Jailbreak Eval Suite Dashboard")
st.caption("Adversarial safety benchmarking: GPT-4o-Mini vs Claude-3.5-Sonnet")

files = glob.glob("reports/*_graded.csv")
if not files:
    st.error("No graded reports found!")
else:
    latest = max(files, key=os.path.getctime)
    df = pd.read_csv(latest)
    total = len(df)
    op_fails = (df["openai_grade"] == "FAIL").sum()
    ant_fails = (df["anthropic_grade"] == "FAIL").sum()

    st.subheader("Overall Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Prompts", total)
    c2.metric("GPT-4o-Mini Failures", f"{op_fails}/{total}",
              delta=f"{op_fails/total*100:.0f}% attack success",
              delta_color="inverse")
    c3.metric("Claude Failures", f"{ant_fails}/{total}",
              delta=f"{ant_fails/total*100:.0f}% attack success",
              delta_color="inverse")
    c4.metric("Categories Tested", df["category"].nunique())

    st.subheader("Category-Wise Safety Failure Rates")
    rows = []
    for cat, gp in df.groupby("category"):
        rows.append({"Category": cat, "Model": "GPT-4o-Mini",
                     "Failure Rate (%)": round(
                         (gp["openai_grade"]=="FAIL").sum()/len(gp)*100, 1)})
        rows.append({"Category": cat, "Model": "Claude-3.5-Sonnet",
                     "Failure Rate (%)": round(
                         (gp["anthropic_grade"]=="FAIL").sum()/len(gp)*100, 1)})
    fig = px.bar(pd.DataFrame(rows), x="Category", y="Failure Rate (%)",
                 color="Model", barmode="group", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full Audit Trace")
    st.dataframe(df[["id","category","prompt",
                      "openai_response","openai_grade",
                      "anthropic_response","anthropic_grade"]])

    st.subheader("Model Comparison Summary")
    summary = pd.DataFrame({
        "Model": ["GPT-4o-Mini", "Claude-3.5-Sonnet"],
        "Attack Success Rate": [
            f"{op_fails/total*100:.1f}%",
            f"{ant_fails/total*100:.1f}%"],
        "Refusals (PASS)": [total - op_fails, total - ant_fails],
        "Failures (FAIL)": [op_fails, ant_fails]
    })
    st.table(summary)
