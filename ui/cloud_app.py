"""Streamlit Cloud entrypoint.

Seeds the offline demo (warehouse + model + analyst cache) on first boot, then
loads the ops dashboard. Local use: prefer `make ui` after `make demo`.

Streamlit Cloud main file: ui/cloud_app.py

Important: do not call Streamlit APIs here before loading streamlit_app.py —
that file calls st.set_page_config() first, which must be the first st command.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("RELIABILITY_UI_DIRECT", "true")


def _demo_ready() -> bool:
    from app.config import get_settings
    from app.db import warehouse_ready

    settings = get_settings()
    model = settings.reliability_models_dir / "reliability_classifier.joblib"
    return warehouse_ready(settings) and model.exists()


def ensure_demo() -> None:
    """Seed offline artifacts before any Streamlit UI calls."""
    if _demo_ready():
        return
    print("==> Snowflake Reliability first boot — seeding offline demo…", flush=True)
    from scripts.build_demo import main as build_demo

    build_demo()


ensure_demo()

_APP = ROOT / "ui" / "streamlit_app.py"
_spec = importlib.util.spec_from_file_location("reliability_streamlit_app", _APP)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Cannot load dashboard from {_APP}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["reliability_streamlit_app"] = _mod
_spec.loader.exec_module(_mod)
