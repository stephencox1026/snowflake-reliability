"""Global theme injection and reusable UI primitives."""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from ui.tokens import (
    ACCENT,
    DANGER,
    FONT_MONO,
    FONT_SIZE,
    FONT_UI,
    NEUTRAL,
    NUMERIC_COLUMNS,
    RADIUS,
    SHADOW,
    SPACE,
    SUCCESS,
    WARNING,
)


def inject_theme() -> None:
    neutrals = NEUTRAL
    findings_bg = "#FBF3E0"
    answer_bg = "#EEF2F7"
    action_bg = "#E7F3EC"
    cause_bg = "#FBF3E0"
    st.markdown(
        f"""
        <style>
          :root {{
            --accent: {ACCENT};
            --success: {SUCCESS};
            --warning: {WARNING};
            --danger: {DANGER};
            --n50: {neutrals[50]};
            --n100: {neutrals[100]};
            --n200: {neutrals[200]};
            --n400: {neutrals[400]};
            --n700: {neutrals[700]};
            --n900: {neutrals[900]};
            --radius: {RADIUS}px;
            --shadow: {SHADOW};
            --space-1: {SPACE[1]}px;
            --space-2: {SPACE[2]}px;
            --space-3: {SPACE[3]}px;
            --space-4: {SPACE[4]}px;
            --space-5: {SPACE[5]}px;
            --space-6: {SPACE[6]}px;
            --font-ui: {FONT_UI};
            --font-mono: {FONT_MONO};
          }}

          .stApp {{
            background-color: var(--n50);
            color: var(--n900);
            font-family: var(--font-ui);
            font-size: {FONT_SIZE["base"]}px;
          }}

          h1, h2, h3, h4, h5, h6, p, label, span, div {{
            text-align: left;
          }}

          h1 {{
            font-size: {FONT_SIZE["lg"]}px;
            font-weight: 600;
            color: var(--n900);
            margin-bottom: var(--space-1);
          }}

          .app-subtitle {{
            font-size: {FONT_SIZE["sm"]}px;
            color: var(--n400);
            margin: 0 0 var(--space-4) 0;
            font-weight: 400;
          }}

          [data-testid="stSidebar"] {{
            background-color: var(--n100);
            border-right: 1px solid var(--n200);
          }}

          [data-testid="stSidebar"] h3 {{
            font-size: {FONT_SIZE["md"]}px;
            font-weight: 600;
            color: var(--n900);
            margin-top: var(--space-5);
            margin-bottom: var(--space-2);
          }}

          [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {{
            font-size: {FONT_SIZE["sm"]}px;
            color: var(--n700);
            line-height: 1.5;
          }}

          div[data-testid="stRadio"] {{
            margin-bottom: var(--space-4);
            border-bottom: 1px solid var(--n200);
            padding-bottom: var(--space-2);
          }}

          div[data-testid="stRadio"] > label {{
            display: none;
          }}

          div[data-testid="stRadio"] [role="radiogroup"] {{
            gap: var(--space-2);
            flex-wrap: wrap;
          }}

          div[data-testid="stRadio"] label[data-baseweb="radio"] {{
            font-size: {FONT_SIZE["sm"]}px;
            font-weight: 500;
            color: var(--n400);
            padding: var(--space-2) var(--space-3);
            border-radius: var(--radius) var(--radius) 0 0;
            background: transparent;
          }}

          div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
            color: var(--n900);
            border-bottom: 2px solid var(--accent);
          }}

          div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {{
            display: none;
          }}

          .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-3);
            margin-bottom: var(--space-4);
          }}

          @media (max-width: 768px) {{
            .kpi-strip {{
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
          }}

          div[data-testid="stMetric"] {{
            background: var(--n50);
            border: 1px solid {neutrals[900]};
            border-radius: var(--radius);
            box-shadow: none;
            padding: var(--space-4);
            text-align: center;
          }}

          div[data-testid="stMetricLabel"],
          div[data-testid="stMetricValue"],
          div[data-testid="stMetricDelta"] {{
            justify-content: center;
            text-align: center;
            width: 100%;
          }}

          div[data-testid="stMetricLabel"],
          div[data-testid="stMetricValue"] {{
            color: {neutrals[900]};
          }}

          div[data-testid="stMetricValue"] {{
            font-variant-numeric: tabular-nums;
          }}

          .kpi-card {{
            background: var(--n50);
            border: 1px solid {neutrals[900]};
            border-radius: var(--radius);
            box-shadow: none;
            padding: var(--space-3) var(--space-4);
            text-align: center;
            min-height: 64px;
            position: relative;
            overflow: hidden;
          }}

          .kpi-card::before {{
            content: "";
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: {neutrals[200]};
          }}

          .kpi-card--critical::before {{ background: {DANGER}; }}
          .kpi-card--high::before {{ background: {WARNING}; }}
          .kpi-card--medium::before {{ background: {neutrals[400]}; }}
          .kpi-card--low::before {{ background: {neutrals[200]}; }}

          .crit-mix {{
            margin: var(--space-4) 0 var(--space-3) 0;
          }}

          .crit-mix-title {{
            font-size: {FONT_SIZE["sm"]}px;
            font-weight: 600;
            color: {neutrals[900]};
            margin-bottom: var(--space-3);
          }}

          .crit-mix-row {{
            display: grid;
            grid-template-columns: 72px 1fr;
            gap: var(--space-3);
            align-items: center;
            margin-bottom: var(--space-2);
          }}

          .crit-mix-label {{
            font-size: {FONT_SIZE["sm"]}px;
            color: {neutrals[700]};
          }}

          .crit-mix-plot {{
            position: relative;
            height: 14px;
            width: 100%;
          }}

          .crit-mix-zero {{
            position: absolute;
            left: 0;
            top: -4px;
            bottom: -4px;
            width: 0;
            border-left: 1px solid {neutrals[700]};
            z-index: 2;
            pointer-events: none;
          }}

          .crit-mix-bar {{
            position: absolute;
            left: 0;
            top: 0;
            height: 14px;
            border-radius: 2px;
            border: 1px solid {neutrals[700]};
            box-sizing: border-box;
            min-width: 0;
            z-index: 1;
          }}

          .crit-mix-value {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-family: var(--font-mono);
            font-size: {FONT_SIZE["sm"]}px;
            font-variant-numeric: tabular-nums;
            color: {neutrals[900]};
            line-height: 1;
            white-space: nowrap;
            z-index: 3;
          }}

          .next-steps {{
            background: {answer_bg};
            border: 1px solid {ACCENT};
            border-left: 4px solid {ACCENT};
            border-radius: var(--radius);
            padding: var(--space-4);
            margin: var(--space-4) 0;
            font-size: {FONT_SIZE["sm"]}px;
            line-height: 1.55;
            color: {neutrals[900]};
          }}

          .next-steps strong.label {{
            display: block;
            font-size: {FONT_SIZE["xs"]}px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: var(--space-2);
          }}

          .next-steps ol {{
            margin: 0;
            padding-left: 1.2rem;
          }}

          .next-steps li {{
            margin-bottom: var(--space-2);
          }}

          .next-steps li:last-child {{
            margin-bottom: 0;
          }}

          .kpi-label {{
            display: block;
            font-size: 14px;
            font-weight: 400;
            letter-spacing: 0.02em;
            color: {neutrals[400]};
            margin-bottom: var(--space-1);
            text-align: center;
            font-family: var(--font-ui);
            line-height: 1.2;
          }}

          .kpi-value {{
            display: block;
            font-size: 18px;
            font-weight: 600;
            color: {neutrals[900]};
            font-variant-numeric: tabular-nums;
            font-family: var(--font-mono);
            text-align: center;
            line-height: 1.25;
            overflow-wrap: anywhere;
            word-break: break-word;
          }}

          .findings-panel {{
            background: {findings_bg};
            border: 1px solid {WARNING};
            border-left: 4px solid {WARNING};
            border-radius: var(--radius);
            padding: var(--space-4);
            margin-top: var(--space-2);
          }}

          .findings-panel ul {{
            margin: 0;
            padding-left: 1.1rem;
            color: {neutrals[900]};
            font-size: {FONT_SIZE["sm"]}px;
            line-height: 1.55;
          }}

          .findings-panel li {{
            margin-bottom: var(--space-2);
          }}

          .findings-panel li:last-child {{
            margin-bottom: 0;
          }}

          .callout {{
            border-radius: var(--radius);
            border: 1px solid var(--n200);
            padding: var(--space-4);
            margin: var(--space-3) 0;
            text-align: left;
            color: {neutrals[900]};
            font-size: {FONT_SIZE["sm"]}px;
            line-height: 1.5;
          }}

          .callout--cause {{
            background: {cause_bg};
            border-color: {WARNING};
            border-left: 4px solid {WARNING};
          }}

          .callout--action {{
            background: {action_bg};
            border-color: {SUCCESS};
            border-left: 4px solid {SUCCESS};
          }}

          .callout--answer {{
            background: {answer_bg};
            border-color: {ACCENT};
            border-left: 4px solid {ACCENT};
            font-size: {FONT_SIZE["md"]}px;
          }}

          .callout-label {{
            display: block;
            font-size: {FONT_SIZE["xs"]}px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: var(--space-2);
            color: {neutrals[900]};
          }}

          .section-title {{
            font-size: {FONT_SIZE["md"]}px;
            font-weight: 600;
            color: var(--n900);
            margin: 0 0 var(--space-3) 0;
          }}

          .section-caption {{
            font-size: {FONT_SIZE["sm"]}px;
            color: var(--n400);
            margin: 0 0 var(--space-4) 0;
          }}

          .semantic-panel {{
            border-radius: var(--radius);
            border: 1px solid var(--n200);
            padding: var(--space-3) var(--space-4);
            margin-bottom: var(--space-3);
            text-align: left;
            font-size: {FONT_SIZE["sm"]}px;
            color: var(--n700);
            background: var(--n100);
          }}

          .semantic-panel--danger {{
            border-left: 3px solid var(--danger);
          }}

          .semantic-panel--warning {{
            border-left: 3px solid var(--warning);
          }}

          .semantic-panel--success {{
            border-left: 3px solid var(--success);
          }}

          .semantic-label {{
            font-size: {FONT_SIZE["xs"]}px;
            font-weight: 600;
            color: var(--n400);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: var(--space-1);
          }}

          .empty-state {{
            text-align: center;
            padding: var(--space-7) var(--space-4);
            color: var(--n700);
            font-size: {FONT_SIZE["base"]}px;
          }}

          .empty-state p {{
            text-align: center;
            margin: 0 0 var(--space-2) 0;
          }}

          .empty-state small {{
            color: var(--n400);
            font-size: {FONT_SIZE["sm"]}px;
          }}

          div[data-testid="stDataFrame"] table {{
            font-size: {FONT_SIZE["sm"]}px;
          }}

          .stButton > button[kind="primary"] {{
            background-color: var(--accent);
            border-radius: var(--radius);
            border: none;
            font-weight: 500;
            font-size: {FONT_SIZE["sm"]}px;
            box-shadow: var(--shadow);
          }}

          .stButton > button:focus-visible,
          div[data-testid="stRadio"] label[data-baseweb="radio"]:focus-within {{
            outline: 2px solid var(--accent);
            outline-offset: 2px;
          }}

          .stSelectbox label, .stMultiSelect label {{
            font-size: {FONT_SIZE["sm"]}px;
            font-weight: 500;
            color: var(--n700);
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(f"# {html.escape(title)}")
    st.caption(subtitle)


def section_header(title: str, caption: str = "") -> None:
    st.markdown(f"### {title}")
    if caption:
        st.caption(caption)


def semantic_panel(label: str, body: str, tone: str = "default") -> None:
    st.markdown(f"**{label}**")
    if tone == "warning":
        st.warning(body)
    elif tone == "success":
        st.success(body)
    elif tone == "danger":
        st.error(body)
    else:
        st.info(body)


def empty_state(message: str, hint: str = "") -> None:
    st.info(message if not hint else f"{message}\n\n{hint}")


def callout(label: str, body: str, *, tone: str = "cause") -> None:
    """Colored container for answer, likely cause, or recommended action."""
    tone_class = {
        "cause": "callout--cause",
        "action": "callout--action",
        "answer": "callout--answer",
    }.get(tone, "callout--cause")
    st.markdown(
        f'<div class="callout {tone_class}">'
        f'<span class="callout-label">{html.escape(label)}</span>'
        f"<div>{html.escape(body)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def style_dataframe(
    df: pd.DataFrame,
    *,
    highlight_critical: bool = False,
    highlight_failed: bool = False,
) -> Any:
    if df.empty:
        return df

    numeric_cols = [col for col in df.columns if col in NUMERIC_COLUMNS]
    styler = df.style

    if numeric_cols:
        styler = styler.set_properties(
            subset=numeric_cols,
            **{
                "text-align": "right",
                "font-variant-numeric": "tabular-nums",
                "font-family": FONT_MONO,
            },
        )

    status_col = None
    for candidate in ("Status", "status", "run_status"):
        if candidate in df.columns:
            status_col = candidate
            break

    if highlight_critical and "Criticality" in df.columns:
        # Match KPI top-bar colors at 20% opacity
        critical_bg = "background-color: rgba(185, 28, 28, 0.2);"
        high_bg = "background-color: rgba(180, 83, 9, 0.2);"

        def _crit_style(row: pd.Series) -> list[str]:
            level = str(row["Criticality"]).lower()
            if level == "critical":
                style = critical_bg
            elif level == "high":
                style = high_bg
            else:
                style = ""
            return [style] * len(row)

        styler = styler.apply(_crit_style, axis=1)

    if highlight_failed and status_col is not None:
        failed_bg = f"background-color: {DANGER}28;"

        def _fail_style(row: pd.Series) -> list[str]:
            status = str(row[status_col]).lower().replace(" ", "")
            if status in {"failed", "fail", "error", "failure"}:
                return [failed_bg] * len(row)
            return [""] * len(row)

        styler = styler.apply(_fail_style, axis=1)

    return styler
