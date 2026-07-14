"""Plain-language Metrics Explorer answers + evidence helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _top_name(rows: list[dict], name_key: str, value_key: str | None = None) -> str:
    if not rows:
        return "n/a"
    row = rows[0]
    name = str(row.get(name_key, "n/a"))
    if value_key and value_key in row:
        return f"{name} ({row[value_key]})"
    return name


def interpret_metrics_result(
    question_id: int,
    question: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return answer, cause, action, and optional chart column mapping."""
    n = len(rows)
    empty = {
        "answer": (
            f"No rows came back for “{question}” "
            "The platform looks clean for this slice, or the filter returned an empty set."
        ),
        "likely_cause": "Either the condition is rare right now, or the lookback window has no matching events.",
        "recommended_action": "Confirm the time window and filters, then re-run after the next batch score if you expected activity.",
        "chart": None,
    }
    if n == 0:
        return empty

    df = pd.DataFrame(rows)

    if question_id == 1:
        top = _top_name(rows, "pipeline_name", "failure_probability")
        teams = sorted({str(r.get("owner_team", "")) for r in rows if r.get("owner_team")})
        answer = (
            f"There are {n} HIGH-risk pipelines right now. "
            f"The hottest is {rows[0].get('pipeline_name')} at "
            f"{float(rows[0].get('failure_probability', 0)):.0%} failure probability, "
            f"with risk concentrated across {len(teams)} owning teams."
        )
        return {
            "answer": answer,
            "likely_cause": "Elevated failure probability is being driven by recent reliability signals on these workloads.",
            "recommended_action": "Open RCA Brief for the top pipelines and assign owners before the next run window.",
            "chart": {"category": "pipeline_name", "value": "failure_probability", "title": "Highest failure probability among HIGH-risk pipelines"},
        }

    if question_id == 2:
        leader = rows[0]
        answer = (
            f"{leader.get('owner_team')} leads freshness SLA breaches this month "
            f"with {int(leader.get('breach_count', 0))} breaches across {n} teams reporting."
        )
        return {
            "answer": answer,
            "likely_cause": "Upstream latency or contract misses are clustering on one or two owning teams.",
            "recommended_action": "Have the leading team review freshness SLAs and open RCA Briefs for their highest-breach pipelines.",
            "chart": {"category": "owner_team", "value": "breach_count", "title": "Freshness SLA breaches by team"},
        }

    if question_id == 3:
        leader = rows[0]
        answer = (
            f"The top credit consumer over the last 7 days is {leader.get('pipeline_name')} "
            f"at {float(leader.get('credits_7d', 0)):.0f} credits. "
            f"These {n} pipelines dominate recent warehouse spend."
        )
        return {
            "answer": answer,
            "likely_cause": "Heavy transforms or inefficient warehouses are concentrating cost on a small set of jobs.",
            "recommended_action": "Review warehouse sizing and clustering for the top spenders; flag any concurrent cost spikes in RCA Brief.",
            "chart": {"category": "pipeline_name", "value": "credits_7d", "title": "Warehouse credits (7d) — top pipelines"},
        }

    if question_id == 4:
        count = int(rows[0].get("failed_pipeline_count", 0))
        answer = f"{count} distinct pipelines failed at least once in the last 7 days."
        return {
            "answer": answer,
            "likely_cause": "Recent run failures are concentrated enough to show up in the weekly failure window.",
            "recommended_action": "Cross-check these against HIGH-risk scores on Pipeline Health Board and open RCA Briefs for repeat offenders.",
            "chart": None,
        }

    if question_id == 5:
        answer = (
            f"{n} business-critical pipelines are HIGH risk and still lack an RCA narrative — "
            f"starting with {rows[0].get('pipeline_name')}."
            if n
            else empty["answer"]
        )
        return {
            "answer": answer,
            "likely_cause": "Batch RCA coverage missed these critical workloads, or they escalated after the last narrative run.",
            "recommended_action": "Re-run the batch pipeline from Model Quality, then brief owners on each uncovered critical pipeline.",
            "chart": {"category": "pipeline_name", "value": "failure_probability", "title": "Critical HIGH-risk pipelines without RCA"},
        }

    if question_id == 6:
        leader = rows[0]
        answer = (
            f"Volume anomaly pressure is highest in the {leader.get('domain')} domain "
            f"(avg z-score {leader.get('avg_z_score')}) across {n} domains."
        )
        return {
            "answer": answer,
            "likely_cause": "Row-volume swings are departing from baseline in that domain’s pipelines.",
            "recommended_action": "Inspect domain pipelines for source spikes or drops; escalate any HIGH-risk overlap via RCA Brief.",
            "chart": {"category": "domain", "value": "avg_z_score", "title": "Average volume anomaly z-score by domain"},
        }

    if question_id == 7:
        leader = rows[0]
        answer = (
            f"{n} pipelines saw schema drift in the last 30 days. "
            f"{leader.get('pipeline_name')} leads with "
            f"{int(leader.get('drift_events', 0))} "
            f"{'event' if int(leader.get('drift_events', 0)) == 1 else 'events'}."
        )
        return {
            "answer": answer,
            "likely_cause": "Upstream schema changes are landing without matching contract updates.",
            "recommended_action": "Freeze downstream consumers for the top drift pipelines until contracts are validated.",
            "chart": {"category": "pipeline_name", "value": "drift_events", "title": "Schema drift events (30d)"},
        }

    if question_id == 8:
        leader = rows[0]
        answer = (
            f"{leader.get('owner_team')} has the highest run failure rate at "
            f"{float(leader.get('failure_rate_pct', 0)):.1f}% across {n} teams."
        )
        return {
            "answer": answer,
            "likely_cause": "Operational instability is concentrating on one owning team’s pipeline fleet.",
            "recommended_action": "Prioritize that team’s HIGH-risk pipelines in RCA Brief and review recent failed runs.",
            "chart": {"category": "owner_team", "value": "failure_rate_pct", "title": "Failure rate (%) by owning team"},
        }

    if question_id == 9:
        leader = rows[0]
        answer = (
            f"{n} pipelines show rising week-over-week credit spikes. "
            f"{leader.get('pipeline_name')} leads at {float(leader.get('credit_spike_pct', 0)):.0f}%."
        )
        return {
            "answer": answer,
            "likely_cause": "Cost is accelerating faster than baseline on these workloads — often query or volume growth.",
            "recommended_action": "FinOps and owners should review warehouse plans for the top spike pipelines this week.",
            "chart": {"category": "pipeline_name", "value": "credit_spike_pct", "title": "Credit spike % week over week"},
        }

    if question_id == 10:
        count = int(rows[0].get("escalated_pipeline_count", 0))
        answer = (
            f"{count} pipelines show escalation pressure (MEDIUM/HIGH risk with recent failures ≥ 2)."
        )
        return {
            "answer": answer,
            "likely_cause": "Repeat failures are pushing previously quieter pipelines into elevated risk tiers.",
            "recommended_action": "Treat this cohort as the watchlist-to-incident bridge — open RCA Briefs for any also marked Critical.",
            "chart": None,
        }

    return {
        "answer": f"Returned {n} rows for “{question}.”",
        "likely_cause": "See the evidence table for the drivers behind this slice.",
        "recommended_action": "Use Pipeline Health Board and RCA Brief to act on the highest-impact rows.",
        "chart": None,
    }


def evidence_frame(rows: list[dict[str, Any]], chart: dict[str, str] | None) -> pd.DataFrame | None:
    if not rows or not chart:
        return None
    df = pd.DataFrame(rows)
    cat, val = chart["category"], chart["value"]
    if cat not in df.columns or val not in df.columns:
        return None
    out = df[[cat, val]].copy()
    out[val] = pd.to_numeric(out[val], errors="coerce").fillna(0)
    return out.head(12)
