"""Tests for Snowflake Reliability Intelligence."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.db import warehouse_ready
from app.pipeline import run_batch_pipeline
from app.warehouse import seed_warehouse


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("RELIABILITY_DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("RELIABILITY_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RELIABILITY_MODELS_DIR", str(tmp_path / "models"))
    get_settings.cache_clear()
    s = get_settings()
    s.ensure_dirs()
    return s


def test_seed_and_pipeline(settings):
    counts = seed_warehouse(settings, pipeline_count=40)
    assert counts["pipelines"] == 40
    assert warehouse_ready(settings)
    out = run_batch_pipeline(settings)
    assert out["pipelines_scored"] == 40
    assert out["model_metrics"]["f1"] >= 0


def test_analyst_questions(settings):
    seed_warehouse(settings, pipeline_count=30)
    run_batch_pipeline(settings)
    from app.analyst import run_question

    for qid in range(1, 11):
        result = run_question(settings, qid)
        assert result["question_id"] == qid
        assert result["sql"]
        assert "rows" in result
