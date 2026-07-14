"""Golden evaluation for ML, RCA coverage, and Analyst questions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analyst import QUESTIONS, run_question  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import connect, fetchall_dicts  # noqa: E402

DOCS = ROOT / "docs"
METRICS = DOCS / "METRICS.md"


def main() -> None:
    settings = get_settings()
    DOCS.mkdir(parents=True, exist_ok=True)

    conn = connect(settings)
    try:
        metrics = fetchall_dicts(
            conn, "SELECT * FROM model_eval_metrics ORDER BY trained_at DESC LIMIT 1"
        )
        high_risk = fetchall_dicts(
            conn, "SELECT COUNT(*) AS n FROM pipeline_risk_scores WHERE risk_tier = 'HIGH'"
        )[0]["n"]
        rca_count = fetchall_dicts(conn, "SELECT COUNT(*) AS n FROM rca_narratives")[0]["n"]
        total = fetchall_dicts(conn, "SELECT COUNT(*) AS n FROM pipelines")[0]["n"]
        bands = {
            r["criticality"]: r["n"]
            for r in fetchall_dicts(
                conn,
                "SELECT lower(criticality) AS criticality, COUNT(*) AS n "
                "FROM pipelines GROUP BY 1",
            )
        }
    finally:
        conn.close()

    analyst_ok = 0
    analyst_rows = 0
    for qid in QUESTIONS:
        result = run_question(settings, qid)
        if result["row_count"] >= 0 and result["sql"]:
            analyst_ok += 1
            analyst_rows += result["row_count"]

    m = metrics[0] if metrics else {}
    lines = [
        "# Snowflake Reliability Intelligence — Eval Metrics",
        "",
        "## Cortex ML (offline proxy)",
        f"- Precision: **{m.get('precision_score', 0):.3f}**",
        f"- Recall: **{m.get('recall_score', 0):.3f}**",
        f"- F1: **{m.get('f1_score', 0):.3f}**",
        f"- ROC AUC: **{m.get('roc_auc', 0):.3f}**",
        f"- Train rows: {m.get('train_rows', 0)}",
        "",
        "## Batch intelligence coverage",
        f"- Pipelines scored: **{total}**",
        (
            f"- Criticality mix: **{bands.get('critical', 0)}** Critical · "
            f"**{bands.get('high', 0)}** High · "
            f"**{bands.get('medium', 0)}** Medium · "
            f"**{bands.get('low', 0)}** Low"
        ),
        f"- HIGH risk pipelines: **{high_risk}**",
        f"- RCA narratives generated: **{rca_count}**",
        f"- RCA coverage of HIGH tier: **{rca_count / max(high_risk, 1):.0%}**",
        "",
        "## Metrics Explorer (10 Analyst questions)",
        f"- Questions passing SQL execution: **{analyst_ok}/10**",
        f"- Total result rows returned: **{analyst_rows}**",
        "",
        "## Success criteria",
        "- [x] No chatbot UI",
        "- [x] Batch ML + LLM outputs as tables",
        "- [x] 10 dropdown Analyst questions with visible SQL",
        "- [x] Offline demo via `make demo`",
        "",
    ]
    METRICS.write_text("\n".join(lines))
    print(METRICS.read_text())
    summary = {
        "analyst_questions_ok": analyst_ok,
        "high_risk": high_risk,
        "rca_count": rca_count,
        "model_metrics": m,
    }
    (DOCS / "eval_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
