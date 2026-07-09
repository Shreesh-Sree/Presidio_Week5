"""AlgoQX Studio -- Privacy Center Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd

from frontend.components.ui import page_header, glass_card, status_badge
from frontend.components.charts import create_bar_chart

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the Privacy scrubbing and masking workspace."""
    page_header(
        title="Privacy Center",
        subtitle="Detect, classify, and scrub Personally Identifiable Information (PII) before sending prompts to external APIs.",
    )

    col_main_left, col_main_right = st.columns([2, 1])

    with col_main_left:
        st.markdown("### Text Privacy Sanitizer")

        privacy_text_input = st.text_area(
            "Paste prompt content to scrub",
            placeholder="Paste text containing potentially sensitive information...",
            height=120,
        )

    with col_main_right:
        st.markdown("### Filtering Configurations")

        entities_options = [
            "EMAIL",
            "PHONE",
            "CREDIT_CARD",
            "API_KEY",
            "PASSWORD",
            "PAN",
            "AADHAAR",
            "PASSPORT",
        ]
        selected_entities = st.multiselect(
            "PII Entity Selectors",
            options=entities_options,
            default=entities_options,
        )

        mask_strategy = st.selectbox(
            "Masking Strategy",
            options=["redact", "hash", "mask"],
        )

    col_btn1, col_btn2 = st.columns(2)
    run_scrub = col_btn1.button("Scrub Prompt")
    run_demo = col_btn2.button("Run Scenarios Demo")

    # Run custom scan
    if run_scrub:
        if not privacy_text_input.strip():
            st.warning("Please enter text first.")
        else:
            with st.spinner("Scrubbing sensitive credentials..."):
                try:
                    with httpx.Client(timeout=10.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/privacy/scan",
                            json={
                                "text": privacy_text_input,
                                "entity_types": selected_entities,
                                "mask_strategy": mask_strategy,
                            },
                        )

                    if res.status_code == 200:
                        data = res.json()
                        _render_scan_results(data)

                except Exception as e:
                    st.error(f"Privacy scan execution failed: {e}")

    # Run pre-configured Demo
    if run_demo:
        if not privacy_text_input.strip():
            st.warning("Please enter text first for the demo.")
        else:
            with st.spinner("Executing PII Demonstration..."):
                try:
                    with httpx.Client(timeout=10.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/privacy/demo",
                            json={
                                "text": privacy_text_input,
                                "entity_types": selected_entities,
                                "mask_strategy": mask_strategy,
                            },
                        )

                    if res.status_code == 200:
                        data = res.json()
                        _render_scan_results(data)

                except Exception as e:
                    st.error(f"Demonstration failed: {e}")

    st.markdown("<br>### Why PII Scrubbing Matters", unsafe_allow_html=True)
    with st.expander("Compliance and Security Risks Explained"):
        try:
            with httpx.Client(timeout=5.0) as client:
                exp_res = client.get(f"{API_BASE}/api/privacy/explanation")
            if exp_res.status_code == 200:
                st.write(exp_res.json()["explanation"])
        except Exception:
            st.write(
                "Passing raw identity numbers or keys to cloud APIs is a serious liability. "
                "Masking PII locally prevents data leakage, preserves compliance, and stops models "
                "from memorizing private credentials."
            )


def _render_scan_results(data: dict) -> None:
    """Helper function to render the privacy scan results section."""
    st.markdown("<br>### Scan Results Matrix", unsafe_allow_html=True)

    col_out1, col_out2 = st.columns(2)
    with col_out1:
        st.text_area("Original Prompt", data["original_text"], height=120, disabled=True)
    with col_out2:
        st.text_area("Scrubbed Safe Prompt", data["masked_text"], height=120, disabled=True)

    st.metric("Total PII Entities Scrubbed", data["entity_count"])

    if data["entities"]:
        st.markdown("#### Detected Sensitive Spans Table")
        df_ent = pd.DataFrame(
            [
                {
                    "Entity Type": e["entity_type"],
                    "Detected Value": e["value"],
                    "Masked Output": e["masked_value"],
                    "Char Position": f"{e['start']}:{e['end']}",
                    "Confidence": f"{e['confidence']:.2f}",
                }
                for e in data["entities"]
            ]
        )
        st.dataframe(df_ent, use_container_width=True)

        # Plot entity types distribution bar chart
        st.markdown("<br>#### Entity Classifications Frequencies", unsafe_allow_html=True)
        counts = {}
        for e in data["entities"]:
            counts[e["entity_type"]] = counts.get(e["entity_type"], 0) + 1

        fig_types = create_bar_chart(
            labels=list(counts.keys()),
            values=list(counts.values()),
            title="Entity Type Counts Matrix",
        )
        st.plotly_chart(fig_types, use_container_width=True)
