# Architecture

Snowflake Reliability Intelligence is a **batch intelligence pipeline** for data-platform health — not a chatbot.

## Layers

1. **Synthetic metadata** — pipeline runs, freshness, volume, schema drift, warehouse costs
2. **Feature table** — `training_features` with transparent `failed_next_7d` labels
3. **Cortex ML Classification** — predict pipeline failure risk (offline: sklearn proxy)
4. **Cortex LLM (AI_COMPLETE)** — batch RCA narratives for HIGH-risk pipelines
5. **Cortex Analyst** — 10 dropdown metrics questions via semantic model YAML
6. **Ops dashboard** — read-only Streamlit UI over FastAPI

**Runtime:** local demo/UI requires **Python 3.11**. On Python 3.14, Streamlit cold-starts are multi-minute and miss the <1 min launch target.

## Dynatrace alignment

Complements [Dynatrace Snowflake Observability Agent](https://github.com/dynatrace-oss/dynatrace-snowflake-observability-agent): DSOA monitors Snowflake infrastructure; this project adds **predictive ML + explainable narratives** on top of pipeline metadata.

## Offline vs Snowflake

| Component | Offline demo | Snowflake production |
|---|---|---|
| Warehouse | SQLite | Snowflake tables |
| ML | HistGradientBoosting | `SNOWFLAKE.ML.CLASSIFICATION` |
| RCA | Template narratives | `AI_COMPLETE` batch SQL |
| Analyst | SQL templates | Cortex Analyst REST API + YAML |
| Orchestration | `make demo` | Snowflake Tasks |
