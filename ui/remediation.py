"""Signal-specific remediation playbooks for the Remediation tab."""

from __future__ import annotations

from typing import Any

SIGNAL_PLAYBOOKS: dict[str, list[str]] = {
    "freshness_delay_avg": [
        "Confirm upstream source landed within SLA window",
        "Check warehouse / task lag for the owning schedule",
        "Validate freshness contract with source owners",
        "Re-run pipeline and confirm delay minutes drop",
    ],
    "sla_breach_count": [
        "Review SLA breach timestamps for this cycle",
        "Identify whether breach is source, transform, or warehouse",
        "Open incident with owning team and set recovery ETA",
        "Confirm next successful land meets SLA",
    ],
    "recent_failures": [
        "Pull last failed run error message / query ID",
        "Rollback or fix the change that introduced the failure",
        "Re-run with monitoring on the failing step",
        "Confirm two consecutive successful runs",
    ],
    "volume_zscore_max": [
        "Compare actual vs expected row volume for the spike/drop day",
        "Validate source extract completeness",
        "Check for duplicate or missing partitions",
        "Re-score after volume stabilizes",
    ],
    "schema_drift_count": [
        "Diff current vs contracted schema",
        "Update consumer mappings / dbt models",
        "Freeze downstream writes until contract is validated",
        "Re-run and confirm drift event clears",
    ],
    "credit_spike_pct": [
        "Inspect warehouse size and query plan changes",
        "Identify top credit-consuming statements",
        "Apply warehouse / clustering / query fix",
        "Confirm week-over-week credits trend down",
    ],
}

DEFAULT_PLAYBOOK = [
    "Review top failure signal with the owning team",
    "Capture root cause and recovery ETA",
    "Apply remediation and re-run the pipeline",
    "Confirm risk score improves on next batch",
]


def playbook_for_signal(signal_key: str) -> list[str]:
    key = str(signal_key or "").strip()
    return list(SIGNAL_PLAYBOOKS.get(key, DEFAULT_PLAYBOOK))


def signal_label(signal_key: str) -> str:
    labels = {
        "freshness_delay_avg": "Freshness delay",
        "sla_breach_count": "SLA breaches",
        "recent_failures": "Recent failures",
        "volume_zscore_max": "Volume anomaly",
        "schema_drift_count": "Schema drift",
        "credit_spike_pct": "Credit spike",
    }
    key = str(signal_key or "").strip()
    return labels.get(key, key.replace("_", " ").title() or "Unknown signal")


def normalize_target(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "pipeline_id": str(row.get("pipeline_id") or ""),
        "pipeline_name": str(row.get("pipeline_name") or row.get("Pipeline") or ""),
        "assigned_team": str(row.get("owner_team") or row.get("Owner team") or ""),
        "top_signal": str(row.get("top_feature") or row.get("Top signal") or ""),
        "signal_value": row.get("top_feature_value", row.get("Signal value")),
        "failure_probability": row.get("failure_probability"),
        "risk_tier": str(row.get("risk_tier") or row.get("Risk tier") or ""),
        "criticality": str(row.get("criticality") or row.get("Criticality") or ""),
    }
