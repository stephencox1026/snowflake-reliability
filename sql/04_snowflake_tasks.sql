-- Snowflake Tasks: scheduled score → explain pipeline

USE DATABASE RELIABILITY_DB;
USE SCHEMA PUBLIC;

-- CREATE OR REPLACE TASK refresh_features
--   WAREHOUSE = COMPUTE_WH
--   SCHEDULE = 'USING CRON 0 6 * * * UTC'
-- AS
--   CREATE OR REPLACE TABLE training_features AS
--   SELECT ... -- feature engineering SQL;

-- CREATE OR REPLACE TASK score_pipelines
--   WAREHOUSE = COMPUTE_WH
--   AFTER refresh_features
-- AS
--   -- Cortex ML batch scoring (see 02_cortex_ml.sql);

-- CREATE OR REPLACE TASK generate_rca
--   WAREHOUSE = COMPUTE_WH
--   AFTER score_pipelines
-- AS
--   -- AI_COMPLETE batch RCA (see 03_cortex_llm_rca.sql);

-- ALTER TASK generate_rca RESUME;
-- ALTER TASK score_pipelines RESUME;
-- ALTER TASK refresh_features RESUME;
