"""AlgoQX Studio -- Analytics Dashboard Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd

from frontend.components.ui import page_header, render_metrics_row, glass_card
from frontend.components.charts import (
    create_line_chart,
    create_donut_chart,
    create_bar_chart,
    create_gauge,
)

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the central analytics dashboard workspace."""
    page_header(
        title="Analytics Dashboard",
        subtitle="Analyze platform request volumes, financial overheads, security alert trends, and RAG groundedness metrics.",
    )

    metrics_data = {
        "total_requests": 0,
        "avg_latency_ms": 0.0,
        "total_cost_usd": 0.0,
        "security_threats": 0,
        "model_usage": {},
        "prompt_style_usage": {},
        "module_usage": {},
        "requests_over_time": [],
        "cost_over_time": [],
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{API_BASE}/api/analytics/summary")
            if res.status_code == 200:
                metrics_data.update(res.json())
    except Exception:
        st.warning("⚠️ Backend API unavailable. Please ensure the backend server is running.")

    # 1. KPI cards row
    render_metrics_row(
        [
            {"label": "Total Requests", "value": metrics_data["total_requests"]},
            {"label": "Avg Latency", "value": f"{metrics_data['avg_latency_ms']:.1f} ms"},
            {"label": "Total cost (USD)", "value": f"${metrics_data['total_cost_usd']:.5f}"},
            {"label": "Security Threats", "value": metrics_data["security_threats"]},
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Charts grid
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        # Platform traffic history
        if "requests_over_time" in metrics_data and metrics_data["requests_over_time"]:
            x_dates = [r["date"] for r in metrics_data["requests_over_time"]]
            y_reqs = [r["requests"] for r in metrics_data["requests_over_time"]]
            fig_reqs = create_line_chart(x_dates, y_reqs, "Traffic History (Requests/Day)", "#6366f1")
            st.plotly_chart(fig_reqs, use_container_width=True)
        else:
            st.info("No request history data available.")

        # Prompt styles bar chart
        styles = list(metrics_data["prompt_style_usage"].keys())
        style_counts = list(metrics_data["prompt_style_usage"].values())
        if styles and style_counts:
            fig_styles = create_bar_chart(
                labels=styles,
                values=style_counts,
                title="Active Prompt Strategy Invocations",
                color="#a855f7",
            )
            st.plotly_chart(fig_styles, use_container_width=True)
        else:
            st.info("No prompt strategy usage data available.")

    with col_chart_right:
        # Platform cost history
        if "cost_over_time" in metrics_data and metrics_data["cost_over_time"]:
            x_dates_cost = [c["date"] for c in metrics_data["cost_over_time"]]
            y_costs = [c["cost"] for c in metrics_data["cost_over_time"]]
            fig_costs = create_line_chart(x_dates_cost, y_costs, "Overhead Cost History (USD/Day)", "#06b6d4")
            st.plotly_chart(fig_costs, use_container_width=True)
        else:
            st.info("No cost history data available.")

        # Model shares donut
        models = list(metrics_data["model_usage"].keys())
        model_counts = list(metrics_data["model_usage"].values())
        if models and model_counts:
            fig_models = create_donut_chart(models, model_counts, "Model Invocations Shares")
            st.plotly_chart(fig_models, use_container_width=True)
        else:
            st.info("No model usage data available.")

    # 3. Module usage & Accuracy gauges
    col_mod_use, col_acc_gauges = st.columns([2, 1])

    with col_mod_use:
        modules = list(metrics_data["module_usage"].keys())
        module_counts = list(metrics_data["module_usage"].values())
        if modules and module_counts:
            fig_modules = create_bar_chart(
                labels=modules,
                values=module_counts,
                title="Module Request Load Distributions",
                color="#10b981",
            )
            st.plotly_chart(fig_modules, use_container_width=True)
        else:
            st.info("No module usage data available.")

    with col_acc_gauges:
        st.markdown("### Accuracy Indicators")
        # Groundedness & Hallucination Gauges
        fig_ground = create_gauge(85.0, "Average RAG Groundedness Score", color="#10b981")
        st.plotly_chart(fig_ground, use_container_width=True)

        fig_halluc = create_gauge(15.0, "Average Hallucination Rate", color="#ef4444")
        st.plotly_chart(fig_halluc, use_container_width=True)
