"""Pipeline Health Board assessment copy — short enough to read in-table."""

from __future__ import annotations

import pandas as pd

SIGNAL_LABELS = {
    "freshness_delay_avg": "freshness delay",
    "sla_breach_count": "SLA breaches",
    "recent_failures": "recent failures",
    "volume_zscore_max": "volume anomaly",
    "schema_drift_count": "schema drift",
    "credit_spike_pct": "credit spike",
}


def build_assessment(row: pd.Series | dict) -> str:
    """One compact line: risk · signal · owner action."""
    get = row.get if hasattr(row, "get") else lambda k, d=None: row[k] if k in row else d  # type: ignore[index]

    tier = str(get("risk_tier") or "LOW").upper()
    try:
        prob = float(get("failure_probability") or 0)
    except (TypeError, ValueError):
        prob = 0.0

    signal_key = str(get("top_feature") or "recent_failures")
    signal = SIGNAL_LABELS.get(signal_key, signal_key.replace("_", " "))
    try:
        signal_value = float(get("top_feature_value") or 0)
        signal_value_text = f"{signal_value:.0f}" if signal_value >= 10 else f"{signal_value:g}"
    except (TypeError, ValueError):
        signal_value_text = "n/a"

    team = str(get("owner_team") or "owner").replace("_", " ")
    if tier == "HIGH":
        action = f"Assign {team}"
    elif tier == "MEDIUM":
        action = f"Watch {team}"
    else:
        action = "Monitor"

    return f"{prob:.0%} · {signal} ({signal_value_text}) · {action}"


def build_rca_situation(pipeline: dict, rca: dict | None = None) -> str:
    """Executive situation: what is happening and why it matters (1–2 sentences)."""
    name = str(pipeline.get("pipeline_name") or pipeline.get("pipeline_id") or "This pipeline")
    tier = str(pipeline.get("risk_tier") or "UNKNOWN").upper()
    criticality = str(pipeline.get("criticality") or "medium").lower()
    team = str(pipeline.get("owner_team") or "the owning team").replace("_", " ")
    signal_key = str(pipeline.get("top_feature") or "recent_failures")
    signal = SIGNAL_LABELS.get(signal_key, signal_key.replace("_", " "))
    try:
        prob = float(pipeline.get("failure_probability") or 0)
    except (TypeError, ValueError):
        prob = 0.0
    try:
        signal_value = float(pipeline.get("top_feature_value") or 0)
        signal_value_text = f"{signal_value:.0f}" if signal_value >= 10 else f"{signal_value:g}"
    except (TypeError, ValueError):
        signal_value_text = "n/a"

    if criticality == "critical":
        stakes = (
            f"It is a business-critical feed owned by {team}, so downtime cascades into "
            f"downstream SLAs and executive-visible outages."
        )
    else:
        stakes = (
            f"Owned by {team}, it is currently above the reliability threshold that warrants "
            f"owner attention this cycle."
        )

    return (
        f"{name} is at {prob:.0%} predicted failure risk ({tier.title()}), "
        f"driven by {signal} at {signal_value_text}. {stakes}"
    )
