"""Data access for Streamlit — thread-safe SQLite reads with optional API fallback."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analyst import list_questions, run_question  # noqa: E402
from app.config import get_settings  # noqa: E402

API_BASE = os.environ.get("RELIABILITY_API_URL", "http://127.0.0.1:8002")
USE_DIRECT = os.environ.get("RELIABILITY_UI_DIRECT", "true").lower() in {"1", "true", "yes"}

_thread_local = threading.local()


def _db_path() -> Path:
    url = get_settings().reliability_database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("UI direct mode requires sqlite:/// database URL")
    return Path(url.replace("sqlite:///", ""))


def _query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Thread-local SQLite connection — safe for Streamlit reruns."""
    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(_db_path(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _thread_local.conn = conn
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _api_get(path: str, **params: Any) -> Any | None:
    import requests

    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _api_post(path: str, body: dict | None = None) -> Any | None:
    import requests

    try:
        r = requests.post(f"{API_BASE}{path}", json=body or {}, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def get_at_risk(tier: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if not USE_DIRECT:
        data = _api_get("/pipelines/at-risk", tier=tier, limit=limit)
        if data is not None:
            return data

    sql = """
        SELECT p.pipeline_id, p.pipeline_name, p.domain, p.owner_team, p.criticality,
               s.failure_probability, s.risk_tier, s.top_feature, s.top_feature_value, s.scored_at
        FROM pipeline_risk_scores s
        JOIN pipelines p ON p.pipeline_id = s.pipeline_id
    """
    params: list[Any] = []
    if tier and tier != "All":
        sql += " WHERE s.risk_tier = ?"
        params.append(tier.upper())
    sql += " ORDER BY s.failure_probability DESC LIMIT ?"
    params.append(limit)
    return _query(sql, tuple(params))


@st.cache_data(ttl=30, show_spinner=False)
def get_brief(pipeline_id: str) -> dict[str, Any] | None:
    if not USE_DIRECT:
        data = _api_get(f"/pipelines/{pipeline_id}/brief")
        if data is not None:
            return data

    meta = _query(
        """
        SELECT p.*, s.failure_probability, s.risk_tier, s.top_feature, s.top_feature_value
        FROM pipelines p
        LEFT JOIN pipeline_risk_scores s ON p.pipeline_id = s.pipeline_id
        WHERE p.pipeline_id = ?
        """,
        (pipeline_id,),
    )
    if not meta:
        return None
    rca = _query("SELECT * FROM rca_narratives WHERE pipeline_id = ?", (pipeline_id,))
    features = _query("SELECT * FROM training_features WHERE pipeline_id = ?", (pipeline_id,))
    recent_runs = _query(
        """
        SELECT run_date, status, duration_minutes, rows_processed
        FROM pipeline_runs WHERE pipeline_id = ?
        ORDER BY run_date DESC LIMIT 14
        """,
        (pipeline_id,),
    )
    return {
        "pipeline": meta[0],
        "rca": rca[0] if rca else None,
        "features": features[0] if features else None,
        "recent_runs": recent_runs,
    }


@st.cache_data(ttl=30, show_spinner=False)
def get_model_metrics() -> list[dict[str, Any]]:
    if not USE_DIRECT:
        data = _api_get("/model/metrics")
        if data is not None:
            return data
    return _query("SELECT * FROM model_eval_metrics ORDER BY trained_at DESC LIMIT 5")


def get_analyst_questions() -> list[dict[str, Any]]:
    return list_questions()


def run_analyst_question(question_id: int) -> dict[str, Any]:
    settings = get_settings()
    cache_path = settings.reliability_data_dir / "analyst_cache.json"
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())
        if str(question_id) in cache:
            return cache[str(question_id)]
    return run_question(settings, question_id)


@st.cache_data(ttl=30, show_spinner=False)
def get_dashboard_summary(summary_version: int = 2) -> dict[str, Any]:
    pipelines = get_at_risk(limit=500)
    tiers = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    criticalities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for row in pipelines:
        tier = row.get("risk_tier")
        if tier in tiers:
            tiers[tier] += 1
        criticality = str(row.get("criticality", "")).lower()
        if criticality in criticalities:
            criticalities[criticality] += 1
    metrics = get_model_metrics()
    latest = metrics[0] if metrics else {}
    return {
        "pipelines_scored": len(pipelines),
        "high_risk": tiers["HIGH"],
        "medium_risk": tiers["MEDIUM"],
        "low_risk": tiers["LOW"],
        "critical": criticalities["critical"],
        "high": criticalities["high"],
        "medium": criticalities["medium"],
        "low": criticalities["low"],
        "f1_score": latest.get("f1_score"),
        "roc_auc": latest.get("roc_auc"),
    }


def _clear_data_caches() -> None:
    get_at_risk.clear()
    get_brief.clear()
    get_model_metrics.clear()
    get_dashboard_summary.clear()
    list_remediation_assignments.clear()


def _ensure_remediation_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
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
            checklist_json TEXT NOT NULL
        )
        """
    )
    conn.commit()


def create_remediation_assignment(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a Next Steps assignment (owner + pipeline + signal checklist)."""
    import uuid
    from datetime import datetime, timezone

    assignment_id = f"asg_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now(timezone.utc).isoformat()
    checklist = payload.get("checklist") or []
    row = {
        "assignment_id": assignment_id,
        "created_at": created_at,
        "pipeline_id": str(payload.get("pipeline_id") or ""),
        "pipeline_name": str(payload.get("pipeline_name") or ""),
        "assigned_team": str(payload.get("assigned_team") or ""),
        "top_signal": str(payload.get("top_signal") or ""),
        "signal_value": float(payload.get("signal_value") or 0),
        "failure_probability": float(payload.get("failure_probability") or 0),
        "risk_tier": str(payload.get("risk_tier") or ""),
        "criticality": str(payload.get("criticality") or ""),
        "status": str(payload.get("status") or "assigned"),
        "notes": str(payload.get("notes") or ""),
        "checklist_json": json.dumps(checklist),
    }

    if not USE_DIRECT:
        data = _api_post("/remediations", row)
        if data is not None:
            list_remediation_assignments.clear()
            return data

    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(_db_path(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _thread_local.conn = conn
    _ensure_remediation_table(conn)
    conn.execute(
        """
        INSERT INTO remediation_assignments (
            assignment_id, created_at, pipeline_id, pipeline_name, assigned_team,
            top_signal, signal_value, failure_probability, risk_tier, criticality,
            status, notes, checklist_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["assignment_id"],
            row["created_at"],
            row["pipeline_id"],
            row["pipeline_name"],
            row["assigned_team"],
            row["top_signal"],
            row["signal_value"],
            row["failure_probability"],
            row["risk_tier"],
            row["criticality"],
            row["status"],
            row["notes"],
            row["checklist_json"],
        ),
    )
    conn.commit()
    list_remediation_assignments.clear()
    return row


@st.cache_data(ttl=15, show_spinner=False)
def list_remediation_assignments(limit: int = 50) -> list[dict[str, Any]]:
    if not USE_DIRECT:
        data = _api_get("/remediations", limit=limit)
        if data is not None:
            return data

    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(_db_path(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _thread_local.conn = conn
    _ensure_remediation_table(conn)
    rows = conn.execute(
        """
        SELECT * FROM remediation_assignments
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        try:
            item["checklist"] = json.loads(item.get("checklist_json") or "[]")
        except json.JSONDecodeError:
            item["checklist"] = []
        out.append(item)
    return out


def run_pipeline() -> dict[str, Any] | None:
    if not USE_DIRECT:
        return _api_post("/pipeline/run")
    from app.pipeline import run_batch_pipeline

    out = run_batch_pipeline(get_settings())
    _clear_data_caches()
    return out


def risk_tier_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "risk_tier" not in df.columns:
        return pd.DataFrame()
    counts = df["risk_tier"].value_counts().reset_index(name="count")
    counts.columns = ["risk_tier", "count"]
    return counts
