"""Seed warehouse tables from synthetic generator."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.db import connect, init_schema
from app.synthetic import (
    derive_training_labels,
    generate_operational_data,
    generate_pipelines,
)


def _clear(conn) -> None:
    for table in (
        "rca_narratives",
        "pipeline_risk_scores",
        "model_eval_metrics",
        "training_features",
        "warehouse_cost_daily",
        "volume_anomalies",
        "schema_drift_events",
        "freshness_checks",
        "pipeline_runs",
        "pipelines",
    ):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def _insert_rows(conn, table: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    col_sql = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
    conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
    conn.commit()
    return len(rows)


def seed_warehouse(settings: Settings, pipeline_count: int = 17) -> dict[str, int]:
    init_schema(settings)
    conn = connect(settings)
    try:
        _clear(conn)
        pipelines = generate_pipelines(pipeline_count)
        ops = generate_operational_data(pipelines)
        features = derive_training_labels(pipelines, ops, ops["profiles"])

        counts = {
            "pipelines": _insert_rows(conn, "pipelines", pipelines),
            "pipeline_runs": _insert_rows(conn, "pipeline_runs", ops["pipeline_runs"]),
            "freshness_checks": _insert_rows(conn, "freshness_checks", ops["freshness_checks"]),
            "schema_drift_events": _insert_rows(conn, "schema_drift_events", ops["schema_drift_events"]),
            "volume_anomalies": _insert_rows(conn, "volume_anomalies", ops["volume_anomalies"]),
            "warehouse_cost_daily": _insert_rows(conn, "warehouse_cost_daily", ops["warehouse_cost_daily"]),
            "training_features": _insert_rows(conn, "training_features", features),
        }
        return counts
    finally:
        conn.close()
