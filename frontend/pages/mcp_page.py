"""AlgoQX Studio -- Model Context Protocol Frontend Page."""

from __future__ import annotations

import streamlit as st
import httpx
import pandas as pd

from frontend.components.ui import page_header, glass_card, status_badge
from frontend.components.charts import create_heatmap

API_BASE = "http://localhost:8000"


def render() -> None:
    """Render the Model Context Protocol (MCP) comparison and demo page."""
    page_header(
        title="Model Context Protocol",
        subtitle="Understand the universal open-source integration standard for linking LLMs directly to local tools.",
    )

    tab_overview, tab_comparison, tab_demo = st.tabs(
        ["Overview", "MCP vs REST API", "Live Demo Simulation"]
    )

    # --------------------------------------------------------
    # Tab 1: Overview
    # --------------------------------------------------------
    with tab_overview:
        st.markdown("### Protocol Primitives & Architecture")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(
                """
                The Model Context Protocol (MCP) standardizes how clients expose local databases, 
                files, and scripts to LLMs. Instead of building bespoke API logic, developer hosts 
                connect MCP servers that declare their capabilities dynamically.
                
                #### Core Primitives
                - **Tools**: Actions the model can execute to mutate state or call scripts (e.g. `write_file`).
                - **Resources**: URI-based data access routes letting models query file content or database schema details.
                - **Prompts**: Reusable guidelines or user prompt templates exposed by servers.
                """
            )

        with col_right:
            st.markdown("#### MCP Topology Diagram")
            st.markdown(
                """
                ```
                ┌────────────────────────────────┐
                │       AlgoQX Host Studio       │
                └───────────────┬────────────────┘
                                │ (JSON-RPC 2.0)
                                ▼
                ┌────────────────────────────────┐
                │        MCP Client Session      │
                └───────────────┬────────────────┘
                                │ (Transport: Stdio/SSE)
                                ▼
                ┌────────────────────────────────┐
                │           MCP Server           │
                ├────────────────────────────────┤
                │  📁 Filesystem  │  🗄️ SQLite   │
                │  💻 Browser     │  🐙 GitHub   │
                └────────────────────────────────┘
                ```
                """
            )

        st.markdown("<br>### Supported Connectors Directory", unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(
                glass_card(
                    "<h4>Filesystem Connector</h4>"
                    "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                    "Read/Write capabilities. Restricts access to selected directories."
                    "</p>"
                ),
                unsafe_allow_html=True,
            )
        with col_c2:
            st.markdown(
                glass_card(
                    "<h4>SQLite Connector</h4>"
                    "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                    "Enables LLM to directly run raw SQL statements and fetch schemas."
                    "</p>"
                ),
                unsafe_allow_html=True,
            )
        with col_c3:
            st.markdown(
                glass_card(
                    "<h4>GitHub Connector</h4>"
                    "<p style='color:var(--text-secondary);font-size:0.875rem;'>"
                    "Read/write repos, create pull requests, manage issues."
                    "</p>"
                ),
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # Tab 2: MCP vs REST
    # --------------------------------------------------------
    with tab_comparison:
        st.markdown("### Structural Comparison Matrix")

        comparison_data = [
            {
                "Feature": "Integration Coupling",
                "REST API (Traditional)": "Tight Coupling (Requires custom endpoints for each tool)",
                "MCP (Modern Standard)": "Loose Coupling (Model calls any server tool dynamically)",
            },
            {
                "Feature": "Discovery Model",
                "REST API (Traditional)": "Static OpenAPI/Swagger mapping, manual code generation",
                "MCP (Modern Standard)": "Dynamic Discovery (Model queries tool schema list at startup)",
            },
            {
                "Feature": "Connection Transport",
                "REST API (Traditional)": "Stateless HTTP Requests",
                "MCP (Modern Standard)": "Stateful sessions over standard inputs/outputs (Stdio/SSE)",
            },
            {
                "Feature": "Resource URIs",
                "REST API (Traditional)": "Bespoke REST paths (e.g. /files/content)",
                "MCP (Modern Standard)": "Standardized scheme routing (e.g. file://workspace/main.py)",
            },
        ]

        df_comp = pd.DataFrame(comparison_data)
        st.dataframe(df_comp, use_container_width=True)

    # --------------------------------------------------------
    # Tab 3: Demo
    # --------------------------------------------------------
    with tab_demo:
        st.markdown("### Live Transport Simulation")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown("#### Traditional REST API Call")
            st.markdown(
                "Triggering a normal GET request to `https://jsonplaceholder.typicode.com/posts/1`."
            )

            if st.button("Run REST Call"):
                try:
                    with httpx.Client(timeout=10.0) as client:
                        res = client.post(f"{API_BASE}/api/mcp/demo/rest")

                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Response received in {data['latency_ms']} ms")
                        st.json(data["response"])
                        st.info(data["explanation"])
                except Exception as e:
                    st.error(f"REST fetch failed: {e}")

        with col_d2:
            st.markdown("#### Dynamic MCP Tool Call")
            st.markdown(
                "Triggering a simulated JSON-RPC 2.0 tool execution via Stdio server transport."
            )

            server_type = st.selectbox(
                "Target MCP Server Type",
                options=["filesystem", "sqlite", "github", "browser"],
            )

            tool_name = st.text_input("Tool Name", placeholder="e.g., read_file, query_db, list_issues, scrape_url")
            tool_args_json = st.text_area("Tool Arguments (JSON)", placeholder='{"path": "file.txt"}\nor\n{"query": "SELECT * FROM table"}', height=100)

            if st.button("Run MCP Tool Call"):
                try:
                    tool_args = {}
                    if tool_args_json.strip():
                        import json
                        tool_args = json.loads(tool_args_json)
                    
                    if not tool_name:
                        st.error("Please enter a tool name")
                    else:
                        with httpx.Client(timeout=10.0) as client:
                            res = client.post(
                                f"{API_BASE}/api/mcp/demo/mcp",
                                json={
                                    "server_type": server_type,
                                    "tool_name": tool_name,
                                    "arguments": tool_args,
                                },
                            )

                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Executed MCP Tool [{data['tool_name']}] in {data['latency_ms']} ms")
                            st.json(data["result"])
                            st.info(
                                "The model discovered this tool definition dynamically and resolved the connection schema "
                                "without manual endpoint coding."
                            )
                except Exception as e:
                    st.error(f"MCP execute failed: {e}")
