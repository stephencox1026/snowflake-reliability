-- Snowflake DDL for Reliability Intelligence (run in trial account)
CREATE DATABASE IF NOT EXISTS RELIABILITY_DB;
CREATE SCHEMA IF NOT EXISTS RELIABILITY_DB.PUBLIC;
USE DATABASE RELIABILITY_DB;
USE SCHEMA PUBLIC;

CREATE TABLE IF NOT EXISTS pipelines (
    pipeline_id VARCHAR PRIMARY KEY,
    pipeline_name VARCHAR NOT NULL,
    domain VARCHAR NOT NULL,
    owner_team VARCHAR NOT NULL,
    criticality VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR PRIMARY KEY,
    pipeline_id VARCHAR NOT NULL,
    run_date DATE NOT NULL,
    status VARCHAR NOT NULL,
    duration_minutes FLOAT NOT NULL,
    rows_processed INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS freshness_checks (
    check_id VARCHAR PRIMARY KEY,
    pipeline_id VARCHAR NOT NULL,
    check_date DATE NOT NULL,
    expected_by TIMESTAMP_NTZ NOT NULL,
    actual_landed_at TIMESTAMP_NTZ NOT NULL,
    delay_minutes INTEGER NOT NULL,
    sla_breached INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS training_features (
    pipeline_id VARCHAR PRIMARY KEY,
    owner_team VARCHAR NOT NULL,
    domain VARCHAR NOT NULL,
    criticality VARCHAR NOT NULL,
    freshness_delay_avg FLOAT NOT NULL,
    sla_breach_count INTEGER NOT NULL,
    recent_failures INTEGER NOT NULL,
    volume_zscore_max FLOAT NOT NULL,
    schema_drift_count INTEGER NOT NULL,
    credit_usage_7d FLOAT NOT NULL,
    credit_spike_pct FLOAT NOT NULL,
    failed_next_7d INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_risk_scores (
    pipeline_id VARCHAR PRIMARY KEY,
    scored_at TIMESTAMP_NTZ NOT NULL,
    failure_probability FLOAT NOT NULL,
    risk_tier VARCHAR NOT NULL,
    top_feature VARCHAR NOT NULL,
    top_feature_value FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS rca_narratives (
    pipeline_id VARCHAR PRIMARY KEY,
    generated_at TIMESTAMP_NTZ NOT NULL,
    summary VARCHAR NOT NULL,
    likely_cause VARCHAR NOT NULL,
    recommended_action VARCHAR NOT NULL,
    owner_team VARCHAR NOT NULL
);
