-- ClickHouse Dual-Database Schema Setup for Privacy-Preserving Clinical Data Gateway
-- Author: Prince Peter Okwuchukwu (2025/A/MIT/0689)

CREATE DATABASE IF NOT EXISTS clinical_gateway;

USE clinical_gateway;

-- ============================================================================
-- 1. RAW_VAULT TABLE (Restricted Single Source of Truth)
-- Field-level AES-256 encrypted PII, SHA-256 pseudonymized patient link
-- ============================================================================
CREATE TABLE IF NOT EXISTS clinical_gateway.RAW_VAULT (
    record_id UUID DEFAULT generateUUIDv4(),
    patient_pseudonym_id String,          -- SHA-256 hash of direct identifier
    encrypted_name String,                 -- AES-256 encrypted direct name
    encrypted_contact String,              -- AES-256 encrypted phone / email
    age UInt8,
    gender LowCardinality(String),
    location String,
    timestamp DateTime,
    phq9_score UInt8,
    diagnosis String,
    treatment_plan String,                 -- JSON serialized string
    raw_clinical_notes String,             -- Unredacted free-text clinical notes
    ingested_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (timestamp, patient_pseudonym_id);

-- ============================================================================
-- 2. ANALYTICS_SCRUBBED TABLE (Scrubbed Analytics Repository)
-- Completely de-identified, spaCy NER redacted clinical notes, optimized for queries
-- ============================================================================
CREATE TABLE IF NOT EXISTS clinical_gateway.ANALYTICS_SCRUBBED (
    record_id UUID,
    patient_pseudonym_id String,          -- SHA-256 hash pseudonym
    age UInt8,
    gender LowCardinality(String),
    location String,
    timestamp DateTime,
    phq9_score UInt8,
    diagnosis String,
    treatment_plan String,
    scrubbed_clinical_notes String,        -- PHI-redacted free-text notes ([NAME], [LOCATION], etc.)
    scrubbed_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (timestamp, diagnosis, location);

-- ============================================================================
-- 3. AUDIT_TRAIL_LOG TABLE (Tamper-Evident Access & Compliance Log)
-- ============================================================================
CREATE TABLE IF NOT EXISTS clinical_gateway.AUDIT_TRAIL_LOG (
    log_id UUID DEFAULT generateUUIDv4(),
    user_id String,
    user_role LowCardinality(String),
    action_type LowCardinality(String),    -- INGESTION, REDACTION, QUERY, UNAUTHORIZED_ACCESS
    target_table LowCardinality(String),
    query_string String,
    ip_address String,
    execution_time_ms Float64,
    status LowCardinality(String),         -- SUCCESS, DENIED, ERROR
    timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (timestamp, user_role, status);
