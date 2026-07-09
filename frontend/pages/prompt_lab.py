"""AlgoQX Studio -- Prompt Lab Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx

from frontend.components.ui import page_header, glass_card, metric_card
from frontend.components.charts import create_radar_chart

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the Prompt Lab comparison workspace."""
    page_header(
        title="Prompt Lab",
        subtitle="Compare standard prompt engineering styles side-by-side on latency, quality, and cost.",
    )

    prompt = st.text_area(
        "Enter prompt content",
        placeholder="Enter your base prompt...",
        height=100,
    )

    col_config_left, col_config_right = st.columns(2)
    with col_config_left:
        # Fetch available models from backend
        prompt_model_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    prompt_model_options = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not prompt_model_options:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
            st.stop()
        
        model = st.selectbox(
            "Select target model",
            options=prompt_model_options,
        )
    with col_config_right:
        strategies_choices = [
            "zero_shot",
            "few_shot",
            "chain_of_thought",
            "role_prompt",
            "json_output",
            "xml_output",
            "system_prompt",
        ]
        selected_strategies = st.multiselect(
            "Select active strategy variants to test",
            options=strategies_choices,
            default=strategies_choices,
        )

    if st.button("Run Strategies Comparison"):
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Executing comparison tests..."):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/prompt/compare",
                            json={
                                "prompt": prompt,
                                "model": model,
                                "strategies": selected_strategies,
                            },
                        )

                    if res.status_code == 200:
                        data = res.json()
                        results = data["results"]

                        # 1. Radar comparison chart
                        st.markdown("### Performance Vector Comparison")
                        radar_categories = ["Quality", "Consistency", "Speed", "Cost Efficiency"]

                        # Reconstruct scores (Speed and Cost are inverted scaling for chart plotting)
                        for r in results:
                            # Latency mapping: 0ms -> 100 score, 5000ms+ -> 10 score
                            speed_score = max(10.0, 100.0 - (r["latency_ms"] / 50.0))
                            # Cost mapping: $0 -> 100 score, $0.01+ -> 10 score
                            cost_score = max(10.0, 100.0 - (r["cost_usd"] * 100000.0))

                            fig_radar = create_radar_chart(
                                categories=radar_categories,
                                values=[
                                    r["quality_score"],
                                    r["consistency_score"],
                                    speed_score,
                                    cost_score,
                                ],
                                title=f"Strategy: {r['strategy'].upper()}",
                            )
                            st.plotly_chart(fig_radar, use_container_width=True)

                        # 2. Results Cards Grid
                        st.markdown("<br>### Execution Outputs Grid", unsafe_allow_html=True)

                        # Display in columns
                        cols = st.columns(2)
                        for idx, r in enumerate(results):
                            col_idx = idx % 2
                            with cols[col_idx]:
                                label_html = f"<h4 style='margin-bottom:8px;'>{r['strategy'].upper()}</h4>"
                                st.markdown(
                                    glass_card(
                                        f"{label_html}"
                                        f"<div style='background:rgba(0,0,0,0.2); padding:12px; border-radius:6px; "
                                        f"max-height:220px; overflow-y:auto; font-size:0.875rem; margin-bottom:12px;'>{r['response']}</div>"
                                        f"<div style='display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted);'>"
                                        f"<span>Latency: {r['latency_ms']:.1f}ms</span>"
                                        f"<span>Cost: ${r['cost_usd']:.5f}</span>"
                                        f"<span>Tokens: {r['total_tokens']}</span>"
                                        f"</div>"
                                    ),
                                    unsafe_allow_html=True,
                                )

                except Exception as e:
                    st.error(f"Error calling Prompt Lab API: {e}")
