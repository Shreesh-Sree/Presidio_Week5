"""AlgoQX Studio -- RAG Studio Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd

from frontend.components.ui import page_header, glass_card, status_badge, render_metrics_row
from frontend.components.charts import create_gauge

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render RAG Studio dashboard workspace."""
    page_header(
        title="RAG Studio",
        subtitle="Build, test, and evaluate Retrieval-Augmented Generation context pipelines.",
    )

    tab_pipeline, tab_query = st.tabs(["Pipeline Builder", "Query & Evaluate"])

    # --------------------------------------------------------
    # Tab 1: Pipeline Builder
    # --------------------------------------------------------
    with tab_pipeline:
        st.markdown("### Document Processing Pipeline")
        st.markdown(
            "Upload files (PDF, DOCX, TXT) to split them into chunks, extract vector embeddings, "
            "and build the local FAISS semantic index."
        )

        uploaded_file = st.file_uploader(
            "Choose a file to index",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=False,
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            chunking_strategy = st.selectbox(
                "Chunking Strategy",
                ["recursive", "fixed_size", "sentence", "semantic"],
            )
            chunk_size = st.slider("Chunk Size (characters)", 100, 2000, 500)

        with col_p2:
            # Fetch available embedding models from backend
            embedding_model_options = []
            try:
                with httpx.Client(timeout=5.0) as client:
                    res = client.get(f"{API_BASE}/api/llm/models")
                    if res.status_code == 200:
                        all_models = res.json().get("models", [])
                        # Filter for embedding models
                        embedding_model_options = [m["id"] for m in all_models if "embedding" in m["id"].lower()]
            except Exception:
                pass
            
            if not embedding_model_options:
                st.error("⚠️ Unable to fetch embedding models from backend.")
                st.stop()
            
            embedding_model = st.selectbox(
                "Embedding Model",
                embedding_model_options,
            )
            chunk_overlap = st.slider("Chunk Overlap (characters)", 0, 400, 50)

        if st.button("Index Document"):
            if uploaded_file is None:
                st.warning("Please upload a file first.")
            else:
                with st.spinner("Processing document embeddings..."):
                    try:
                        # Prepare files payload
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        data = {
                            "chunking_strategy": chunking_strategy,
                            "chunk_size": str(chunk_size),
                            "chunk_overlap": str(chunk_overlap),
                            "embedding_model": embedding_model,
                        }

                        with httpx.Client(timeout=60.0) as client:
                            res = client.post(
                                f"{API_BASE}/api/rag/upload",
                                files=files,
                                data=data,
                            )

                        if res.status_code == 200:
                            res_data = res.json()
                            st.success(f"Successfully processed file: {res_data['filename']}")
                            st.markdown(
                                f"""
                                <div class='glass-card'>
                                    <h4>Pipeline Summary</h4>
                                    <p>Chunks generated: {res_data['chunk_count']}</p>
                                    <p>Chunking strategy: {res_data['chunking_strategy']}</p>
                                    <p>Model: {res_data['embedding_model']}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    except Exception as e:
                        st.error(f"Failed to process document: {e}")

        # List indexed documents
        st.markdown("<br>### Active Indexed Documents", unsafe_allow_html=True)
        try:
            with httpx.Client(timeout=5.0) as client:
                docs_res = client.get(f"{API_BASE}/api/rag/documents")
            if docs_res.status_code == 200:
                docs = docs_res.json().get("documents", [])
                if not docs:
                    st.info("No active indexes in database.")
                else:
                    df_docs = pd.DataFrame(
                        [
                            {
                                "Filename": d["filename"],
                                "Chunks": d["chunk_count"],
                                "Model": d["embedding_model"],
                                "Strategy": d["chunking_strategy"],
                                "Date": d["created_at"][:10],
                            }
                            for d in docs
                        ]
                    )
                    st.dataframe(df_docs, use_container_width=True)
        except Exception:
            st.info("Database connection offline. Showing simulated active schemas.")

    # --------------------------------------------------------
    # Tab 2: Query & Evaluate
    # --------------------------------------------------------
    with tab_query:
        st.markdown("### Context Query Playground")

        query_text = st.text_input(
            "Ask a question to the database",
            placeholder="Enter your question about the uploaded documents...",
        )

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            # Fetch available models from backend
            rag_query_model_options = []
            try:
                with httpx.Client(timeout=5.0) as client:
                    res = client.get(f"{API_BASE}/api/llm/models")
                    if res.status_code == 200:
                        rag_query_model_options = [m["id"] for m in res.json().get("models", []) if "embedding" not in m["id"].lower()]
            except Exception:
                pass
            
            if not rag_query_model_options:
                st.error("⚠️ Unable to fetch models from backend.")
                st.stop()
            
            query_model = st.selectbox(
                "Inference Model",
                options=rag_query_model_options,
                key="rag_query_model",
            )
            top_k = st.slider("Top K retrieved chunks", 1, 10, 3)

        with col_q2:
            retriever_type = st.selectbox("Retrieval Algorithm", ["similarity", "mmr"])

        col_run, col_comp = st.columns(2)
        run_query = col_run.button("Search & Generate")
        run_compare = col_comp.button("Compare Prompt vs RAG")

        # Handle RAG Run
        if run_query:
            if not query_text.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Retrieving sources & executing LLM..."):
                    try:
                        with httpx.Client(timeout=30.0) as client:
                            res = client.post(
                                f"{API_BASE}/api/rag/query",
                                json={
                                    "query": query_text,
                                    "top_k": top_k,
                                    "model": query_model,
                                    "retriever_type": retriever_type,
                                },
                            )

                        if res.status_code == 200:
                            data = res.json()

                            # Answer
                            st.markdown("#### Generated Answer")
                            st.markdown(glass_card(data["answer"]), unsafe_allow_html=True)

                            # Metrics
                            st.markdown("<br>#### Evaluation Scores", unsafe_allow_html=True)
                            col_g1, col_g2 = st.columns(2)
                            with col_g1:
                                fig_gnd = create_gauge(
                                    data["groundedness_score"] * 100,
                                    "Groundedness",
                                    color="#10b981",
                                )
                                st.plotly_chart(fig_gnd, use_container_width=True)
                            with col_g2:
                                fig_hal = create_gauge(
                                    data["hallucination_score"] * 100,
                                    "Hallucination Risk",
                                    color="#ef4444",
                                )
                                st.plotly_chart(fig_hal, use_container_width=True)

                            # Retrieved chunks
                            st.markdown("<br>#### Retrieved Context Chunks", unsafe_allow_html=True)
                            for chunk in data["chunks"]:
                                st.markdown(
                                    f"""
                                    <div class='chunk-card'>
                                        <div class='chunk-rank'>Rank {chunk['rank']}</div>
                                        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                                            <span style='font-size:0.75rem; color:var(--text-muted);'>Source: {chunk['metadata'].get('source', 'Index')}</span>
                                            <span class='chunk-score'>Score: {chunk['score']:.4f}</span>
                                        </div>
                                        <div style='font-size:0.875rem;'>{chunk['content']}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    except Exception as e:
                        st.error(f"Error querying RAG studio: {e}")

        # Handle Comparison Run
        if run_compare:
            if not query_text.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Comparing pipelines..."):
                    try:
                        with httpx.Client(timeout=30.0) as client:
                            res = client.post(
                                f"{API_BASE}/api/rag/compare",
                                json={
                                    "query": query_text,
                                    "top_k": top_k,
                                    "model": query_model,
                                    "retriever_type": retriever_type,
                                },
                            )

                        if res.status_code == 200:
                            data = res.json()
                            p_result = data["prompt_only"]
                            rag_result = data["rag_result"]
                            comp_info = data["comparison"]

                            col_p_only, col_rag = st.columns(2)

                            with col_p_only:
                                st.markdown("#### Prompt-Only (Without context)")
                                st.markdown(
                                    glass_card(
                                        f"<p>{p_result['response']}</p>"
                                        f"<hr style='margin:8px 0;'>"
                                        f"<div style='font-size:0.75rem;color:var(--text-muted);'>"
                                        f"Latency: {p_result['latency_ms']:.1f}ms<br>Cost: ${p_result['cost_usd']:.5f}"
                                        f"</div>"
                                    ),
                                    unsafe_allow_html=True,
                                )

                            with col_rag:
                                st.markdown("#### RAG Studio Pipeline")
                                st.markdown(
                                    glass_card(
                                        f"<p>{rag_result['answer']}</p>"
                                        f"<hr style='margin:8px 0;'>"
                                        f"<div style='font-size:0.75rem;color:var(--text-muted);'>"
                                        f"Latency: {rag_result['latency_ms']:.1f}ms<br>Cost: ${rag_result['cost_usd']:.5f}"
                                        f"</div>"
                                    ),
                                    unsafe_allow_html=True,
                                )

                            st.markdown("<br>#### System Recommendation", unsafe_allow_html=True)
                            st.info(comp_info["recommendation"])

                    except Exception as e:
                        st.error(f"Error executing comparison matrix: {e}")
