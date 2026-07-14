.PHONY: help install demo pipeline-run api ui eval test lint clean

PY := .venv/bin/python
PIP := .venv/bin/pip
PYTHON311 := $(shell command -v python3.11 2>/dev/null)

help:
	@echo "Snowflake Reliability Intelligence:"
	@echo "  make install       Install deps into .venv (requires Python 3.11)"
	@echo "  make demo          Seed data + train + score + RCA + analyst cache"
	@echo "  make pipeline-run  Re-run batch pipeline on existing data"
	@echo "  make api           FastAPI on :8002 (optional; UI defaults to direct DB)"
	@echo "  make ui            Streamlit dashboard on :8504 (direct DB, no API needed)"
	@echo "  make ui-api        Streamlit using API backend instead of direct DB"
	@echo "  make ui-time       Print UI cold-start import timings"
	@echo "  make eval          Write docs/METRICS.md"
	@echo "  make test          pytest"
	@echo "  make lint          ruff"
	@echo ""
	@echo "UI tip: keep one Streamlit process warm. Concurrent imports against the same"
	@echo ".venv contend on disk and stretch cold start (import streamlit alone can take minutes)."

install:
	@if [ -z "$(PYTHON311)" ]; then \
		echo "error: python3.11 is required (Streamlit cold-starts are unusable on 3.14)."; \
		echo "Install Python 3.11 and re-run: make install"; \
		exit 1; \
	fi
	$(PYTHON311) -m venv .venv
	$(PIP) install -r requirements-dev.txt

demo:
	$(PY) -m scripts.build_demo

pipeline-run:
	$(PY) -c "from app.config import get_settings; from app.pipeline import run_batch_pipeline; print(run_batch_pipeline(get_settings()))"

api:
	.venv/bin/uvicorn app.api:app --port 8002 --host 127.0.0.1

ui:
	@xattr -cr .venv 2>/dev/null || true
	@$(PY) -c "import streamlit; print('warmed streamlit')"
	RELIABILITY_UI_DIRECT=true $(PY) -m streamlit run ui/streamlit_app.py \
		--server.port 8504 \
		--server.headless true \
		--server.fileWatcherType none \
		--browser.gatherUsageStats false

ui-api:
	@xattr -cr .venv 2>/dev/null || true
	@$(PY) -c "import streamlit; print('warmed streamlit')"
	RELIABILITY_UI_DIRECT=false $(PY) -m streamlit run ui/streamlit_app.py \
		--server.port 8504 \
		--server.headless true \
		--server.fileWatcherType none \
		--browser.gatherUsageStats false

ui-time:
	$(PY) -m scripts.time_ui_coldstart

eval:
	$(PY) -m scripts.evaluate

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check app scripts tests ui

clean:
	rm -rf data/warehouse.db data/models data/analyst_cache.json .pytest_cache .ruff_cache
	@mkdir -p data/models && touch data/models/.gitkeep
