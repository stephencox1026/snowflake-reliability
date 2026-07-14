# Snowflake Cortex Setup

## 1. Trial account

1. Sign up at https://signup.snowflake.com/
2. Choose **Enterprise Edition** + **AWS US West 2 (Oregon)**
3. $400 credits, 30 days, no credit card required

## 2. Enable Cortex

Grant roles:
```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE YOUR_ROLE;
GRANT USE AI FUNCTIONS ON ACCOUNT TO ROLE YOUR_ROLE;
```

## 3. Run DDL

```bash
# In Snowflake worksheet
@snowflake-reliability/sql/01_ddl.sql
```

Load seed data from your synthetic generator or COPY from staged CSVs.

## 4. Cortex ML

See [sql/02_cortex_ml.sql](../sql/02_cortex_ml.sql)

## 5. Cortex LLM RCA

See [sql/03_cortex_llm_rca.sql](../sql/03_cortex_llm_rca.sql)

## 6. Cortex Analyst

1. Upload `semantic_models/pipeline_health.yaml` to a stage
2. Call REST API with `question_id` mapped to natural language
3. Offline demo uses equivalent SQL templates in `app/analyst.py`

## 7. Tasks

See [sql/04_snowflake_tasks.sql](../sql/04_snowflake_tasks.sql)
