"""AlgoQX Studio -- Settings Configuration Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx

from frontend.components.ui import page_header, glass_card

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the configuration settings workspace."""
    page_header(
        title="Settings",
        subtitle="Manage endpoint credentials, model selection defaults, database indices, and system cache.",
    )

    # 1. LLM Endpoint configurations
    with st.expander("LLM Provider Configurations", expanded=True):
        endpoint_url = st.text_input(
            "Ollama Base URL",
            placeholder="https://ollama.algoqx.tech/v1",
        )
        api_key = st.text_input(
            "API Authentication Token (Bearer)",
            placeholder="Enter your API key...",
            type="password",
        )
        # Fetch available models from backend for default model
        settings_model_opts = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    settings_model_opts = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not settings_model_opts:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
        else:
            default_model = st.selectbox(
                "Default Inference Model",
                options=settings_model_opts,
            )

        if st.button("Test Endpoint Connection"):
            try:
                with httpx.Client(timeout=5.0) as client:
                    res = client.get(f"{API_BASE}/health")
                if res.status_code == 200:
                    st.success("Successfully established API tunnel to Ollama service host.")
                else:
                    st.error(f"Endpoint returned error status: {res.status_code}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

    # 2. Embeddings configs
    with st.expander("Embedding Models Configurations"):
        # Fetch available embedding models from backend
        embedding_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    all_models = res.json().get("models", [])
                    embedding_options = [m["id"] for m in all_models if "embedding" in m["id"].lower()]
        except Exception:
            pass
        
        if not embedding_options:
            st.error("⚠️ Unable to fetch embedding models from backend.")
            st.stop()
        
        st.selectbox(
            "Primary Vector Model",
            options=embedding_options,
        )
        st.markdown(
            """
            * Dimensions: 768
            * Max Sequence Tokens: 32768
            * Distance Space: Cosine / Inner Product
            """
        )

    # 3. RAG configs
    with st.expander("RAG Indexer Defaults"):
        st.slider("Default Chunk Size", 100, 2000, 500)
        st.slider("Default Chunk Overlap", 0, 400, 50)
        st.text_input("Local Index Storage Root Path", placeholder="./data/faiss_index")

    # 4. About card
    st.markdown("<br>### Platform Context", unsafe_allow_html=True)
    st.markdown(
        glass_card(
            "<h4>AlgoQX Studio Core v1.0.0</h4>"
            "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
            "The Operating System for Enterprise AI. Built using FastAPI backend, SQLite, FAISS, "
            "LangChain, LangGraph, and Streamlit frontend. Runs in isolated Docker containers."
            "</p>"
        ),
        unsafe_allow_html=True,
    )
