"""AlgoQX Studio -- Streamlit Application Entry Point.

The Operating System for Enterprise AI.
Navigation hub that routes to all module pages.
"""

from __future__ import annotations

import streamlit as st

from frontend.components.ui import load_css, gradient_text, metric_card, render_metrics_row

# -- Page Config --
st.set_page_config(
    page_title="AlgoQX Studio",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# -- Sidebar Navigation --
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 1rem 0 0.5rem 0;">
            {gradient_text("AlgoQX Studio", "1.5rem")}
            <p style="font-size:0.7rem; color:#64748b; margin-top:4px; letter-spacing:0.05em;">
                THE OPERATING SYSTEM FOR ENTERPRISE AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        options=[
            "Dashboard",
            "LLM Explorer",
            "Prompt Lab",
            "RAG Studio",
            "Agent Builder",
            "MCP",
            "App Builder",
            "Security Center",
            "Privacy Center",
            "Analytics",
            "Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="padding:8px 0; font-size:0.7rem; color:#4a5568;">
            <div style="margin-bottom:4px;">v1.0.0</div>
            <div>Built for Enterprise AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -- Page Router --
if page == "Dashboard":
    from frontend.pages.dashboard import render
    render()
elif page == "LLM Explorer":
    from frontend.pages.llm_explorer import render
    render()
elif page == "Prompt Lab":
    from frontend.pages.prompt_lab import render
    render()
elif page == "RAG Studio":
    from frontend.pages.rag_studio import render
    render()
elif page == "Agent Builder":
    from frontend.pages.agent_builder import render
    render()
elif page == "MCP":
    from frontend.pages.mcp_page import render
    render()
elif page == "App Builder":
    from frontend.pages.app_builder import render
    render()
elif page == "Security Center":
    from frontend.pages.security_center import render
    render()
elif page == "Privacy Center":
    from frontend.pages.privacy_center import render
    render()
elif page == "Analytics":
    from frontend.pages.analytics_page import render
    render()
elif page == "Settings":
    from frontend.pages.settings_page import render
    render()
