-- Batch AI_COMPLETE RCA narratives for HIGH-risk pipelines (Snowflake production path)

USE DATABASE RELIABILITY_DB;
USE SCHEMA PUBLIC;

-- Example pattern:
-- INSERT INTO rca_narratives (pipeline_id, generated_at, summary, likely_cause, recommended_action, owner_team)
-- SELECT
--   s.pipeline_id,
--   CURRENT_TIMESTAMP(),
--   AI_COMPLETE('mistral-7b', OBJECT_CONSTRUCT(
--     'prompt', CONCAT(
--       'Summarize pipeline risk in 2 sentences. Pipeline: ', p.pipeline_name,
--       ', risk: ', s.risk_tier, ', probability: ', s.failure_probability,
--       ', top signal: ', s.top_feature
--     )
--   )):choices[0]:messages::STRING,
--   ...
-- FROM pipeline_risk_scores s
-- JOIN pipelines p ON p.pipeline_id = s.pipeline_id
-- WHERE s.risk_tier = 'HIGH';
