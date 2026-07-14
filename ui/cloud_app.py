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


def _is_streamlit_cloud() -> bool:
    # Cloud clones into /mount/src/<repo>; local runs never have this path.
    if Path("/mount/src").exists():
        return True
    return os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT", "").lower() == "cloud"


def _configure_cloud_writable_paths() -> None:
    """Repo mount is often not writable — keep SQLite + models under /tmp on Cloud."""
    if not _is_streamlit_cloud():
        return
    data = Path("/tmp/snowflake-reliability")
    models = data / "models"
    data.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    os.environ["RELIABILITY_DATABASE_URL"] = f"sqlite:///{data / 'warehouse.db'}"
    os.environ["RELIABILITY_DATA_DIR"] = str(data)
    os.environ["RELIABILITY_MODELS_DIR"] = str(models)
    print(f"==> Streamlit Cloud data root → {data}", flush=True)


_configure_cloud_writable_paths()


def _demo_ready() -> bool:
    from app.config import get_settings
    from app.db import warehouse_ready

    settings = get_settings()
    settings.ensure_dirs()
    model = settings.reliability_models_dir / "reliability_classifier.joblib"
    return warehouse_ready(settings) and model.exists()


def ensure_demo() -> None:
    """Seed offline artifacts before any Streamlit UI calls."""
    if _demo_ready():
        return
    print("==> Snowflake Reliability first boot — seeding offline demo…", flush=True)
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    settings.ensure_dirs()
    from scripts.build_demo import main as build_demo

    build_demo()
    get_settings.cache_clear()
    if not _demo_ready():
        raise RuntimeError(
            "Demo seed finished but warehouse/model are still missing. "
            "Check Cloud logs for build_demo errors."
        )


ensure_demo()

_APP = ROOT / "ui" / "streamlit_app.py"
_spec = importlib.util.spec_from_file_location("reliability_streamlit_app", _APP)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Cannot load dashboard from {_APP}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["reliability_streamlit_app"] = _mod
_spec.loader.exec_module(_mod)
