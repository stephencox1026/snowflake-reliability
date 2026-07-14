"""Offline ML proxy for Cortex ML Classification (Snowflake SQL in sql/cortex_ml.sql)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.config import Settings
from app.db import connect, fetchall_dicts

FEATURE_COLS = [
    "freshness_delay_avg",
    "sla_breach_count",
    "recent_failures",
    "volume_zscore_max",
    "schema_drift_count",
    "credit_usage_7d",
    "credit_spike_pct",
]
CAT_COLS = ["owner_team", "domain", "criticality"]


def _model_path(settings: Settings) -> Path:
    return settings.reliability_models_dir / "reliability_classifier.joblib"


def _meta_path(settings: Settings) -> Path:
    return settings.reliability_models_dir / "reliability_classifier_meta.json"


def _load_features(settings: Settings) -> pd.DataFrame:
    conn = connect(settings)
    try:
        rows = fetchall_dicts(conn, "SELECT * FROM training_features")
    finally:
        conn.close()
    return pd.DataFrame(rows)


def train_reliability_model(settings: Settings) -> dict[str, float]:
    df = _load_features(settings)
    if df.empty:
        raise RuntimeError("No training features. Run seed first.")

    x = df[FEATURE_COLS + CAT_COLS]
    y = df["failed_next_7d"].astype(int)

    pre = ColumnTransformer(
        [
            ("num", "passthrough", FEATURE_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
        ]
    )
    clf = HistGradientBoostingClassifier(max_depth=6, random_state=42)
    pipe = Pipeline([("pre", pre), ("clf", clf)])

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y if y.nunique() > 1 else None
    )
    pipe.fit(x_train, y_train)
    proba = pipe.predict_proba(x_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else 0.5,
        "train_rows": int(len(df)),
    }

    settings.reliability_models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, _model_path(settings))
    _meta_path(settings).write_text(
        json.dumps(
            {
                "model_type": "offline_hist_gradient_boosting",
                "snowflake_equivalent": "SNOWFLAKE.ML.CLASSIFICATION",
                "feature_cols": FEATURE_COLS,
                "cat_cols": CAT_COLS,
                "trained_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )

    conn = connect(settings)
    try:
        conn.execute("DELETE FROM model_eval_metrics")
        conn.execute(
            """
            INSERT INTO model_eval_metrics
            (run_id, trained_at, precision_score, recall_score, f1_score, roc_auc, train_rows, model_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                datetime.now(timezone.utc).isoformat(),
                metrics["precision"],
                metrics["recall"],
                metrics["f1"],
                metrics["roc_auc"],
                metrics["train_rows"],
                "offline_hist_gradient_boosting",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return metrics


def _risk_tier(prob: float) -> str:
    if prob >= 0.82:
        return "HIGH"
    if prob >= 0.55:
        return "MEDIUM"
    return "LOW"


def _top_feature(row: pd.Series) -> tuple[str, float]:
    candidates = {
        "freshness_delay_avg": float(row["freshness_delay_avg"]),
        "sla_breach_count": float(row["sla_breach_count"]),
        "recent_failures": float(row["recent_failures"]),
        "volume_zscore_max": float(row["volume_zscore_max"]),
        "schema_drift_count": float(row["schema_drift_count"]),
        "credit_spike_pct": float(row["credit_spike_pct"]),
    }
    name = max(candidates, key=candidates.get)
    return name, candidates[name]


def score_pipelines(settings: Settings) -> int:
    model_file = _model_path(settings)
    if not model_file.exists():
        train_reliability_model(settings)
    pipe = joblib.load(model_file)
    df = _load_features(settings)
    x = df[FEATURE_COLS + CAT_COLS]
    proba = pipe.predict_proba(x)[:, 1]

    scored_at = datetime.now(timezone.utc).isoformat()
    conn = connect(settings)
    try:
        conn.execute("DELETE FROM pipeline_risk_scores")
        for i, row in df.iterrows():
            p = float(proba[i])
            feat, val = _top_feature(row)
            conn.execute(
                """
                INSERT INTO pipeline_risk_scores
                (pipeline_id, scored_at, failure_probability, risk_tier, top_feature, top_feature_value)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (row["pipeline_id"], scored_at, round(p, 4), _risk_tier(p), feat, round(val, 2)),
            )
        conn.commit()
    finally:
        conn.close()
    return len(df)
