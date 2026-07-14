"""Synthetic Snowflake-style pipeline metadata generator."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any

DOMAINS = ["finance", "product", "customer_success", "marketing", "platform"]
TEAMS = ["data_platform", "analytics_eng", "revops", "product_analytics", "finops"]
CRITICALITIES = ["critical", "high", "medium", "low"]
PIPELINE_PREFIXES = [
    "fct_revenue",
    "dim_customer",
    "agg_usage",
    "stg_events",
    "mart_churn",
    "raw_logs",
    "dbt_marts",
    "snowpipe_ingest",
]


def _pid() -> str:
    return f"pipe_{uuid.uuid4().hex[:8]}"


def _rid() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


def generate_pipelines(n: int = 17, seed: int = 42) -> list[dict[str, Any]]:
    """Build a compact demo portfolio: 2 critical, 3 high, 2 medium, rest low."""
    rng = random.Random(seed)
    quotas = {"critical": 2, "high": 3, "medium": 2}
    reserved = sum(quotas.values())
    if n < reserved:
        raise ValueError(f"Need at least {reserved} pipelines; got n={n}")
    # Cap low so Key Findings stay focused (default n=17 → 10 low)
    low_count = n - reserved
    bands: list[str] = (
        ["critical"] * quotas["critical"]
        + ["high"] * quotas["high"]
        + ["medium"] * quotas["medium"]
        + ["low"] * low_count
    )
    rng.shuffle(bands)

    pipelines: list[dict[str, Any]] = []
    for i, criticality in enumerate(bands):
        prefix = rng.choice(PIPELINE_PREFIXES)
        pipelines.append(
            {
                "pipeline_id": _pid(),
                "pipeline_name": f"{prefix}_{i:03d}",
                "domain": rng.choice(DOMAINS),
                "owner_team": rng.choice(TEAMS),
                "criticality": criticality,
            }
        )
    return pipelines


def _risk_profile(rng: random.Random) -> str:
    return rng.choices(["healthy", "degraded", "failing"], weights=[0.82, 0.13, 0.05])[0]


def generate_operational_data(
    pipelines: list[dict[str, Any]],
    days: int = 45,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    today = date.today()
    profiles = {p["pipeline_id"]: _risk_profile(rng) for p in pipelines}

    runs: list[dict[str, Any]] = []
    freshness: list[dict[str, Any]] = []
    drift: list[dict[str, Any]] = []
    volumes: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []

    for p in pipelines:
        pid = p["pipeline_id"]
        profile = profiles[pid]
        base_credits = rng.uniform(2, 40)

        for d in range(days):
            day = today - timedelta(days=days - d)
            day_str = day.isoformat()

            fail_prob = {"healthy": 0.02, "degraded": 0.12, "failing": 0.35}[profile]
            status = "failed" if rng.random() < fail_prob else "success"
            runs.append(
                {
                    "run_id": _rid(),
                    "pipeline_id": pid,
                    "run_date": day_str,
                    "status": status,
                    "duration_minutes": round(rng.uniform(3, 120), 1),
                    "rows_processed": rng.randint(10_000, 5_000_000),
                }
            )

            delay = int(rng.uniform(0, 30))
            if profile == "degraded":
                delay = int(rng.uniform(30, 180))
            elif profile == "failing":
                delay = int(rng.uniform(120, 480))
            expected = datetime.combine(day, datetime.min.time()) + timedelta(hours=6)
            actual = expected + timedelta(minutes=delay)
            freshness.append(
                {
                    "check_id": f"fresh_{uuid.uuid4().hex[:8]}",
                    "pipeline_id": pid,
                    "check_date": day_str,
                    "expected_by": expected.isoformat(),
                    "actual_landed_at": actual.isoformat(),
                    "delay_minutes": delay,
                    "sla_breached": 1 if delay > 60 else 0,
                }
            )

            expected_rows = rng.randint(50_000, 500_000)
            noise = rng.gauss(0, 1)
            if profile == "failing":
                noise = rng.uniform(2.5, 5.0)
            elif profile == "degraded":
                noise = rng.uniform(1.0, 2.5)
            actual_rows = max(1000, int(expected_rows * (1 + noise * 0.15)))
            z = abs((actual_rows - expected_rows) / max(expected_rows * 0.1, 1))
            volumes.append(
                {
                    "anomaly_id": f"vol_{uuid.uuid4().hex[:8]}",
                    "pipeline_id": pid,
                    "check_date": day_str,
                    "expected_rows": expected_rows,
                    "actual_rows": actual_rows,
                    "z_score": round(z, 2),
                }
            )

            credits = base_credits * rng.uniform(0.8, 1.2)
            if profile == "failing":
                credits *= rng.uniform(1.5, 2.5)
            costs.append(
                {
                    "cost_id": f"cost_{uuid.uuid4().hex[:8]}",
                    "pipeline_id": pid,
                    "cost_date": day_str,
                    "credits_used": round(credits, 2),
                    "query_count": rng.randint(5, 200),
                }
            )

        if profile in {"degraded", "failing"} and rng.random() < 0.7:
            drift.append(
                {
                    "event_id": f"drift_{uuid.uuid4().hex[:8]}",
                    "pipeline_id": pid,
                    "detected_at": (today - timedelta(days=rng.randint(1, 20))).isoformat(),
                    "change_type": rng.choice(["column_added", "type_changed", "column_dropped"]),
                    "column_name": rng.choice(["amount", "user_id", "event_ts", "region"]),
                }
            )

    return {
        "pipeline_runs": runs,
        "freshness_checks": freshness,
        "schema_drift_events": drift,
        "volume_anomalies": volumes,
        "warehouse_cost_daily": costs,
        "profiles": profiles,
    }


def derive_training_labels(
    pipelines: list[dict[str, Any]],
    ops: dict[str, list[dict[str, Any]]],
    profiles: dict[str, str],
) -> list[dict[str, Any]]:
    """Transparent label: pipelines with failing/degraded profile likely fail next week."""
    rows: list[dict[str, Any]] = []
    pid_to_meta = {p["pipeline_id"]: p for p in pipelines}
    runs_by_pid: dict[str, list[dict[str, Any]]] = {}
    for r in ops["pipeline_runs"]:
        runs_by_pid.setdefault(r["pipeline_id"], []).append(r)

    for pid, meta in pid_to_meta.items():
        profile = profiles[pid]
        recent = sorted(runs_by_pid.get(pid, []), key=lambda x: x["run_date"])[-7:]
        recent_failures = sum(1 for r in recent if r["status"] == "failed")
        fresh = [f for f in ops["freshness_checks"] if f["pipeline_id"] == pid][-7:]
        sla_breach_count = sum(f["sla_breached"] for f in fresh)
        freshness_delay_avg = (
            sum(f["delay_minutes"] for f in fresh) / len(fresh) if fresh else 0.0
        )
        vols = [v for v in ops["volume_anomalies"] if v["pipeline_id"] == pid][-7:]
        volume_zscore_max = max((v["z_score"] for v in vols), default=0.0)
        drift_count = sum(1 for d in ops["schema_drift_events"] if d["pipeline_id"] == pid)
        costs = [c for c in ops["warehouse_cost_daily"] if c["pipeline_id"] == pid][-7:]
        credit_usage_7d = sum(c["credits_used"] for c in costs)
        if len(costs) >= 2:
            first_half = sum(c["credits_used"] for c in costs[: len(costs) // 2])
            second_half = sum(c["credits_used"] for c in costs[len(costs) // 2 :])
            credit_spike_pct = (
                ((second_half - first_half) / first_half * 100) if first_half else 0.0
            )
        else:
            credit_spike_pct = 0.0

        failed_next_7d = 1 if profile in {"failing", "degraded"} and (
            recent_failures >= 2 or sla_breach_count >= 3 or drift_count >= 1
        ) else 0
        if profile == "failing":
            failed_next_7d = 1

        rows.append(
            {
                "pipeline_id": pid,
                "owner_team": meta["owner_team"],
                "domain": meta["domain"],
                "criticality": meta["criticality"],
                "freshness_delay_avg": round(freshness_delay_avg, 1),
                "sla_breach_count": sla_breach_count,
                "recent_failures": recent_failures,
                "volume_zscore_max": round(volume_zscore_max, 2),
                "schema_drift_count": drift_count,
                "credit_usage_7d": round(credit_usage_7d, 2),
                "credit_spike_pct": round(credit_spike_pct, 1),
                "failed_next_7d": failed_next_7d,
            }
        )
    return rows
