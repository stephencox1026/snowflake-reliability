"""SQLite warehouse access and schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config import Settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pipelines (
    pipeline_id TEXT PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    owner_team TEXT NOT NULL,
    criticality TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    run_date TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_minutes REAL NOT NULL,
    rows_processed INTEGER NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);

CREATE TABLE IF NOT EXISTS freshness_checks (
    check_id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    check_date TEXT NOT NULL,
    expected_by TEXT NOT NULL,
    actual_landed_at TEXT NOT NULL,
    delay_minutes INTEGER NOT NULL,
    sla_breached INTEGER NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);

CREATE TABLE IF NOT EXISTS schema_drift_events (
    event_id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    change_type TEXT NOT NULL,
    column_name TEXT,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);

CREATE TABLE IF NOT EXISTS volume_anomalies (
    anomaly_id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    check_date TEXT NOT NULL,
    expected_rows INTEGER NOT NULL,
    actual_rows INTEGER NOT NULL,
    z_score REAL NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);

CREATE TABLE IF NOT EXISTS warehouse_cost_daily (
    cost_id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    cost_date TEXT NOT NULL,
    credits_used REAL NOT NULL,
    query_count INTEGER NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);

CREATE TABLE IF NOT EXISTS training_features (
    pipeline_id TEXT PRIMARY KEY,
    owner_team TEXT NOT NULL,
    domain TEXT NOT NULL,
    criticality TEXT NOT NULL,
    freshness_delay_avg REAL NOT NULL,
    sla_breach_count INTEGER NOT NULL,
    recent_failures INTEGER NOT NULL,
    volume_zscore_max REAL NOT NULL,
    schema_drift_count INTEGER NOT NULL,
    credit_usage_7d REAL NOT NULL,
    credit_spike_pct REAL NOT NULL,
    failed_next_7d INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_risk_scores (
    pipeline_id TEXT PRIMARY KEY,
    scored_at TEXT NOT NULL,
    failure_probability REAL NOT NULL,
    risk_tier TEXT NOT NULL,
    top_feature TEXT NOT NULL,
    top_feature_value REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS rca_narratives (
    pipeline_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    likely_cause TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    owner_team TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_eval_metrics (
    run_id TEXT PRIMARY KEY,
    trained_at TEXT NOT NULL,
    precision_score REAL NOT NULL,
    recall_score REAL NOT NULL,
    f1_score REAL NOT NULL,
    roc_auc REAL NOT NULL,
    train_rows INTEGER NOT NULL,
    model_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS remediation_assignments (
    assignment_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    pipeline_id TEXT NOT NULL,
    pipeline_name TEXT NOT NULL,
    assigned_team TEXT NOT NULL,
    top_signal TEXT NOT NULL,
    signal_value REAL,
    failure_probability REAL,
    risk_tier TEXT,
    criticality TEXT,
    status TEXT NOT NULL,
    notes TEXT NOT NULL,
    checklist_json TEXT NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
);
"""


def _sqlite_path(url: str) -> Path:
    if not url.startswith("sqlite:///"):
        raise ValueError("Offline demo supports sqlite only. Set RELIABILITY_DATABASE_URL.")
    return Path(url.replace("sqlite:///", ""))


def connect(settings: Settings) -> sqlite3.Connection:
    path = _sqlite_path(settings.reliability_database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(settings: Settings) -> None:
    conn = connect(settings)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def warehouse_ready(settings: Settings) -> bool:
    """True when the warehouse has pipeline rows; False if missing/uninitialized."""
    try:
        conn = connect(settings)
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM pipelines").fetchone()
            return bool(row and int(row["n"]) > 0)
        finally:
            conn.close()
    except (sqlite3.Error, OSError, ValueError):
        return False


def fetchall_dicts(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def execute_many(conn: sqlite3.Connection, sql: str, rows: list[tuple[Any, ...]]) -> None:
    conn.executemany(sql, rows)
    conn.commit()
