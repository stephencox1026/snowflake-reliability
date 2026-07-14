"""Orchestrate train → score → explain batch pipeline."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.ml import score_pipelines, train_reliability_model
from app.rca import generate_rca_narratives


def run_batch_pipeline(settings: Settings) -> dict[str, Any]:
    metrics = train_reliability_model(settings)
    scored = score_pipelines(settings)
    narratives = generate_rca_narratives(settings)
    return {
        "model_metrics": metrics,
        "pipelines_scored": scored,
        "rca_narratives_generated": narratives,
    }
