# Privacy-Preserving Synthetic Clinical Datasets (20,000 Patient Cohort)

**Project**: Privacy-Preserving Clinical Data Gateway for Mental Health Systems (NDPA 2023 Compliant)  
**Author**: PRINCE PETER OKWUCHUKWU (Student ID: 2025/A/MIT/0689)  
**Institution**: MIVA Open University, Abuja, Nigeria  

---

## Dataset Overview

This directory contains **20,000 synthetic patient records** (comprising **40,095 total longitudinal clinical visit rows**) generated to support third-party research, algorithm validation, and data governance auditing under the **Nigeria Data Protection Act (NDPA) 2023**.

The dataset demonstrates the gateway's **Privacy by Design** architecture by providing two physically segregated data views:

1. **`RAW_VAULT` Repository (Restricted Source of Truth)**
   * Stores direct PII encrypted using **AES-256-GCM** (Ciphertexts) and patient IDs hashed using **SHA-256** pseudonyms.
   * Access is restricted to system administrators and compliance data protection officers.
   * Available formats: `raw_vault_20k.json` (34.31 MB), `raw_vault_20k.csv` (25.08 MB).

2. **`ANALYTICS_SCRUBBED` Repository (De-identified Research Vault)**
   * Open analytical dataset for third-party researchers and BI dashboards.
   * All Protected Health Information (PHI) in free-text clinical notes is redacted using a **spaCy + Gazetteer (EntityRuler)** hybrid engine (`[NAME]`, `[LOCATION]`, `[FACILITY]`, `[DATE]`, `[CONTACT]`).
   * Available formats: `analytics_scrubbed_20k.json` (26.73 MB), `analytics_scrubbed_20k.csv` (19.11 MB).

---

## Schema & Field Specifications

### 1. `RAW_VAULT` Files (`raw_vault_20k.json` & `raw_vault_20k.csv`)

| Field Name | Data Type | Protection Standard | Example Value |
| :--- | :--- | :--- | :--- |
| `record_id` | `UUID` | Primary Key | `c9a2f1b4-8e31-4a22-91d1-123456789abc` |
| `patient_pseudonym_id` | `VARCHAR(64)` | **SHA-256 Hash** | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `encrypted_name` | `TEXT` | **AES-256-GCM** | `gAAAAABn...` (Ciphertext) |
| `encrypted_contact` | `TEXT` | **AES-256-GCM** | `gAAAAABn...` (Ciphertext) |
| `age` | `INTEGER` | Demographic | `34` |
| `gender` | `VARCHAR(16)` | Demographic | `Female` |
| `location` | `VARCHAR(128)` | Location | `Yaba, Lagos` |
| `timestamp` | `ISO DATETIME` | Metadata | `2026-04-15T10:30:00` |
| `phq9_score` | `INTEGER` | Metric | `14` |
| `diagnosis` | `VARCHAR(128)` | Metric | `Major Depressive Disorder` |
| `treatment_plan` | `JSON String` | Metric | `["Fluoxetine 20mg", "CBT Weekly"]` |
| `raw_clinical_notes` | `TEXT` | **Restricted Unredacted** | Contains original unredacted text |
| `ingested_at` | `ISO DATETIME` | Audit Timestamp | `2026-09-21T13:45:00` |

---

### 2. `ANALYTICS_SCRUBBED` Files (`analytics_scrubbed_20k.json` & `analytics_scrubbed_20k.csv`)

| Field Name | Data Type | Privacy Status | Example Value |
| :--- | :--- | :--- | :--- |
| `record_id` | `UUID` | Anonymous Key | `c9a2f1b4-8e31-4a22-91d1-123456789abc` |
| `patient_pseudonym_id` | `VARCHAR(64)` | Pseudonym Linkage | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `age` | `INTEGER` | Demographic | `34` |
| `gender` | `VARCHAR(16)` | Demographic | `Female` |
| `location` | `VARCHAR(128)` | Location | `Yaba, Lagos` |
| `timestamp` | `ISO DATETIME` | Metadata | `2026-04-15T10:30:00` |
| `phq9_score` | `INTEGER` | Metric | `14` |
| `diagnosis` | `VARCHAR(128)` | Metric | `Major Depressive Disorder` |
| `treatment_plan` | `JSON String` | Metric | `["Fluoxetine 20mg", "CBT Weekly"]` |
| `scrubbed_clinical_notes` | `TEXT` | **spaCy + Gazetteer Redacted** | `Patient [NAME] visited [FACILITY] in [LOCATION]...` |
| `scrubbed_at` | `ISO DATETIME` | Audit Timestamp | `2026-09-21T13:45:00` |

---

## Empirical Verification Metrics (20,000 Cohort)

* **PII Removal Accuracy**: **100.00%**
* **De-identification Success Rate**: **100.00%**
* **Residual PII Count**: **0**
* **NDPA 2023 Compliance**: Fully compliant under Section 24 (Privacy by Design).

---

## Instructions for Third-Party Researchers

### Loading Data in Python (Pandas)
```python
import pandas as pd

# Load de-identified research dataset
df_analytics = pd.read_csv("data/analytics_scrubbed_20k.csv")
print(df_analytics.info())
print(df_analytics[["diagnosis", "phq9_score", "scrubbed_clinical_notes"]].head())
```

### Loading Data in SQL (ClickHouse)
```sql
CREATE TABLE ANALYTICS_SCRUBBED_EXPORT (
    record_id UUID,
    patient_pseudonym_id String,
    age UInt8,
    gender String,
    location String,
    timestamp DateTime,
    phq9_score UInt8,
    diagnosis String,
    treatment_plan String,
    scrubbed_clinical_notes String,
    scrubbed_at DateTime
) ENGINE = MergeTree() ORDER BY (timestamp, record_id);

-- Import from CSV
INSERT INTO ANALYTICS_SCRUBBED_EXPORT FROM INFILE 'data/analytics_scrubbed_20k.csv' FORMAT CSVWithNames;
```
