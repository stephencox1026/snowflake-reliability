# Demo script — Snowflake Reliability Intelligence (~3 min)

Record a Loom walkthrough with this outline. Speak to the ops narrative: batch ML risk scores, not a chatbot.

## 0. Cold start (optional, 15s)

```bash
make install && make demo && make ui
```

Open http://127.0.0.1:8504 — or the Streamlit Cloud URL after deploy.

## 1. Pipeline Health Board (60–70s)

- Show **Critical / High / Medium / Low** KPI cards (tight action portfolio).
- Leave Focus on **Action queue (Critical + High)**.
- Point at the ranked table: Criticality → High, failure %, top signal, assessment.
- Read **Next steps** aloud — assign the owning team to the top pipeline.
- Click **Execute assignment → Solution**.

## 2. Solution tab (45–60s)

- Confirm pipeline selector and KPI chrome (Pipeline / Team / Signal / Failure %).
- Check 1–2 **To-do steps** from the signal playbook.
- Glance at the assignment brief + notes.
- Click **Create assignment** (optional on Cloud; fine on local).
- Mention durable assignments land in SQLite for the owning team.

## 3. Metrics Explorer (45–60s)

- Pick a curated Analyst question (e.g. freshness / critical high-risk).
- Click **Run analysis**.
- Walk the order: **Answer → table evidence → Likely cause → Recommended action**.
- Expand **SQL** once to show governed, auditable query (no free-form chat).

## Closing line

> Offline demo uses an sklearn Cortex-ML proxy and template RCA; production path is Snowflake `SNOWFLAKE.ML.CLASSIFICATION` + `AI_COMPLETE` + Cortex Analyst — see `sql/` and `docs/CORTEX_SETUP.md`.
