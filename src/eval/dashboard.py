"""Streamlit dashboard for EasyMart evaluation metrics."""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def load_eval_results(filepath: Path = None):
    """Load evaluation results from JSON."""
    if filepath is None:
        filepath = Path(__file__).parent.parent.parent / "data" / "eval" / "full_eval_results.json"

    if filepath.exists():
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def load_baseline_scores(filepath: Path = None):
    """Load baseline RAG scores."""
    if filepath is None:
        filepath = Path(__file__).parent.parent.parent / "data" / "eval" / "baseline_scores.json"

    if filepath.exists():
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def load_advanced_scores(filepath: Path = None):
    """Load advanced RAG scores."""
    if filepath is None:
        filepath = Path(__file__).parent.parent.parent / "data" / "eval" / "advanced_scores.json"

    if filepath.exists():
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def main():
    st.set_page_config(page_title="EasyMart Evaluation Dashboard", layout="wide")

    st.title("EasyMart Support Agent - Evaluation Dashboard")

    # Load data
    eval_results = load_eval_results()
    baseline = load_baseline_scores()
    advanced = load_advanced_scores()

    if not eval_results:
        st.error("No evaluation results found. Run the evaluation suite first.")
        st.info("Run: python scripts/run_full_eval.py")
        return

    summary = eval_results.get("summary", {})
    results = eval_results.get("results", [])

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "📈 RAG Comparison",
        "🛡️ Guardrails",
        "📋 Details"
    ])

    # TAB 1: Overview
    with tab1:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Intent Accuracy",
                f"{summary.get('intent_accuracy', 0):.1%}",
                delta="How often intent was classified correctly"
            )

        with col2:
            st.metric(
                "Resolution Rate",
                f"{summary.get('resolution_rate', 0):.1%}",
                delta="Conversations resolved without escalation"
            )

        with col3:
            st.metric(
                "Avg Latency",
                f"{summary.get('avg_latency', 0):.2f}s",
                delta="End-to-end response time"
            )

        with col4:
            st.metric(
                "Policy Compliance",
                f"{summary.get('policy_compliance', 0):.2f}",
                delta="LLM-judge score (0-1)"
            )

        # LLM Judge Scores
        st.subheader("Response Quality Scores")
        judge_col1, judge_col2, judge_col3 = st.columns(3)

        with judge_col1:
            st.metric(
                "Helpfulness",
                f"{summary.get('helpfulness', 0):.2f}/1.0",
                delta="Response addresses customer needs"
            )

        with judge_col2:
            st.metric(
                "Groundedness",
                f"{summary.get('groundedness', 0):.2f}/1.0",
                delta="Response backed by context"
            )

        with judge_col3:
            st.metric(
                "Policy Compliance",
                f"{summary.get('policy_compliance', 0):.2f}/1.0",
                delta="Agent stays within authority"
            )

        # Category Breakdown
        st.subheader("Performance by Category")
        by_category = summary.get("by_category", {})

        if by_category:
            cat_data = []
            for cat, metrics in by_category.items():
                total = metrics.get("total", 0)
                resolved = metrics.get("resolved", 0)
                intent_match = metrics.get("intent_match", 0)

                cat_data.append({
                    "Category": cat.replace("_", " ").title(),
                    "Total": total,
                    "Resolved": resolved,
                    "Intent Accuracy": f"{intent_match/total:.1%}" if total > 0 else "0%",
                    "Resolution Rate": f"{resolved/total:.1%}" if total > 0 else "0%",
                })

            st.dataframe(
                pd.DataFrame(cat_data),
                use_container_width=True,
                hide_index=True
            )

    # TAB 2: RAG Comparison
    with tab2:
        st.subheader("Baseline vs Advanced RAG")

        if baseline and advanced:
            baseline_metrics = baseline.get("metrics", {})
            advanced_metrics = advanced.get("metrics", {})

            # Comparison data
            metrics_list = ["relevance", "faithfulness", "context_quality"]
            comparison_data = []

            for metric in metrics_list:
                baseline_val = baseline_metrics.get(metric, 0)
                advanced_val = advanced_metrics.get(metric, 0)
                improvement = advanced_val - baseline_val

                comparison_data.append({
                    "Metric": metric.replace("_", " ").title(),
                    "Baseline": f"{baseline_val:.3f}",
                    "Advanced": f"{advanced_val:.3f}",
                    "Improvement": f"{improvement:+.3f} ({improvement/baseline_val*100:+.1f}%)" if baseline_val > 0 else f"{improvement:+.3f}",
                })

            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

            # Comparison chart
            chart_data = []
            for metric in metrics_list:
                chart_data.append({
                    "Metric": metric.replace("_", " ").title(),
                    "Baseline": baseline_metrics.get(metric, 0),
                    "Advanced": advanced_metrics.get(metric, 0),
                })

            chart_df = pd.DataFrame(chart_data)
            fig = px.bar(
                chart_df,
                x="Metric",
                y=["Baseline", "Advanced"],
                barmode="group",
                title="RAG Pipeline Comparison",
                labels={"value": "Score", "variable": "Pipeline"}
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Baseline and/or advanced RAG scores not found")

    # TAB 3: Guardrails
    with tab3:
        st.subheader("Guardrail Triggers")

        # Check for guardrail logs
        log_file = Path(__file__).parent.parent.parent / "data" / "logs" / "guardrail_logs.json"

        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)

            # Count by type
            trigger_counts = {}
            for log in logs:
                trigger_type = log.get("type", "unknown")
                trigger_counts[trigger_type] = trigger_counts.get(trigger_type, 0) + 1

            if trigger_counts:
                # Display counts
                st.write("**Guardrail Triggers by Type:**")
                for trigger_type, count in sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {trigger_type}: {count}")

                # Chart
                chart_data = [
                    {"Type": t.replace("_", " ").title(), "Count": c}
                    for t, c in trigger_counts.items()
                ]
                fig = px.bar(
                    pd.DataFrame(chart_data),
                    x="Type",
                    y="Count",
                    title="Guardrail Triggers"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No guardrail triggers recorded")
        else:
            st.info("Guardrail logs not found")

    # TAB 4: Details
    with tab4:
        st.subheader("Individual Conversation Results")

        if results:
            # Create dataframe
            detail_data = []
            for i, result in enumerate(results):
                detail_data.append({
                    "#": i + 1,
                    "Category": result.get("category", "unknown").replace("_", " ").title(),
                    "Intent": result.get("actual_intent", "N/A"),
                    "Match": "✓" if result.get("intent_match") else "✗",
                    "Escalated": "Yes" if result.get("escalated") else "No",
                    "Latency": f"{result.get('latency', 0):.2f}s",
                    "Policy": f"{result.get('scores', {}).get('policy_compliance', 0):.2f}",
                    "Helpful": f"{result.get('scores', {}).get('helpfulness', 0):.2f}",
                    "Grounded": f"{result.get('scores', {}).get('groundedness', 0):.2f}",
                })

            detail_df = pd.DataFrame(detail_data)
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

            # Export option
            if st.button("Export Results as CSV"):
                csv = detail_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="evaluation_results.csv",
                    mime="text/csv"
                )


if __name__ == "__main__":
    main()
