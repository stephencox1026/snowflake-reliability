"""Shared chart theme — apply to every chart, never style individually.

Plotly is imported lazily so the UI can start without paying cold-import cost.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ui.tokens import (
    ACCENT,
    CATEGORY_COLORS,
    CHART_HEIGHT,
    CHART_MARGIN,
    FONT_MONO,
    FONT_UI,
    GRID_OPACITY,
    NEUTRAL,
)

_PLOTLY_TEMPLATE = None


def _go():
    import plotly.graph_objects as go

    return go


def _get_template():
    global _PLOTLY_TEMPLATE
    if _PLOTLY_TEMPLATE is None:
        go = _go()
        _PLOTLY_TEMPLATE = go.layout.Template(
            layout=go.Layout(
                font=dict(family=FONT_UI, size=13, color=NEUTRAL[700]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=CHART_MARGIN,
                colorway=[ACCENT, NEUTRAL[400], NEUTRAL[200], NEUTRAL[700]],
                xaxis=dict(
                    showgrid=True,
                    gridcolor=f"rgba(61, 69, 85, {GRID_OPACITY})",
                    zeroline=False,
                    showline=False,
                    ticks="",
                    title_font=dict(size=13, color=NEUTRAL[400]),
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    ticks="",
                    title_font=dict(size=13, color=NEUTRAL[400]),
                ),
                hoverlabel=dict(
                    bgcolor=NEUTRAL[900],
                    font=dict(family=FONT_UI, size=12, color=NEUTRAL[50]),
                    bordercolor=NEUTRAL[900],
                ),
            )
        )
    return _PLOTLY_TEMPLATE


def _truncate_label(label: str, max_len: int = 28) -> str:
    text = str(label).strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"


def _bar_colors(labels: list[str], highlight: str | None = None) -> list[str]:
    muted = NEUTRAL[200]
    colors: list[str] = []
    for label in labels:
        mapped = CATEGORY_COLORS.get(label, muted)
        if highlight and label != highlight:
            colors.append(muted)
        else:
            colors.append(mapped)
    return colors


def horizontal_bar_chart(
    frame: pd.DataFrame,
    *,
    category_col: str,
    value_col: str,
    title: str,
    x_axis_title: str = "Count",
    highlight: str | None = None,
    category_order: list[str] | None = None,
    empty_message: str = "No data available for this chart.",
) -> Any:
    """Horizontal bars. category_order is top→bottom (e.g. Critical, High, Medium, Low)."""
    if frame.empty or frame[value_col].sum() == 0:
        return None

    go = _go()
    chart_frame = frame.copy()
    chart_frame[category_col] = chart_frame[category_col].astype(str)
    chart_frame[value_col] = pd.to_numeric(chart_frame[value_col], errors="coerce").fillna(0)

    if category_order:
        # Desired visual order is top→bottom. Plotly draws the first y value at the
        # bottom, so reverse once and do not re-sort by value.
        lookup = {
            str(row[category_col]): float(row[value_col])
            for _, row in chart_frame.iterrows()
        }
        top_to_bottom = [str(c) for c in category_order]
        raw_labels = list(reversed(top_to_bottom))
        values = [lookup.get(label, 0.0) for label in raw_labels]
    else:
        chart_frame = chart_frame.sort_values(value_col, ascending=True)
        raw_labels = chart_frame[category_col].tolist()
        values = chart_frame[value_col].tolist()

    labels = [_truncate_label(lab) for lab in raw_labels]
    colors = _bar_colors(raw_labels, highlight=highlight)

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{int(v)}" for v in values],
            textposition="outside",
            textfont=dict(size=12, color=NEUTRAL[700], family=FONT_MONO),
            cliponaxis=False,
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(
        template=_get_template(),
        title=dict(text=title, x=0, font=dict(size=14, color=NEUTRAL[900])),
        height=CHART_HEIGHT,
        xaxis=dict(title=x_axis_title, rangemode="tozero"),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=raw_labels,
            autorange=False,
        ),
        showlegend=False,
    )
    return fig


def empty_chart_figure(message: str, action: str = "") -> Any:
    """Graceful empty state — never a blank white rectangle."""
    go = _go()
    annotations = [
        dict(
            text=message,
            x=0.5,
            y=0.55,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color=NEUTRAL[700], family=FONT_UI),
        )
    ]
    if action:
        annotations.append(
            dict(
                text=action,
                x=0.5,
                y=0.42,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=13, color=NEUTRAL[400], family=FONT_UI),
            )
        )
    fig = go.Figure()
    fig.update_layout(
        template=_get_template(),
        height=CHART_HEIGHT,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=annotations,
    )
    return fig


def render_chart(
    fig: Any | None,
    *,
    empty_message: str,
    empty_action: str = "Run make demo to seed pipeline data.",
) -> None:
    """Render chart or token-compliant empty state."""
    import streamlit as st

    if fig is None:
        st.plotly_chart(
            empty_chart_figure(empty_message, empty_action),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        return
    fig.update_layout(template=_get_template())
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def criticality_distribution_chart(summary: dict[str, Any]) -> Any:
    # Locked visual order: Critical (top) → High → Medium → Low (bottom)
    order = ["Critical", "High", "Medium", "Low"]
    frame = pd.DataFrame(
        [
            {"level": "Critical", "count": int(summary.get("critical", 0) or 0)},
            {"level": "High", "count": int(summary.get("high", 0) or 0)},
            {"level": "Medium", "count": int(summary.get("medium", 0) or 0)},
            {"level": "Low", "count": int(summary.get("low", 0) or 0)},
        ]
    )
    return horizontal_bar_chart(
        frame,
        category_col="level",
        value_col="count",
        title="Criticality mix — Critical, High, Medium, Low",
        x_axis_title="Pipelines",
        category_order=order,
    )
