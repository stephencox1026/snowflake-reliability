"""FastAPI read endpoints for Snowflake Reliability Intelligence."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.analyst import list_questions, run_question
from app.config import get_settings
from app.db import connect, fetchall_dicts, init_schema, warehouse_ready

app = FastAPI(
    title="Snowflake Reliability Intelligence",
    description="Batch Cortex ML + LLM pipeline health for data platforms",
    version="0.1.0",
)


class AnalystRequest(BaseModel):
    question_id: int = Field(..., ge=1, le=10)


@app.on_event("startup")
def _startup() -> None:
    settings = get_settings()
    init_schema(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    settings = get_settings()
    return {
        "warehouse_ready": warehouse_ready(settings),
        "offline_mode": settings.reliability_offline_mode,
    }


@app.post("/pipeline/run")
def pipeline_run() -> dict[str, Any]:
    from app.pipeline import run_batch_pipeline

    settings = get_settings()
    if not warehouse_ready(settings):
        raise HTTPException(503, "Warehouse empty. Run make demo first.")
    return run_batch_pipeline(settings)


@app.get("/pipelines/at-risk")
def pipelines_at_risk(tier: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    settings = get_settings()
    conn = connect(settings)
    try:
        sql = """
            SELECT p.pipeline_id, p.pipeline_name, p.domain, p.owner_team, p.criticality,
                   s.failure_probability, s.risk_tier, s.top_feature, s.top_feature_value, s.scored_at
            FROM pipeline_risk_scores s
            JOIN pipelines p ON p.pipeline_id = s.pipeline_id
        """
        params: list[Any] = []
        if tier:
            sql += " WHERE s.risk_tier = ?"
            params.append(tier.upper())
        sql += " ORDER BY s.failure_probability DESC LIMIT ?"
        params.append(limit)
        return fetchall_dicts(conn, sql, tuple(params))
    finally:
        conn.close()


@app.get("/pipelines/{pipeline_id}/brief")
def pipeline_brief(pipeline_id: str) -> dict[str, Any]:
    settings = get_settings()
    conn = connect(settings)
    try:
        meta = fetchall_dicts(
            conn,
            """
            SELECT p.*, s.failure_probability, s.risk_tier, s.top_feature, s.top_feature_value
            FROM pipelines p
            LEFT JOIN pipeline_risk_scores s ON s.pipeline_id = p.pipeline_id
            WHERE p.pipeline_id = ?
            """,
            (pipeline_id,),
        )
        if not meta:
            raise HTTPException(404, "Pipeline not found")
        rca = fetchall_dicts(
            conn, "SELECT * FROM rca_narratives WHERE pipeline_id = ?", (pipeline_id,)
        )
        features = fetchall_dicts(
            conn, "SELECT * FROM training_features WHERE pipeline_id = ?", (pipeline_id,)
        )
        recent_runs = fetchall_dicts(
            conn,
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
    finally:
        conn.close()


@app.get("/model/metrics")
def model_metrics() -> list[dict[str, Any]]:
    settings = get_settings()
    conn = connect(settings)
    try:
        return fetchall_dicts(
            conn,
            "SELECT * FROM model_eval_metrics ORDER BY trained_at DESC LIMIT 5",
        )
    finally:
        conn.close()


@app.get("/analyst/questions")
def analyst_questions() -> list[dict[str, Any]]:
    return list_questions()


@app.post("/analyst/ask")
def analyst_ask(body: AnalystRequest) -> dict[str, Any]:
    settings = get_settings()
    if not warehouse_ready(settings):
        raise HTTPException(503, "Warehouse empty. Run make demo first.")
    try:
        return run_question(settings, body.question_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
