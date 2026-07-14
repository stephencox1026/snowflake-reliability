"""Batch RCA narrative generation (offline proxy for AI_COMPLETE)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.config import Settings
from app.db import connect, fetchall_dicts

FEATURE_LABELS = {
    "freshness_delay_avg": "average freshness delay",
    "sla_breach_count": "SLA breaches",
    "recent_failures": "recent run failures",
    "volume_zscore_max": "volume anomaly severity",
    "schema_drift_count": "schema drift events",
    "credit_spike_pct": "warehouse credit spike",
}


def _narrative(row: dict) -> dict[str, str]:
    feat = row.get("top_feature", "recent_failures")
    label = FEATURE_LABELS.get(feat, feat)
    val = row.get("top_feature_value", 0)
    prob = float(row.get("failure_probability", 0))
    team = row.get("owner_team", "data_platform")
    name = row.get("pipeline_name", row["pipeline_id"])

    summary = (
        f"Pipeline {name} has {prob:.0%} predicted failure risk. "
        f"Primary signal: {label} ({val})."
    )
    cause = (
        f"Elevated {label} suggests upstream latency or data contract instability. "
        f"Historical runs and freshness checks for this pipeline are trending worse than peer baselines."
    )
    action = (
        f"Assign {team} to inspect recent task runs, validate freshness SLAs, "
        f"and review schema contracts. Consider pausing downstream consumers until backlog clears."
    )
    return {
        "summary": summary,
        "likely_cause": cause,
        "recommended_action": action,
        "owner_team": team,
    }


def generate_rca_narratives(settings: Settings, min_tier: str = "HIGH") -> int:
    tiers = {"HIGH": {"HIGH"}, "MEDIUM": {"HIGH", "MEDIUM"}}
    allowed = tiers.get(min_tier, {"HIGH"})

    conn = connect(settings)
    try:
        rows = fetchall_dicts(
            conn,
            """
            SELECT s.pipeline_id, s.failure_probability, s.risk_tier, s.top_feature,
                   s.top_feature_value, p.pipeline_name, p.owner_team
            FROM pipeline_risk_scores s
            JOIN pipelines p ON p.pipeline_id = s.pipeline_id
            WHERE s.risk_tier IN ({})
            """.format(",".join("?" for _ in allowed)),
            tuple(allowed),
        )
        conn.execute("DELETE FROM rca_narratives")
        generated_at = datetime.now(timezone.utc).isoformat()
        for row in rows:
            n = _narrative(row)
            conn.execute(
                """
                INSERT INTO rca_narratives
                (pipeline_id, generated_at, summary, likely_cause, recommended_action, owner_team)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["pipeline_id"],
                    generated_at,
                    n["summary"],
                    n["likely_cause"],
                    n["recommended_action"],
                    n["owner_team"],
                ),
            )
        conn.commit()
        return len(rows)
    finally:
        conn.close()
