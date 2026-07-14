"""Streamlit Cloud entrypoint.

Copies a committed offline seed into a writable /tmp data root on Cloud, then
loads the ops dashboard. Local use: prefer `make ui` after `make demo`.

Streamlit Cloud main file: ui/cloud_app.py

Important: do not call Streamlit APIs here before loading streamlit_app.py —
that file calls st.set_page_config() first, which must be the first st command.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("RELIABILITY_UI_DIRECT", "true")

SEED_DIR = ROOT / "data" / "seed"


def _is_streamlit_cloud() -> bool:
    if Path("/mount/src").exists():
        return True
    return os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT", "").lower() == "cloud"


def _data_root() -> Path:
    if _is_streamlit_cloud():
        return Path("/tmp/snowflake-reliability")
    return ROOT / "data"


def _configure_paths(data_root: Path) -> None:
    models = data_root / "models"
    data_root.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    # Always absolute sqlite URL (four slashes for absolute path).
    db_path = (data_root / "warehouse.db").resolve()
    os.environ["RELIABILITY_DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["RELIABILITY_DATA_DIR"] = str(data_root.resolve())
    os.environ["RELIABILITY_MODELS_DIR"] = str(models.resolve())
    print(f"==> data root → {data_root}", flush=True)
    print(f"==> database  → {db_path}", flush=True)


def _seed_files_present() -> bool:
    return (
        (SEED_DIR / "warehouse.db").exists()
        and (SEED_DIR / "models" / "reliability_classifier.joblib").exists()
    )


def _copy_seed(data_root: Path) -> None:
    """Install committed demo artifacts into the writable data root."""
    if not _seed_files_present():
        raise RuntimeError(f"Missing committed seed under {SEED_DIR}")

    models = data_root / "models"
    models.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SEED_DIR / "warehouse.db", data_root / "warehouse.db")
    shutil.copy2(
        SEED_DIR / "models" / "reliability_classifier.joblib",
        models / "reliability_classifier.joblib",
    )
    meta = SEED_DIR / "models" / "reliability_classifier_meta.json"
    if meta.exists():
        shutil.copy2(meta, models / "reliability_classifier_meta.json")
    cache = SEED_DIR / "analyst_cache.json"
    if cache.exists():
        shutil.copy2(cache, data_root / "analyst_cache.json")
    print(f"==> Copied demo seed → {data_root}", flush=True)


def _demo_ready() -> bool:
    from app.config import get_settings
    from app.db import warehouse_ready

    get_settings.cache_clear()
    settings = get_settings()
    settings.ensure_dirs()
    model = Path(settings.reliability_models_dir) / "reliability_classifier.joblib"
    ready = warehouse_ready(settings) and model.exists()
    print(f"==> demo ready={ready} model={model.exists()} db={settings.reliability_database_url}", flush=True)
    return ready


def ensure_demo() -> None:
    """Make offline artifacts available before any Streamlit UI calls."""
    data_root = _data_root()
    _configure_paths(data_root)

    if _demo_ready():
        return

    # Prefer copy of committed seed (fast + Cloud-safe). Fall back to full build locally.
    try:
        if _seed_files_present():
            print("==> Installing committed offline seed…", flush=True)
            _copy_seed(data_root)
            if _demo_ready():
                return
    except Exception as exc:  # noqa: BLE001 — show Cloud logs clearly
        print(f"==> Seed copy failed: {exc!r}", flush=True)

    if _is_streamlit_cloud():
        raise RuntimeError(
            "Cloud demo seed is missing or unreadable. "
            "Ensure data/seed/warehouse.db and model files are in the repo."
        )

    print("==> No seed installed — running full build_demo…", flush=True)
    from scripts.build_demo import main as build_demo

    build_demo()
    if not _demo_ready():
        raise RuntimeError("build_demo finished but warehouse/model are still missing.")


ensure_demo()

_APP = ROOT / "ui" / "streamlit_app.py"
_spec = importlib.util.spec_from_file_location("reliability_streamlit_app", _APP)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Cannot load dashboard from {_APP}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["reliability_streamlit_app"] = _mod
_spec.loader.exec_module(_mod)
