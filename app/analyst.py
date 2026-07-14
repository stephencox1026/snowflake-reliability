"""Cortex Analyst Metrics Explorer — 10 dropdown questions with SQL templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db import connect, fetchall_dicts

QUESTIONS: dict[int, dict[str, str]] = {
    1: {
        "label": "Which pipelines are high risk right now?",
        "description": "Pipelines with HIGH risk tier ordered by failure probability.",
    },
    2: {
        "label": "Which teams have the most freshness SLA breaches this month?",
        "description": "Count of SLA breaches grouped by owning team in the last 30 days.",
    },
    3: {
        "label": "What are the top 10 pipelines by warehouse credit usage?",
        "description": "Sum of credits over the last 7 days per pipeline.",
    },
    4: {
        "label": "How many pipelines failed in the last 7 days?",
        "description": "Distinct pipelines with at least one failed run.",
    },
    5: {
        "label": "Which critical pipelines have no RCA narrative generated?",
        "description": "Critical pipelines at HIGH risk without an RCA record.",
    },
    6: {
        "label": "What is the average volume anomaly z-score by data domain?",
        "description": "Mean z-score from volume anomaly checks grouped by domain.",
    },
    7: {
        "label": "Which pipelines had schema drift events in the last 30 days?",
        "description": "Pipelines with one or more schema drift events.",
    },
    8: {
        "label": "What is the failure rate by owning team?",
        "description": "Failed runs divided by total runs per team.",
    },
    9: {
        "label": "Which pipelines have rising cost spikes week over week?",
        "description": "Pipelines where second-half 7d credits exceed first half by 25%+.",
    },
    10: {
        "label": "How many pipelines moved from low to high risk in the last 7 days?",
        "description": "Proxy: MEDIUM/HIGH risk with recent_failures >= 2.",
    },
}

SQL_TEMPLATES: dict[int, str] = {
    1: """
        SELECT p.pipeline_name, p.owner_team, s.failure_probability, s.risk_tier
        FROM pipeline_risk_scores s
        JOIN pipelines p ON p.pipeline_id = s.pipeline_id
        WHERE s.risk_tier = 'HIGH'
        ORDER BY s.failure_probability DESC
        LIMIT 25
    """,
    2: """
        SELECT p.owner_team, SUM(f.sla_breached) AS breach_count
        FROM freshness_checks f
        JOIN pipelines p ON p.pipeline_id = f.pipeline_id
        WHERE f.check_date >= date('now', '-30 days')
        GROUP BY p.owner_team
        ORDER BY breach_count DESC
    """,
    3: """
        SELECT p.pipeline_name, SUM(c.credits_used) AS credits_7d
        FROM warehouse_cost_daily c
        JOIN pipelines p ON p.pipeline_id = c.pipeline_id
        WHERE c.cost_date >= date('now', '-7 days')
        GROUP BY p.pipeline_name
        ORDER BY credits_7d DESC
        LIMIT 10
    """,
    4: """
        SELECT COUNT(DISTINCT pipeline_id) AS failed_pipeline_count
        FROM pipeline_runs
        WHERE status = 'failed' AND run_date >= date('now', '-7 days')
    """,
    5: """
        SELECT p.pipeline_name, s.failure_probability
        FROM pipelines p
        JOIN pipeline_risk_scores s ON s.pipeline_id = p.pipeline_id
        LEFT JOIN rca_narratives r ON r.pipeline_id = p.pipeline_id
        WHERE p.criticality = 'critical' AND s.risk_tier = 'HIGH' AND r.pipeline_id IS NULL
    """,
    6: """
        SELECT p.domain, ROUND(AVG(v.z_score), 2) AS avg_z_score
        FROM volume_anomalies v
        JOIN pipelines p ON p.pipeline_id = v.pipeline_id
        GROUP BY p.domain
        ORDER BY avg_z_score DESC
    """,
    7: """
        SELECT p.pipeline_name, COUNT(*) AS drift_events
        FROM schema_drift_events d
        JOIN pipelines p ON p.pipeline_id = d.pipeline_id
        WHERE d.detected_at >= date('now', '-30 days')
        GROUP BY p.pipeline_name
        ORDER BY drift_events DESC
    """,
    8: """
        SELECT p.owner_team,
               ROUND(100.0 * SUM(CASE WHEN r.status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
        FROM pipeline_runs r
        JOIN pipelines p ON p.pipeline_id = r.pipeline_id
        GROUP BY p.owner_team
        ORDER BY failure_rate_pct DESC
    """,
    9: """
        SELECT p.pipeline_name, t.credit_spike_pct
        FROM training_features t
        JOIN pipelines p ON p.pipeline_id = t.pipeline_id
        WHERE t.credit_spike_pct >= 25
        ORDER BY t.credit_spike_pct DESC
        LIMIT 20
    """,
    10: """
        SELECT COUNT(*) AS escalated_pipeline_count
        FROM training_features t
        JOIN pipeline_risk_scores s ON s.pipeline_id = t.pipeline_id
        WHERE s.risk_tier IN ('HIGH', 'MEDIUM') AND t.recent_failures >= 2
    """,
}


def list_questions() -> list[dict[str, Any]]:
    return [
        {"question_id": qid, **meta, "sql_template": SQL_TEMPLATES[qid].strip()}
        for qid, meta in sorted(QUESTIONS.items())
    ]


def run_question(settings: Settings, question_id: int) -> dict[str, Any]:
    if question_id not in SQL_TEMPLATES:
        raise ValueError(f"Unknown question_id: {question_id}")

    sql = SQL_TEMPLATES[question_id].strip()
    conn = connect(settings)
    try:
        rows = fetchall_dicts(conn, sql)
    finally:
        conn.close()

    return {
        "question_id": question_id,
        "question": QUESTIONS[question_id]["label"],
        "description": QUESTIONS[question_id]["description"],
        "sql": sql,
        "rows": rows,
        "row_count": len(rows),
        "source": "offline_sql_template",
        "cortex_analyst_note": (
            "In Snowflake, the same question is sent to the Cortex Analyst REST API "
            "with semantic_models/pipeline_health.yaml."
        ),
    }


def build_analyst_cache(settings: Settings) -> Path:
    cache = {str(qid): run_question(settings, qid) for qid in QUESTIONS}
    out = settings.reliability_data_dir / "analyst_cache.json"
    out.write_text(json.dumps(cache, indent=2))
    return out
