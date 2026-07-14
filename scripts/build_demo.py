"""One-command offline demo bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analyst import build_analyst_cache  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.pipeline import run_batch_pipeline  # noqa: E402
from app.warehouse import seed_warehouse  # noqa: E402


def main() -> None:
    settings = get_settings()
    settings.ensure_dirs()

    print("==> Seeding synthetic pipeline metadata (SQLite)...")
    counts = seed_warehouse(settings)
    for k, v in counts.items():
        print(f"    {k:22s} {v:>6,}")

    print("\n==> Running batch pipeline (train → score → RCA)...")
    out = run_batch_pipeline(settings)
    print(f"    precision={out['model_metrics']['precision']:.3f}  "
          f"recall={out['model_metrics']['recall']:.3f}  "
          f"f1={out['model_metrics']['f1']:.3f}")
    print(f"    scored={out['pipelines_scored']}  rca_narratives={out['rca_narratives_generated']}")

    print("\n==> Building Analyst question cache (10 questions)...")
    cache_path = build_analyst_cache(settings)
    print(f"    {cache_path}")

    print("\nDemo ready.")
    print("  make api   → http://127.0.0.1:8002/docs")
    print("  make ui    → http://127.0.0.1:8504")


if __name__ == "__main__":
    main()
