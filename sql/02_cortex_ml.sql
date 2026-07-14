-- Cortex ML Classification (Snowflake production path)
-- Offline demo uses app/ml.py sklearn proxy with identical feature columns.

USE DATABASE RELIABILITY_DB;
USE SCHEMA PUBLIC;

-- Example: train reliability classifier
-- CREATE SNOWFLAKE.ML.CLASSIFICATION MODEL pipeline_reliability_model
--   INPUT (
--     freshness_delay_avg, sla_breach_count, recent_failures,
--     volume_zscore_max, schema_drift_count, credit_usage_7d, credit_spike_pct,
--     owner_team, domain, criticality
--   )
--   OUTPUT (failed_next_7d)
--   FROM training_features;

-- Batch score into pipeline_risk_scores
-- INSERT INTO pipeline_risk_scores (...)
-- SELECT pipeline_id, CURRENT_TIMESTAMP(), prob, tier, top_feature, top_value
-- FROM TABLE(pipeline_reliability_model!PREDICT(INPUT => SELECT * FROM training_features));
