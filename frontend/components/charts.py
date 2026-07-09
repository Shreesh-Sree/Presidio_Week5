"""AlgoQX Studio -- Plotly Theme and Chart Helpers.

Consistent dark-theme chart configuration for all visualizations.
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import plotly.express as px


# -- AlgoQX Plotly Theme --
CHART_COLORS = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444",
    "#a855f7", "#ec4899", "#14b8a6", "#f97316", "#3b82f6",
]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e2e8f0", size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(color="#94a3b8"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(color="#94a3b8"),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
    ),
    hoverlabel=dict(
        bgcolor="#1e1e2e",
        font_size=12,
        font_family="Inter, sans-serif",
        bordercolor="rgba(255,255,255,0.1)",
    ),
    colorway=CHART_COLORS,
)


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply AlgoQX dark theme to a Plotly figure."""
    fig.update_layout(**CHART_LAYOUT)
    return fig


def create_gauge(
    value: float,
    title: str = "",
    max_value: float = 100,
    color: str = "#6366f1",
    suffix: str = "%",
) -> go.Figure:
    """Create a gauge/dial chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=suffix, font=dict(size=28, color="#e2e8f0")),
        title=dict(text=title, font=dict(size=14, color="#94a3b8")),
        gauge=dict(
            axis=dict(range=[0, max_value], tickcolor="#64748b"),
            bar=dict(color=color),
            bgcolor="rgba(255,255,255,0.03)",
            borderwidth=0,
            steps=[
                dict(range=[0, max_value * 0.5], color="rgba(16,185,129,0.1)"),
                dict(range=[max_value * 0.5, max_value * 0.8], color="rgba(245,158,11,0.1)"),
                dict(range=[max_value * 0.8, max_value], color="rgba(239,68,68,0.1)"),
            ],
        ),
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def create_bar_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    color: str = "#6366f1",
    horizontal: bool = False,
) -> go.Figure:
    """Create a styled bar chart."""
    if horizontal:
        fig = go.Figure(go.Bar(y=labels, x=values, orientation="h", marker_color=color))
    else:
        fig = go.Figure(go.Bar(x=labels, y=values, marker_color=color))
    fig.update_layout(title=title, height=350)
    return apply_theme(fig)


def create_line_chart(
    x: list,
    y: list,
    title: str = "",
    color: str = "#6366f1",
    fill: bool = True,
) -> go.Figure:
    """Create a styled line/area chart."""
    fig = go.Figure(go.Scatter(
        x=x, y=y,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy" if fill else None,
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)"
        if fill else None,
    ))
    fig.update_layout(title=title, height=300)
    return apply_theme(fig)


def create_donut_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
) -> go.Figure:
    """Create a styled donut/pie chart."""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=CHART_COLORS[:len(labels)]),
        textfont=dict(color="#e2e8f0"),
    ))
    fig.update_layout(title=title, height=300, showlegend=True)
    return apply_theme(fig)


def create_heatmap(
    z: list[list[float]],
    x_labels: list[str],
    y_labels: list[str],
    title: str = "",
) -> go.Figure:
    """Create a styled heatmap."""
    fig = go.Figure(go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0, "#0a0a0f"],
            [0.5, "#6366f1"],
            [1, "#06b6d4"],
        ],
        texttemplate="%{z:.2f}",
        textfont=dict(size=11, color="#e2e8f0"),
    ))
    fig.update_layout(title=title, height=400)
    return apply_theme(fig)


def create_scatter_2d(
    x: list[float],
    y: list[float],
    labels: list[str],
    title: str = "",
    colors: list[str] | None = None,
) -> go.Figure:
    """Create a 2D scatter plot for embedding visualization."""
    fig = go.Figure(go.Scatter(
        x=x, y=y,
        mode="markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=10, color="#94a3b8"),
        marker=dict(
            size=10,
            color=colors or "#6366f1",
            line=dict(width=1, color="rgba(255,255,255,0.2)"),
        ),
    ))
    fig.update_layout(title=title, height=500)
    return apply_theme(fig)


def create_scatter_3d(
    x: list[float],
    y: list[float],
    z: list[float],
    labels: list[str],
    title: str = "",
) -> go.Figure:
    """Create a 3D scatter plot for embedding visualization."""
    fig = go.Figure(go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers+text",
        text=labels,
        textfont=dict(size=8, color="#94a3b8"),
        marker=dict(
            size=6,
            color=z,
            colorscale=[[0, "#6366f1"], [1, "#06b6d4"]],
            line=dict(width=0.5, color="rgba(255,255,255,0.2)"),
        ),
    ))
    fig.update_layout(
        title=title,
        height=500,
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.04)"),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.04)"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return apply_theme(fig)


def create_radar_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    max_value: float = 100,
) -> go.Figure:
    """Create a radar/spider chart for multi-dimensional comparison."""
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],  # close the polygon
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6, color="#6366f1"),
    ))
    fig.update_layout(
        title=title,
        height=400,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, max_value],
                gridcolor="rgba(255,255,255,0.06)",
                tickfont=dict(color="#64748b"),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                tickfont=dict(color="#94a3b8"),
            ),
        ),
    )
    return apply_theme(fig)
