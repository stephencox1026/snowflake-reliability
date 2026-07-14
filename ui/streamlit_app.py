"""Streamlit ops dashboard — token-driven, dense-but-calm register."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.assessments import build_assessment  # noqa: E402
from ui.data_access import (  # noqa: E402
    USE_DIRECT,
    create_remediation_assignment,
    get_analyst_questions,
    get_at_risk,
    get_dashboard_summary,
    list_remediation_assignments,
    run_analyst_question,
)
from ui.kpi import criticality_kpi_strip, kpi_strip, render_criticality_mix  # noqa: E402
from ui.remediation import (  # noqa: E402
    normalize_target,
    playbook_for_signal,
    signal_label,
)
from ui.theme import (  # noqa: E402
    callout,
    empty_state,
    inject_theme,
    page_header,
    section_header,
    style_dataframe,
)

st.set_page_config(
    page_title="Snowflake Reliability Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

# Targeted action queue — not the full fleet
HEALTH_BOARD_ROW_CAP = 25

PAGES = [
    "Pipeline Health Board",
    "Metrics Explorer",
    "Solution",
]

PAGE_BLURBS = {
    "Pipeline Health Board": (
        "Today’s action queue — Critical and High pipelines that need an owner this cycle. "
        "Each row shows the driving signal and a one-line assessment so you can assign work "
        "before the next SLA miss."
    ),
    "Metrics Explorer": (
        "Ask a curated reliability question and get a plain-language answer, the proof table, "
        "likely cause, and recommended action — with the SQL visible for audit."
    ),
    "Solution": (
        "Execute the Health Board next step: assign the owning team, run the signal playbook, "
        "and record a durable assignment."
    ),
}

COLUMN_LABELS = {
    "pipeline_id": "Pipeline id",
    "pipeline_name": "Pipeline",
    "domain": "Domain",
    "owner_team": "Owner team",
    "criticality": "Criticality",
    "failure_probability": "Failure probability",
    "risk_tier": "Risk tier",
    "top_feature": "Top signal",
    "top_feature_value": "Signal value",
    "assessment": "Assessment",
}


def _format_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace("_", " ").strip()
    return text.title() if text else "—"


def _prepare_health_board_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    table = df.copy()
    table["assessment"] = table.apply(build_assessment, axis=1)

    if "failure_probability" in table.columns:
        table["failure_probability"] = table["failure_probability"].apply(
            lambda value: f"{float(value):.0%}" if pd.notna(value) else "—"
        )
    if "scored_at" in table.columns:
        table = table.drop(columns=["scored_at"])

    skip_format = {"failure_probability", "assessment"}
    for column in table.columns:
        if column in skip_format:
            continue
        table[column] = table[column].apply(_format_cell)

    out = table.rename(columns=COLUMN_LABELS)
    if "Pipeline id" in out.columns:
        out = out.drop(columns=["Pipeline id"])
    crit_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    out["_crit_ord"] = out["Criticality"].map(crit_rank).fillna(99)
    out["_prob_ord"] = (
        out["Failure probability"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .replace({"—": "-1"})
        .astype(float)
    )
    out = (
        out.sort_values(["_crit_ord", "_prob_ord"], ascending=[True, False])
        .drop(columns=["_crit_ord", "_prob_ord"])
        .reset_index(drop=True)
    )
    return out


def _focus_health_board(df: pd.DataFrame, focus: str) -> pd.DataFrame:
    if df.empty or focus == "All criticalities":
        return df
    if focus == "Action queue (Critical + High)":
        return df[df["Criticality"].isin(["Critical", "High"])].reset_index(drop=True)
    return df


def _action_queue_raw(tier: str | None = None) -> list[dict]:
    rows = get_at_risk(None if tier in (None, "All") else tier, limit=500)
    ranked = sorted(
        rows,
        key=lambda r: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                str(r.get("criticality", "")).lower(), 99
            ),
            -float(r.get("failure_probability") or 0),
        ),
    )
    return [
        r
        for r in ranked
        if str(r.get("criticality", "")).lower() in {"critical", "high"}
    ]


def _health_board_next_steps(summary: dict, top_raw: dict | None) -> None:
    critical = int(summary.get("critical", 0) or 0)
    high_risk = int(summary.get("high_risk", 0) or 0)
    target = normalize_target(top_raw)
    top_name = (target or {}).get("pipeline_name") or "—"
    top_team = _format_cell((target or {}).get("assigned_team") or "—")
    top_signal = signal_label((target or {}).get("top_signal") or "")

    items = [
        (
            f"Assign <strong>{html.escape(top_team)}</strong> to remediating "
            f"<strong>{html.escape(_format_cell(top_name))}</strong> first — top signal is "
            f"<strong>{html.escape(top_signal)}</strong>."
            if target
            else "Open the ranked table and assign the first Critical / High row to its owner."
        ),
        (
            f"There are <strong>{critical}</strong> business-critical and "
            f"<strong>{high_risk}</strong> HIGH-risk pipelines this cycle — treat Critical + HIGH "
            "as today’s incident queue, not a watchlist."
        ),
        (
            "Use <strong>Metrics Explorer</strong> to answer one focused question "
            "(which team is failing, where cost is spiking, who lacks coverage) and leave with "
            "a recommended action + SQL you can audit."
        ),
    ]
    lis = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(
        f'<div class="next-steps"><strong class="label">Next steps</strong><ol>{lis}</ol></div>',
        unsafe_allow_html=True,
    )
    if target and st.button(
        "Execute assignment → Solution",
        type="primary",
        key="execute_next_step",
    ):
        st.session_state["remediation_target"] = target
        # Cannot set main_nav_v3 after the radio widget exists — apply on next run.
        st.session_state["nav_pending"] = "Solution"
        st.rerun()


def _render_solution_page() -> None:
    queue = _action_queue_raw()
    target = st.session_state.get("remediation_target") or normalize_target(
        queue[0] if queue else None
    )

    if not target:
        empty_state(
            "No Critical/High pipeline to remediate",
            "Open Pipeline Health Board after scoring, then execute Next steps.",
        )
        return

    options = {
        f"{_format_cell(r['pipeline_name'])} ({_format_cell(r['owner_team'])})": normalize_target(r)
        for r in queue
    }
    labels = list(options.keys())
    default_label = next(
        (
            lab
            for lab, row in options.items()
            if row and row.get("pipeline_id") == target.get("pipeline_id")
        ),
        labels[0] if labels else None,
    )
    choice = st.selectbox(
        "Pipeline to remediate",
        labels,
        index=labels.index(default_label) if default_label in labels else 0,
        key="remediation_pipeline_choice",
    )
    target = options.get(choice) or target
    st.session_state["remediation_target"] = target

    signal_key = str(target.get("top_signal") or "")
    playbook = playbook_for_signal(signal_key)
    prob = target.get("failure_probability")
    try:
        prob_label = f"{float(prob):.0%}" if prob is not None else "—"
    except (TypeError, ValueError):
        prob_label = "—"

    # Same card chrome as Health Board (label/value type + Critical→Low top bars);
    # content stays assignment fields.
    kpi_strip(
        [
            ("Pipeline", _format_cell(target.get("pipeline_name")), "critical"),
            ("Assigned team", _format_cell(target.get("assigned_team")), "high"),
            ("Top signal", signal_label(signal_key), "medium"),
            ("Failure probability", prob_label, "low"),
        ],
        columns=4,
    )

    st.markdown("**To-do steps**")
    checked: list[str] = []
    for i, step in enumerate(playbook):
        if st.checkbox(step, key=f"rem_step_{target.get('pipeline_id')}_{i}"):
            checked.append(step)

    callout(
        "Assignment brief",
        (
            f"Assign {_format_cell(target.get('assigned_team'))} to remediate "
            f"{_format_cell(target.get('pipeline_name'))}. Primary signal: "
            f"{signal_label(signal_key)}."
        ),
        tone="answer",
    )

    notes = st.text_area(
        "Notes for the owning team",
        value=(
            f"Please remediate {signal_label(signal_key).lower()} on "
            f"{_format_cell(target.get('pipeline_name'))} this cycle."
        ),
        key="remediation_notes",
    )

    if st.button("Create assignment", type="primary", key="create_assignment"):
        if len(checked) < 1:
            st.warning("Check at least one playbook step before assigning.")
        else:
            created = create_remediation_assignment(
                {
                    **target,
                    "notes": notes,
                    "checklist": checked,
                    "status": "assigned",
                }
            )
            st.success(
                f"Assignment {created['assignment_id']} created for "
                f"{_format_cell(created['assigned_team'])} · "
                f"{_format_cell(created['pipeline_name'])}."
            )

    assignments = list_remediation_assignments(limit=25)
    if assignments:
        st.markdown("**Assignment log**")
        log = pd.DataFrame(
            [
                {
                    "Created": a.get("created_at", "")[:19].replace("T", " "),
                    "Pipeline": _format_cell(a.get("pipeline_name")),
                    "Team": _format_cell(a.get("assigned_team")),
                    "Signal": signal_label(str(a.get("top_signal") or "")),
                    "Status": _format_cell(a.get("status")),
                    "Steps checked": len(a.get("checklist") or []),
                }
                for a in assignments
            ]
        )
        st.dataframe(log, use_container_width=True, hide_index=True)
    else:
        st.caption("No assignments yet — create one above to execute Next steps.")


mode = "direct DB" if USE_DIRECT else "API"
# Apply cross-page navigation before the radio widget is created
if "nav_pending" in st.session_state:
    pending = st.session_state.pop("nav_pending")
    if pending == "Remediation":
        pending = "Solution"
    st.session_state["main_nav_v3"] = pending
if st.session_state.get("main_nav_v3") == "Remediation":
    st.session_state["main_nav_v3"] = "Solution"

page_header(
    "Snowflake Reliability Intelligence",
    f"Batch Cortex ML and governed metrics · {mode}",
)

page = st.radio(
    "Navigate",
    PAGES,
    horizontal=True,
    label_visibility="collapsed",
    key="main_nav_v3",
)

st.markdown(f"### {page}")
st.markdown(PAGE_BLURBS[page])

summary = get_dashboard_summary(summary_version=3)

with st.sidebar:
    section_header("Purpose")
    st.markdown(
        "Snowflake Reliability Intelligence turns pipeline telemetry into a governed "
        "risk view for data platform and analytics leaders.\n\n"
        "**What it does**\n\n"
        "- Scores each pipeline’s failure probability from recent runs, freshness, "
        "schema drift, volume anomalies, and warehouse cost signals.\n"
        "- Ranks workloads by business criticality so Critical and High bands surface first.\n"
        "- Lets leaders ask curated reliability questions with transparent SQL — the same "
        "pattern as Cortex Analyst against a semantic model.\n"
        "- Turns Next steps into durable assignments for owning teams via Solution.\n\n"
        "Designed as an offline demo of batch Cortex ML + Analyst-style metrics — auditable, "
        "repeatable, and warehouse-native."
    )

    section_header("Key Findings")
    if summary["pipelines_scored"]:
        critical = summary.get("critical", 0)
        high = summary.get("high", 0)
        medium = summary.get("medium", 0)
        low = summary.get("low", 0)
        bullets = [
            f"<strong>{summary['pipelines_scored']}</strong> pipelines scored in the latest batch run.",
            f"<strong>{critical}</strong> Critical — SLA misses cascade fastest here.",
            f"<strong>{high}</strong> High — prioritize owners on this band next.",
            f"<strong>{medium}</strong> Medium and <strong>{low}</strong> Low stay on the watchlist this cycle.",
        ]
        items = "".join(f"<li>{b}</li>" for b in bullets)
        st.markdown(
            f'<div class="findings-panel"><ul>{items}</ul></div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("No pipeline data loaded", "Run make demo to seed the warehouse.")

if page == "Pipeline Health Board":
    criticality_kpi_strip(
        [
            ("Critical", summary.get("critical", 0), "critical"),
            ("High", summary.get("high", 0), "high"),
            ("Medium", summary.get("medium", 0), "medium"),
            ("Low", summary.get("low", 0), "low"),
        ]
    )

    c1, c2 = st.columns(2)
    with c1:
        focus = st.selectbox(
            "Focus",
            ["Action queue (Critical + High)", "All criticalities"],
            key="health_focus",
        )
    with c2:
        tier = st.selectbox("Risk tier", ["All", "HIGH", "MEDIUM", "LOW"], key="tier_filter")

    raw_rows = get_at_risk(None if tier == "All" else tier, limit=500)
    display_df = _focus_health_board(_prepare_health_board_table(pd.DataFrame(raw_rows)), focus)
    total_rows = len(display_df)
    view_df = display_df.head(HEALTH_BOARD_ROW_CAP) if total_rows else display_df

    action_raw = _action_queue_raw(None if tier == "All" else tier)
    _health_board_next_steps(summary, action_raw[0] if action_raw else None)

    if view_df.empty:
        empty_state("No pipelines match this filter", "Broaden Focus / risk tier or run make demo.")
    else:
        if total_rows > HEALTH_BOARD_ROW_CAP:
            st.caption(
                f"Showing top {HEALTH_BOARD_ROW_CAP} of {total_rows} in this focus "
                "(Critical → High, then by failure %)."
            )
        else:
            st.caption(
                f"{total_rows} pipeline{'s' if total_rows != 1 else ''} in this focus "
                "(Critical → High, then by failure %)."
            )
        st.dataframe(
            style_dataframe(view_df, highlight_critical=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Assessment": st.column_config.TextColumn(
                    "Assessment",
                    width="large",
                    help="Risk · driving signal · owner action",
                ),
                "Pipeline": st.column_config.TextColumn("Pipeline", width="medium"),
                "Owner team": st.column_config.TextColumn("Owner team", width="small"),
                "Domain": st.column_config.TextColumn("Domain", width="small"),
                "Criticality": st.column_config.TextColumn("Criticality", width="small"),
                "Risk tier": st.column_config.TextColumn("Risk tier", width="small"),
                "Failure probability": st.column_config.TextColumn(
                    "Failure probability", width="small"
                ),
                "Top signal": st.column_config.TextColumn("Top signal", width="medium"),
                "Signal value": st.column_config.TextColumn("Signal value", width="small"),
            },
        )

    render_criticality_mix(summary)

elif page == "Solution":
    _render_solution_page()

else:
    from ui.metrics_answers import interpret_metrics_result  # lazy: Metrics Explorer only

    questions = get_analyst_questions()
    labels = {q["question_id"]: q["label"] for q in questions}
    qid = st.selectbox(
        "Question",
        options=sorted(labels.keys()),
        format_func=lambda i: f"{i}. {labels[i]}",
        key="metrics_qid",
    )
    run = st.button("Run analysis", type="primary", key="run_analysis")
    if run:
        st.session_state["metrics_result"] = run_analyst_question(qid)
        st.session_state["metrics_qid_ran"] = qid

    result = st.session_state.get("metrics_result")
    if result and st.session_state.get("metrics_qid_ran") == qid:
        rows = list(result.get("rows") or [])
        interpretation = interpret_metrics_result(
            int(result.get("question_id") or qid),
            str(result.get("question") or labels.get(qid, "")),
            rows,
        )

        callout("Answer", interpretation["answer"], tone="answer")

        if rows:
            display_rows = pd.DataFrame(rows).copy()
            rename_map = {c: c.replace("_", " ").title() for c in display_rows.columns}
            display_rows = display_rows.rename(columns=rename_map)
            for column in display_rows.select_dtypes(include="object").columns:
                display_rows[column] = display_rows[column].apply(_format_cell)
            st.dataframe(
                style_dataframe(display_rows, highlight_failed=True),
                use_container_width=True,
                hide_index=True,
            )
        else:
            empty_state("This question returned no rows", "Try a different question.")

        callout("Likely cause", interpretation["likely_cause"], tone="cause")
        callout("Recommended action", interpretation["recommended_action"], tone="action")

        with st.expander("SQL", expanded=False):
            st.code(result.get("sql", ""), language="sql")
    elif not run:
        st.caption(
            "Select a question and run analysis to see the answer, table evidence, "
            "likely cause, and recommended action."
        )
