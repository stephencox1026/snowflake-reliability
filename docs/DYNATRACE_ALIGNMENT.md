# Dynatrace Alignment

## Why this project for Dynatrace

Dynatrace operates at the intersection of **observability** and **enterprise data platforms**:

- **DSOA** (Snowflake Observability Agent) streams Snowflake telemetry into Dynatrace
- Internal teams need **governed AI** on warehouse data for reliability decisions
- Job postings require **Snowflake Cortex ML**, **Cortex Analyst**, and production AI workflows

## How this project maps

| Dynatrace need | This project |
|---|---|
| Snowflake platform expertise | Native DDL, Tasks, Cortex SQL scripts |
| Cortex ML models | Pipeline failure classification |
| Cortex LLM | Batch RCA narratives (AI_COMPLETE) |
| Cortex Analyst | 10-question Metrics Explorer + semantic YAML |
| Data observability | Freshness, volume, schema drift, cost signals |
| Not another chatbot | Batch pipeline + ops dashboard only |

## Interview pitch

> "Dynatrace monitors Snowflake with DSOA. I built the AI layer on top: Cortex ML predicts which pipelines will fail, LLM generates RCA briefs as governed table outputs, and Analyst answers predefined metrics questions through a semantic model — all without moving data out of Snowflake."

## Portfolio complement

- **InsightRAG** — conversational RAG + SQL agent
- **DocPulse** — document ML + anomaly dashboard
- **TourMind** — LangGraph ops command center
- **This project** — Snowflake Cortex batch intelligence for data platforms
