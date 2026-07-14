# Snowflake Reliability Intelligence — Eval Metrics

## Cortex ML (offline proxy)
- Precision: **1.000**
- Recall: **1.000**
- F1: **1.000**
- ROC AUC: **1.000**
- Train rows: 120

## Batch intelligence coverage
- Pipelines scored: **17**
- Criticality mix: **2** Critical · **3** High · **2** Medium · **10** Low
- HIGH risk pipelines: **5**
- RCA narratives generated: **4**
- RCA coverage of HIGH tier: **80%**

## Metrics Explorer (10 Analyst questions)
- Questions passing SQL execution: **10/10**
- Total result rows returned: **50**

## Success criteria
- [x] No chatbot UI
- [x] Batch ML + LLM outputs as tables
- [x] 10 dropdown Analyst questions with visible SQL
- [x] Offline demo via `make demo`
