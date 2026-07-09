"""AlgoQX Studio -- LLM Explorer Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd
import numpy as np

from frontend.components.ui import page_header, glass_card, metric_card
from frontend.components.charts import (
    create_heatmap,
    create_scatter_2d,
    create_gauge,
    create_bar_chart,
)

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the LLM Explorer visualization and token tools."""
    page_header(
        title="LLM Explorer",
        subtitle="Learn how Large Language Models analyze sequences, build semantic vectors, and compute attentions.",
    )

    tab_tokenizer, tab_embeddings, tab_context, tab_cost, tab_education = st.tabs(
        [
            "Tokenizer",
            "Embeddings & Semantics",
            "Context Window",
            "Cost Estimator",
            "How LLMs Work",
        ]
    )

    # --------------------------------------------------------
    # Tab 1: Tokenizer
    # --------------------------------------------------------
    with tab_tokenizer:
        st.markdown("### Tokenizer Playground")
        st.markdown(
            "Large Language Models do not read raw strings. They ingest sequences of discrete numerical tokens. "
            "Input text is parsed using a subword vocabulary tokenizer."
        )

        tokenize_text = st.text_area(
            "Enter text to tokenize",
            placeholder="Enter text to tokenize...",
            height=100,
        )

        # Fetch available models from backend
        model_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    model_options = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not model_options:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
            return
        
        selected_tokenizer_model = st.selectbox("Select Tokenizer Encoding Schema", model_options)

        if st.button("Tokenize & Analyze"):
            try:
                with httpx.Client(timeout=5.0) as client:
                    res = client.post(
                        f"{API_BASE}/api/llm/tokenize",
                        json={"text": tokenize_text, "model": selected_tokenizer_model},
                    )

                if res.status_code == 200:
                    data = res.json()
                    tokens = data["tokens"]
                    token_count = data["token_count"]

                    # Display metrics
                    st.metric("Total Token Count", token_count)

                    # Highlighted visual output
                    st.markdown("#### Token Sequence Visualization")
                    spans = ""
                    for token in tokens:
                        spans += (
                            f"<span class='token' style='background-color: {token['color']}; "
                            f"color: #ffffff; margin-right: 4px; border-radius: 4px; padding: 2px 6px; "
                            f"display: inline-block;'>{token['text'].replace(' ', '&nbsp;')}</span>"
                        )
                    st.markdown(
                        f"<div class='token-display'>{spans}</div>",
                        unsafe_allow_html=True,
                    )

                    # Token mapping table
                    st.markdown("<br>#### Token IDs Matrix", unsafe_allow_html=True)
                    df_tokens = pd.DataFrame(
                        [
                            {
                                "Index": t["index"],
                                "Token String": repr(t["text"]),
                                "Token ID": t["id"],
                                "Bytes": t["byte_length"],
                            }
                            for t in tokens
                        ]
                    )
                    st.dataframe(df_tokens, use_container_width=True)

            except Exception as e:
                st.error(f"Error calling Tokenizer API: {e}")

    # --------------------------------------------------------
    # Tab 2: Embeddings
    # --------------------------------------------------------
    with tab_embeddings:
        st.markdown("### Vector Spaces & Similarity")
        st.markdown(
            "Embedding models project tokens into high-dimensional vector spaces where mathematically "
            "close vectors represent similar semantic concepts."
        )

        text_inputs_raw = st.text_area(
            "Enter sentences to compare (one sentence per line)",
            value=(
                "The cat runs fast.\n"
                "A kitten is chasing a mouse.\n"
                "Machine learning algorithms build models.\n"
                "Deep neural networks power artificial intelligence."
            ),
            height=120,
        )

        texts = [line.strip() for line in text_inputs_raw.split("\n") if line.strip()]

        if len(texts) < 2:
            st.warning("Please enter at least 2 sentences to run semantic analysis.")
        else:
            if st.button("Generate Embeddings Matrix"):
                try:
                    with httpx.Client(timeout=5.0) as client:
                        # 1. Similarity matrix
                        sim_res = client.post(
                            f"{API_BASE}/api/llm/similarity-matrix",
                            json=texts,
                        )
                        # 2. Embedding coords
                        coords_res = client.post(
                            f"{API_BASE}/api/llm/embedding-visualization",
                            json=texts,
                        )

                    if sim_res.status_code == 200 and coords_res.status_code == 200:
                        sim_data = sim_res.json()
                        coords_data = coords_res.json()

                        col_heat, col_scatter = st.columns(2)

                        with col_heat:
                            fig_heat = create_heatmap(
                                z=sim_data["matrix"],
                                x_labels=[f"S{i+1}" for i in range(len(texts))],
                                y_labels=[f"S{i+1}" for i in range(len(texts))],
                                title="Pairwise Cosine Similarity Matrix",
                            )
                            st.plotly_chart(fig_heat, use_container_width=True)

                        with col_scatter:
                            coords = coords_data["coordinates"]
                            x = [c[0] for c in coords]
                            y = [c[1] for c in coords]
                            labels = [f"S{i+1}: {text[:25]}..." for i, text in enumerate(texts)]

                            fig_scatter = create_scatter_2d(
                                x=x,
                                y=y,
                                labels=labels,
                                title="2D Embeddings Projections (PCA)",
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)

                        # Detailed text list
                        st.markdown("#### Sentence Mapping Index")
                        for i, t in enumerate(texts):
                            st.write(f"**S{i+1}**: {t}")

                except Exception as e:
                    st.error(f"Error computing embeddings: {e}")

    # --------------------------------------------------------
    # Tab 3: Context Window
    # --------------------------------------------------------
    with tab_context:
        st.markdown("### Context Window Visualizer")
        st.markdown(
            "Every model has a maximum token capacity. Entering inputs beyond this limit causes "
            "truncation, memory loss, or generation errors."
        )

        context_prompt = st.text_area(
            "Paste prompt content to check",
            placeholder="Enter text to analyze context window...",
            height=120,
        )

        # Fetch available models from backend
        context_model_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    context_model_options = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not context_model_options:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
        else:
            model_context_select = st.selectbox(
                "Select Target LLM Model",
                options=context_model_options,
                key="context_model",
            )

            if st.button("Check Context Usage"):
                try:
                    with httpx.Client(timeout=5.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/llm/context-window",
                            json={"text": context_prompt, "model": model_context_select},
                        )

                    if res.status_code == 200:
                        data = res.json()
                        col_gauge, col_bar = st.columns(2)

                        with col_gauge:
                            fig_gauge = create_gauge(
                                value=data["usage_percent"],
                                title=f"{data['model']} Context Consumption",
                            )
                            st.plotly_chart(fig_gauge, use_container_width=True)

                        with col_bar:
                            # Fetch context window limits from backend
                            backend_models = []
                            limits = []
                            try:
                                with httpx.Client(timeout=5.0) as client:
                                    res = client.get(f"{API_BASE}/api/llm/models")
                                    if res.status_code == 200:
                                        models_data = res.json().get("models", [])
                                        backend_models = [m["id"] for m in models_data]
                                        limits = [m.get("context_length", 131072) for m in models_data]
                            except Exception:
                                pass
                            
                            if not backend_models:
                                st.error("⚠️ Unable to fetch model context limits from backend.")
                            else:
                                fig_limits = create_bar_chart(
                                    labels=backend_models,
                                    values=limits,
                                    title="Max Token Limits Across Models",
                                )
                                st.plotly_chart(fig_limits, use_container_width=True)

                except Exception as e:
                    st.error(f"Error calculating context window: {e}")

    # --------------------------------------------------------
    # Tab 4: Cost Estimator
    # --------------------------------------------------------
    with tab_cost:
        st.markdown("### Financial Cost Estimator")

        prompt_cost_text = st.text_area(
            "Draft prompt",
            placeholder="Enter query to estimate cost...",
            height=100,
        )

        # Fetch available models from backend
        cost_model_options_new = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    cost_model_options_new = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not cost_model_options_new:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
        else:
            selected_cost_model = st.selectbox(
                "Select target model to estimate",
                options=cost_model_options_new,
                key="cost_model",
            )

            output_tokens_slide = st.slider("Expected output tokens", 50, 4000, 500)

            if st.button("Estimate Cost"):
                try:
                    with httpx.Client(timeout=5.0) as client:
                        res = client.post(
                            f"{API_BASE}/api/llm/estimate-cost",
                            json={
                                "text": prompt_cost_text,
                                "model": selected_cost_model,
                                "expected_output_tokens": output_tokens_slide,
                            },
                        )

                    if res.status_code == 200:
                        data = res.json()
                        st.subheader("Cost Estimation")

                        col_c1, col_c2, col_c3 = st.columns(3)
                        with col_c1:
                            st.markdown(
                                metric_card("Input Cost", f"${data['input_cost']:.6f}"),
                                unsafe_allow_html=True,
                            )
                        with col_c2:
                            st.markdown(
                                metric_card("Output Cost", f"${data['output_cost']:.6f}"),
                                unsafe_allow_html=True,
                            )
                        with col_c3:
                            st.markdown(
                                metric_card("Total Cost", f"${data['total_cost']:.6f}"),
                                unsafe_allow_html=True,
                            )

                except Exception as e:
                    st.error(f"Error computing cost estimate: {e}")

    # --------------------------------------------------------
    # Tab 5: How LLMs Work
    # --------------------------------------------------------
    with tab_education:
        st.markdown("### Transformer Architecture Explanation")

        st.markdown(
            """
            #### 1. The Core Pipeline
            ```
            [Input Text] 
                 │
                 ▼
            [Tokenizer] ─────► Parses raw characters to index tokens (IDs)
                 │
                 ▼
            [Embeddings] ────► Converts token IDs into continuous semantic vectors
                 │
                 ▼
            [Self-Attention] ► Tokens compute weights showing correlation to other words
                 │
                 ▼
            [Feed Forward] ──► Applies activation functions to representations
                 │
                 ▼
            [Linear Output] ─► Selects the next token using Softmax probability distribution
            ```
            
            #### 2. The Self-Attention Equation
            $$Attention(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$
            
            - **Queries (Q)**: What a word is searching for.
            - **Keys (K)**: What a word offers.
            - **Values (V)**: The actual content weight of the word.
            """
        )
