"""AlgoQX Studio -- Reusable UI Components.

Provides metric cards, headers, status badges, and other
shared UI elements used across all pages.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st


API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def load_css() -> None:
    """Load the global CSS stylesheet."""
    css_path = Path(__file__).parent.parent / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", border: bool = True) -> None:
    """Render a consistent page header."""
    st.markdown(
        f'<h1 class="section-header" style="{"border-bottom: 1px solid rgba(255,255,255,0.06);" if border else "border:none;"}'
        f'margin-top:0;">{title}</h1>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<p class="section-subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def metric_card(label: str, value: str, delta: str = "", delta_type: str = "positive") -> str:
    """Generate HTML for a metric card.

    Returns HTML string -- use with st.markdown(html, unsafe_allow_html=True).
    """
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_type == "positive" else "negative"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def render_metrics_row(metrics: list[dict]) -> None:
    """Render a row of metric cards.

    Args:
        metrics: List of dicts with keys: label, value, delta (optional), delta_type (optional)
    """
    cols = st.columns(len(metrics))
    for i, m in enumerate(metrics):
        with cols[i]:
            html = metric_card(
                label=m["label"],
                value=str(m["value"]),
                delta=m.get("delta", ""),
                delta_type=m.get("delta_type", "positive"),
            )
            st.markdown(html, unsafe_allow_html=True)


def status_badge(text: str, status: str = "info") -> str:
    """Generate HTML for a status badge.

    Args:
        text: Badge text
        status: One of 'success', 'warning', 'error', 'info'
    """
    return f'<span class="status-badge {status}">{text}</span>'


def glass_card(content: str, animate: bool = True) -> str:
    """Wrap content in a glass-card div."""
    anim_class = "animate-in" if animate else ""
    return f'<div class="glass-card {anim_class}">{content}</div>'


def section_divider() -> None:
    """Render a subtle section divider."""
    st.markdown("<hr>", unsafe_allow_html=True)


def empty_state(message: str, icon: str = "") -> None:
    """Display an empty state message."""
    st.markdown(
        f"""
        <div style="text-align:center; padding:3rem 1rem; color:var(--text-muted);">
            <div style="font-size:2.5rem; margin-bottom:1rem; opacity:0.5;">{icon}</div>
            <div style="font-size:1rem;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def code_block(code: str, language: str = "python") -> None:
    """Display code in a styled code block."""
    st.code(code, language=language)


def gradient_text(text: str, size: str = "2rem") -> str:
    """Generate gradient text HTML."""
    return (
        f'<span class="gradient-text" style="font-size:{size}; font-weight:800; '
        f'letter-spacing:-0.03em;">{text}</span>'
    )
