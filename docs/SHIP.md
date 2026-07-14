# Ship checklist — Snowflake Reliability Intelligence

Use this when publishing or refreshing the public demo.

## Local

```bash
cd snowflake-reliability
python3.11 -m venv .venv
make install
make demo
make ui          # http://127.0.0.1:8504
make test && make lint
make eval        # refreshes docs/METRICS.md
```

## GitHub

```bash
git status
git push origin main
```

Repo: https://github.com/stephencox1026/snowflake-reliability

## Streamlit Cloud

1. Open [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Repository: `stephencox1026/snowflake-reliability`
3. Branch: `main`
4. Main file path: `ui/cloud_app.py`
5. Python version: **3.11**
6. Advanced → confirm `requirements.txt` and `packages.txt` are detected
7. Deploy — first boot runs the offline `make demo` equivalent (1–3 minutes)
8. Live URL (current): _Add after deploy_

No secrets required for the offline demo.

## Screenshots + Loom

1. Capture stills into `docs/screenshots/` (Health Board, Metrics Explorer, Solution)
2. Record ~3 min walkthrough with [docs/DEMO.md](DEMO.md)
3. Paste the Loom URL into README under **Demo video**

## Done when

- [ ] Public repo loads
- [ ] Live Cloud URL opens the ops dashboard
- [ ] README has live link + screenshots + Loom link
- [ ] `make demo && make ui` still works offline
