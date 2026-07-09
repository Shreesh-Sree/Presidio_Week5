"""AlgoQX Studio -- Application Builder Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx

from frontend.components.ui import page_header, glass_card

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the automatic application generator code space."""
    page_header(
        title="Application Builder",
        subtitle="Generate production-ready FastAPI endpoints and Streamlit frontend pages automatically.",
    )

    st.markdown("### Select Application Blueprint Template")

    col_blueprints = st.columns(4)

    blueprints = [
        {"id": "chatbot", "name": "Conversational Chatbot", "desc": "Chat completion with history memory."},
        {"id": "summarizer", "name": "Text Summarizer", "desc": "Condense logs or documents."},
        {"id": "document_qa", "name": "Document QA", "desc": "Answer questions over context docs."},
        {"id": "sentiment_analyzer", "name": "Sentiment Analyzer", "desc": "Classify text emotions."},
    ]

    # Handle session state for selected blueprint
    if "selected_blueprint" not in st.session_state:
        st.session_state.selected_blueprint = "chatbot"

    for idx, bp in enumerate(blueprints):
        with col_blueprints[idx]:
            card_class = "glass-card"
            if st.session_state.selected_blueprint == bp["id"]:
                card_class = "glass-card active"

            # Create visual cards
            st.markdown(
                f"""
                <div class='{card_class}' style='height: 120px;'>
                    <h4 style='margin-top:0;'>{bp['name']}</h4>
                    <p style='color:var(--text-secondary); font-size:0.75rem;'>{bp['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    selected_bp_radio = st.radio(
        "Choose Blueprint template to configure",
        options=["chatbot", "summarizer", "document_qa", "sentiment_analyzer"],
        horizontal=True,
    )
    st.session_state.selected_blueprint = selected_bp_radio

    st.markdown("<br>### Configuration Settings", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        # Fetch available models from backend
        app_model_options = []
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{API_BASE}/api/llm/models")
                if res.status_code == 200:
                    app_model_options = [m["id"] for m in res.json().get("models", [])]
        except Exception:
            pass
        
        if not app_model_options:
            st.error("⚠️ Unable to fetch models from backend. Please ensure the backend server is running.")
            st.stop()
        
        model = st.selectbox(
            "Target LLM Model",
            options=app_model_options,
        )
    with col_c2:
        include_rag = st.checkbox("Enable RAG context pipeline", value=False)
        include_memory = st.checkbox("Enable persistence conversation memory", value=True)

    if st.button("Generate Codebases"):
        with st.spinner("Generating scripts and configurations..."):
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(
                        f"{API_BASE}/api/app/generate",
                        json={
                            "app_type": st.session_state.selected_blueprint,
                            "model": model,
                            "include_rag": include_rag,
                            "include_memory": include_memory,
                        },
                    )

                if res.status_code == 200:
                    data = res.json()

                    tab_fastapi, tab_streamlit, tab_swagger, tab_reqs = st.tabs(
                        [
                            "FastAPI Endpoint",
                            "Streamlit Page",
                            "OpenAPI/Swagger Schema",
                            "Requirements.txt",
                        ]
                    )

                    with tab_fastapi:
                        st.code(data["fastapi_code"], language="python")

                    with tab_streamlit:
                        st.code(data["streamlit_code"], language="python")

                    with tab_swagger:
                        st.json(data["swagger_spec"])

                    with tab_reqs:
                        reqs_text = "\n".join(data["requirements"])
                        st.code(reqs_text, language="text")

            except Exception as e:
                st.error(f"Failed to generate application blueprint: {e}")
