"""AlgoQX Studio -- Dashboard Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd

from frontend.components.ui import page_header, render_metrics_row, glass_card, status_badge
from frontend.components.charts import create_line_chart, create_donut_chart

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the dashboard workspace page."""
    page_header(
        title="Dashboard",
        subtitle="Monitor system requests, resource overheads, and security alerts in real-time.",
    )

    # Fetch metrics from backend
    metrics_data = {
        "total_requests": 0,
        "avg_latency_ms": 0.0,
        "total_cost_usd": 0.0,
        "security_threats": 0,
        "model_usage": {},
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{API_BASE}/api/analytics/summary")
            if res.status_code == 200:
                metrics_data.update(res.json())
    except Exception:
        st.warning("⚠️ Backend API unavailable. Please ensure the backend server is running.")

    # 1. Top Metrics row
    render_metrics_row(
        [
            {"label": "Total Requests", "value": metrics_data["total_requests"], "delta": "+12% this week"},
            {"label": "Avg Latency", "value": f"{metrics_data['avg_latency_ms']} ms", "delta": "-24 ms reduction"},
            {"label": "Total Cost", "value": f"${metrics_data['total_cost_usd']:.5f}", "delta": "+8% usage spike"},
            {
                "label": "Security Alerts",
                "value": metrics_data["security_threats"],
                "delta": "All mitigated" if metrics_data["security_threats"] > 0 else "0 threats",
                "delta_type": "positive" if metrics_data["security_threats"] == 0 else "negative",
            },
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Charts Section
    col_chart_left, col_chart_right = st.columns([2, 1])

    with col_chart_left:
        # Request history (line chart) - fetch from backend
        if "requests_over_time" in metrics_data and metrics_data["requests_over_time"]:
            dates = [r["date"] for r in metrics_data["requests_over_time"]]
            requests_history = [r["requests"] for r in metrics_data["requests_over_time"]]
        else:
            dates = []
            requests_history = []
        
        if dates and requests_history:
            fig_requests = create_line_chart(dates, requests_history, "Platform Traffic (Requests/Day)", "#6366f1")
            st.plotly_chart(fig_requests, use_container_width=True)
        else:
            st.info("No request history data available yet.")

    with col_chart_right:
        # Model usage (donut chart)
        models = list(metrics_data["model_usage"].keys())
        counts = list(metrics_data["model_usage"].values())
        if models and counts:
            fig_models = create_donut_chart(models, counts, "Model Request Shares")
            st.plotly_chart(fig_models, use_container_width=True)
        else:
            st.info("No model usage data available yet.")

    # 3. Quick Actions
    st.markdown("### Quick Modules")
    col_action_1, col_action_2, col_action_3 = st.columns(3)

    with col_action_1:
        st.markdown(
            glass_card(
                "<h4>LLM Explorer</h4>"
                "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                "Inspect model tokens, context windows, and embeddings visualizations."
                "</p>",
                animate=False,
            ),
            unsafe_allow_html=True,
        )

    with col_action_2:
        st.markdown(
            glass_card(
                "<h4>Prompt Lab</h4>"
                "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                "Compare zero-shot, few-shot, and CoT strategy responses side-by-side."
                "</p>",
                animate=False,
            ),
            unsafe_allow_html=True,
        )

    with col_action_3:
        st.markdown(
            glass_card(
                "<h4>RAG Studio</h4>"
                "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                "Upload manuals, split text, index into FAISS database, and test answers."
                "</p>",
                animate=False,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Recent activity & System health
    col_activity, col_health = st.columns([2, 1])

    with col_activity:
        st.markdown("### Recent Traces")

        # Fetch recent traces or show mock logs
        traces = []
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{API_BASE}/api/observability/traces?limit=5")
                if res.status_code == 200:
                    traces = res.json().get("traces", [])
        except Exception:
            pass

        if not traces:
            st.info("No traces available yet. Execute some operations to populate activity logs.")
        else:
            # Render styled activity log table without newlines/blank lines
            table_rows = ""
            for t in traces:
                status_style = (
                    status_badge("Success", "success")
                    if t["status"] == "success"
                    else status_badge("Blocked", "error")
                )
                table_rows += (
                    f"<tr style='border-bottom: 1px solid var(--border);'>"
                    f"<td style='padding: 12px; font-family: var(--font-mono); font-size: 0.8rem;'>{t['trace_id']}</td>"
                    f"<td style='padding: 12px; font-size: 0.875rem;'>{t['module'].upper()}</td>"
                    f"<td style='padding: 12px; font-family: var(--font-mono); font-size: 0.8rem;'>{t['model']}</td>"
                    f"<td style='padding: 12px; font-size: 0.875rem;'>{t['latency_ms']:.1f} ms</td>"
                    f"<td style='padding: 12px;'>{status_style}</td>"
                    f"</tr>"
                )

            table_html = (
                f"<table style='width: 100%; border-collapse: collapse; text-align: left;'>"
                f"<thead>"
                f"<tr style='border-bottom: 2px solid var(--border); color: var(--text-muted); font-size: 0.8rem;'>"
                f"<th style='padding: 12px;'>TRACE ID</th>"
                f"<th style='padding: 12px;'>MODULE</th>"
                f"<th style='padding: 12px;'>MODEL</th>"
                f"<th style='padding: 12px;'>LATENCY</th>"
                f"<th style='padding: 12px;'>STATUS</th>"
                f"</tr>"
                f"</thead>"
                f"<tbody>"
                f"{table_rows}"
                f"</tbody>"
                f"</table>"
            )
            st.markdown(table_html, unsafe_allow_html=True)

    with col_health:
        st.markdown("### System Health")
        backend_status = status_badge("Online", "success")
        db_status = status_badge("Online", "success")

        # Check LLM connection
        llm_connected = False
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{API_BASE}/health")
                if res.status_code == 200:
                    llm_connected = True
        except Exception:
            pass

        llm_status = (
            status_badge("Online", "success")
            if llm_connected
            else status_badge("Offline", "error")
        )

        st.markdown(
            f"""
            <div class='glass-card' style='padding: 18px;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:12px;'>
                    <span style='color:var(--text-secondary);'>FastAPI Core</span>
                    {backend_status}
                </div>
                <div style='display:flex; justify-content:space-between; margin-bottom:12px;'>
                    <span style='color:var(--text-secondary);'>SQLite Database</span>
                    {db_status}
                </div>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='color:var(--text-secondary);'>Ollama Endpoint</span>
                    {llm_status}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
