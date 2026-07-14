"""Cold-start timing gate for the Streamlit UI.

Prints seconds for streamlit, pandas, data_access, summary fetch, and HTML bars path.
Asserts our app does not import ui.charts on the Health Board cold path.

Note: installing plotly means Streamlit may import plotly at package load time;
that is outside this app's import graph. We still keep ui.charts off the hot path.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _timed(label: str, fn):
    t0 = time.perf_counter()
    result = fn()
    dt = time.perf_counter() - t0
    print(f"{label:32s} {dt:6.3f}s", flush=True)
    return result


def main() -> int:
    total_t0 = time.perf_counter()
    _timed("import streamlit", lambda: __import__("streamlit"))
    _timed("import pandas", lambda: __import__("pandas"))
    _timed("import ui.data_access", lambda: __import__("ui.data_access"))
    _timed("import ui.kpi", lambda: __import__("ui.kpi"))

    from ui.data_access import get_at_risk, get_dashboard_summary
    from ui.kpi import criticality_mix_html

    summary = _timed("get_dashboard_summary", lambda: get_dashboard_summary(summary_version=2))
    _timed("get_at_risk(limit=100)", lambda: get_at_risk(limit=100))
    _timed(
        "criticality_mix_html",
        lambda: criticality_mix_html(
            {
                "critical": summary.get("critical", 0),
                "high": summary.get("high", 0),
                "medium": summary.get("medium", 0),
                "low": summary.get("low", 0),
            }
        ),
    )

    print(f"{'TOTAL':32s} {time.perf_counter() - total_t0:6.3f}s", flush=True)
    print(f"ui.charts loaded: {'ui.charts' in sys.modules}", flush=True)
    if "ui.charts" in sys.modules:
        print("FAIL: ui.charts should not load on Health Board cold path", flush=True)
        return 1
    print("ok: Health Board cold path avoids ui.charts", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
