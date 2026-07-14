"""KPI strip helpers — one card style everywhere."""

from __future__ import annotations

import html
import re
from typing import Any

import streamlit as st

from ui.tokens import CATEGORY_COLORS, DANGER, NEUTRAL, WARNING

_TONE_CLASS = {
    "critical": "kpi-card--critical",
    "high": "kpi-card--high",
    "medium": "kpi-card--medium",
    "low": "kpi-card--low",
}

# Locked Critical → High → Medium → Low; colors match CATEGORY_COLORS / KPI top bars
_MIX_ORDER = (
    ("Critical", "critical", DANGER),
    ("High", "high", WARNING),
    ("Medium", "medium", NEUTRAL[400]),
    ("Low", "low", NEUTRAL[200]),
)


def _tone_from_label(label: str) -> str:
    key = re.sub(r"[^a-z]", "", label.lower())
    return _TONE_CLASS.get(key, "")


def kpi_strip(items: list[tuple], *, columns: int = 4) -> None:
    """Boxed KPI cards with optional tone for a colored top bar."""
    if not items:
        return
    normalized: list[tuple[str, str, str]] = []
    for item in items:
        label, value = item[0], item[1]
        tone = item[2] if len(item) >= 3 else ""
        tone_class = _TONE_CLASS.get(str(tone).lower(), "") or _tone_from_label(str(label))
        normalized.append((str(label), str(value), tone_class))

    for start in range(0, len(normalized), columns):
        chunk = normalized[start : start + columns]
        cols = st.columns(len(chunk))
        for col, (label, value, tone_class) in zip(cols, chunk):
            with col:
                cls = f"kpi-card {tone_class}".strip()
                st.markdown(
                    f'<div class="{cls}">'
                    f'<span class="kpi-label">{html.escape(label)}</span>'
                    f'<span class="kpi-value">{html.escape(value)}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )


def criticality_kpi_strip(items: list[tuple[str, str | int, str]]) -> None:
    """Critical/High/Medium/Low cards with matching top accent bars."""
    kpi_strip(
        [(label, value, tone) for label, value, tone in items],
        columns=len(items) or 4,
    )


def criticality_mix_html(summary: dict[str, Any]) -> str:
    """Token-colored Critical→High→Medium→Low bars (no Plotly)."""
    counts = {
        "critical": int(summary.get("critical", 0) or 0),
        "high": int(summary.get("high", 0) or 0),
        "medium": int(summary.get("medium", 0) or 0),
        "low": int(summary.get("low", 0) or 0),
    }
    maximum = max(counts.values()) if counts else 0

    def _width_pct(value: int) -> float:
        if value <= 0 or maximum <= 0:
            return 0.0
        return 100.0 * value / maximum

    rows: list[str] = []
    for label, key, color in _MIX_ORDER:
        value = counts[key]
        bar_color = CATEGORY_COLORS.get(label, color)
        width_pct = _width_pct(value)
        rows.append(
            "<div class='crit-mix-row'>"
            f"<span class='crit-mix-label'>{html.escape(label)}</span>"
            "<div class='crit-mix-plot'>"
            "<div class='crit-mix-zero'></div>"
            f"<div class='crit-mix-bar' style='width:{width_pct:.2f}%;background:{bar_color};'></div>"
            f"<span class='crit-mix-value' style='left:calc({width_pct:.2f}% + 8px)'>{value}</span>"
            "</div>"
            "</div>"
        )

    body = "".join(rows)
    return (
        "<div class='crit-mix'>"
        "<div class='crit-mix-title'>Criticality mix — Critical, High, Medium, Low</div>"
        f"{body}"
        "</div>"
    )


def render_criticality_mix(summary: dict[str, Any]) -> None:
    st.markdown(criticality_mix_html(summary), unsafe_allow_html=True)
