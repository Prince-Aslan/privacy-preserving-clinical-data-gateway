# SYSTEM ENTITY-RELATIONSHIP DIAGRAM (ERD) & DATABASE SPECIFICATION

**Project**: Privacy-Preserving Clinical Data Gateway for Mental Health Systems (NDPA 2023 Compliant)  
**Author**: PRINCE PETER OKWUCHUKWU (Student ID: 2025/A/MIT/0689)  
**Degree**: Professional Master of Information Technology (MIT)  
**Institution**: MIVA Open University, Abuja, Nigeria  

---

## 1. Executive System ERD Diagram

The architecture below illustrates the complete Entity-Relationship Diagram (ERD) and transactional database schema for the clinical data gateway. The database model operationalizes **Privacy by Design** (NDPA 2023 Section 24) by physically segregating encrypted source-of-truth records (`RAW_VAULT`) from de-identified research analytics (`ANALYTICS_SCRUBBED`), governed by User Role Authentication (`USER_ACCOUNTS`) and Tamper-Evident Audit Logging (`AUDIT_TRAIL_LOG`).

![System ERD Diagram](file:///C:/Users/USERR/.gemini/antigravity-ide/brain/117cb94f-ee06-4c4a-9ebb-7e7a579e47c4/system_erd_diagram_1787439200004.jpg)

---

## 2. Complete Data Dictionary & Entity Specifications

### 2.1 Entity: `USER_ACCOUNTS` (Authentication & RBAC)
Stores system credentials, hashed passwords, and Role-Based Access Control (RBAC) classifications to enforce operational permission boundaries across gateway endpoints.

| Attribute Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `username` | `VARCHAR(64)` | **PRIMARY KEY** | Unique user authentication identifier |
| `hashed_password` | `VARCHAR(255)` | `NOT NULL` | Bcrypt hashed user password |
| `user_role` | `ENUM` | `NOT NULL` | Assigned RBAC role (`admin`, `clinician`, `researcher`, `data_officer`) |
| `full_name` | `VARCHAR(128)` | `NOT NULL` | Full registered user title and name |
| `created_at` | `TIMESTAMP` | `NOT NULL` | Account creation timestamp |

---

### 2.2 Entity: `PATIENT_PROFILE` (Logical Ingestion Entity)
Represents the logical patient profile submitted during clinical ingestion before cryptographic segregation and spaCy NER de-identification.

| Attribute Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `patient_id` | `VARCHAR(64)` | **LOGICAL PK** | Original hospital/clinic patient identification code |
| `patient_name` | `VARCHAR(128)` | **PII (Direct)** | Original unencrypted patient full name |
| `contact_info` | `VARCHAR(64)` | **PII (Direct)** | Patient phone number or email address |
| `age` | `INTEGER` | `NOT NULL` | Patient age at clinical visit (18-120) |
| `gender` | `VARCHAR(16)` | `NOT NULL` | Patient gender classification (Male, Female) |
| `location` | `VARCHAR(128)` | `NOT NULL` | Facility geographic location (LGA / State) |

---

### 2.3 Entity: `RAW_VAULT` (ClickHouse Encrypted Source of Truth)
Restricted source-of-truth table in ClickHouse storing column-level AES-256-GCM ciphertexts for direct PII, SHA-256 pseudonym linkage hashes, and unredacted clinical narratives. Access is restricted to `admin` and `data_officer` roles.

| Attribute Name | Data Type | Constraint / Status | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | `UUID` | **PRIMARY KEY** | Unique system record primary key |
| `patient_pseudonym_id` | `VARCHAR(64)` | **SHA-256 HASH** | Deterministic salted hash for longitudinal record linkage |
| `encrypted_name` | `TEXT` | **AES-256-GCM** | Authenticated ciphertext of patient direct full name |
| `encrypted_contact` | `TEXT` | **AES-256-GCM** | Authenticated ciphertext of phone number / contact info |
| `age` | `UINT8` | `NOT NULL` | Patient demographic age |
| `gender` | `VARCHAR(16)` | `NOT NULL` | Demographic gender |
| `location` | `VARCHAR(128)` | `NOT NULL` | Demographic clinic location |
| `timestamp` | `DATETIME` | `NOT NULL` | Clinical visit timestamp |
| `phq9_score` | `UINT8` | `NOT NULL` | Longitudinal PHQ-9 depression assessment score (0-27) |
| `diagnosis` | `VARCHAR(128)` | `NOT NULL` | Psychiatric diagnostic classification code |
| `treatment_plan` | `TEXT (JSON)` | `NOT NULL` | Serialized pharmacotherapy and CBT therapy plan |
| `raw_clinical_notes` | `TEXT` | **RESTRICTED** | Unredacted physician free-text clinical narrative |
| `ingested_at` | `DATETIME` | `TIMESTAMP` | System ingestion timestamp |

---

### 2.4 Entity: `ANALYTICS_SCRUBBED` (ClickHouse De-Identified Analytics Vault)
Fully de-identified, columnar ClickHouse table optimized for high-performance aggregate queries by researchers. Excludes direct PII columns and replaces all PHI in free-text clinical notes with standardized tokens (`[NAME]`, `[LOCATION]`, `[FACILITY]`, `[DATE]`, `[CONTACT]`).

| Attribute Name | Data Type | Privacy Status | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | `UUID` | **LINKED KEY** | Anonymous reference key linking to RAW_VAULT |
| `patient_pseudonym_id` | `VARCHAR(64)` | **SHA-256 HASH** | Pseudonymized linkage key for trend analysis |
| `age` | `UINT8` | `DEMOGRAPHIC` | Patient age |
| `gender` | `VARCHAR(16)` | `DEMOGRAPHIC` | Patient gender |
| `location` | `VARCHAR(128)` | `DEMOGRAPHIC` | Geographic facility location |
| `timestamp` | `DATETIME` | `METADATA` | Clinical visit timestamp |
| `phq9_score` | `UINT8` | `METRIC` | Longitudinal PHQ-9 score for cohort evaluation |
| `diagnosis` | `VARCHAR(128)` | `CLASSIFICATION` | Psychiatric diagnostic code |
| `treatment_plan` | `TEXT (JSON)` | `METRIC` | Treatment plan details |
| `scrubbed_clinical_notes` | `TEXT` | **spaCy REDACTED** | Clinical narrative with PHI replaced by `[NAME]`, `[LOCATION]`, etc. |
| `scrubbed_at` | `DATETIME` | `TIMESTAMP` | Pipeline transformation timestamp |

---

### 2.5 Entity: `AUDIT_TRAIL_LOG` (Tamper-Evident Compliance Log)
Mandatory audit logging table under NDPA 2023 Section 24. Logs every access attempt, data ingestion, pipeline transformation, and researcher query with user credentials, IP address, latency, and status.

| Attribute Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `log_id` | `UUID` | **PRIMARY KEY** | Unique audit entry identifier |
| `user_id` | `VARCHAR(64)` | **FOREIGN KEY** | Username executing the transaction |
| `user_role` | `VARCHAR(32)` | `NOT NULL` | Role of user during execution |
| `action_type` | `VARCHAR(32)` | `NOT NULL` | Transaction category (`INGESTION`, `QUERY`, `QUERY_VAULT`, `PIPELINE`) |
| `target_table` | `VARCHAR(64)` | `NOT NULL` | Target ClickHouse table accessed |
| `query_string` | `TEXT` | `NOT NULL` | Executed SQL query or API operation details |
| `ip_address` | `VARCHAR(45)` | `NOT NULL` | Client network IP address |
| `execution_time_ms` | `FLOAT` | `NOT NULL` | Execution latency in milliseconds |
| `status` | `VARCHAR(16)` | `NOT NULL` | Transaction outcome status (`SUCCESS`, `FORBIDDEN`, `ERROR`) |
| `timestamp` | `DATETIME` | `NOT NULL` | Immutable log timestamp |

---

## 3. Entity Relationships & Cardinality Matrix

| Source Entity | Target Entity | Relationship Type | Cardinality | Key Mapping / Linkage Mechanism |
| :--- | :--- | :---: | :---: | :--- |
| `USER_ACCOUNTS` | `AUDIT_TRAIL_LOG` | One-to-Many | $1 : N$ | `USER_ACCOUNTS.username` = `AUDIT_TRAIL_LOG.user_id` |
| `PATIENT_PROFILE` | `RAW_VAULT` | One-to-Many | $1 : N$ | $\text{SHA-256}(\text{Salt} \parallel \text{PATIENT\_PROFILE.patient\_id}) =$ `RAW_VAULT.patient_pseudonym_id` |
| `RAW_VAULT` | `ANALYTICS_SCRUBBED` | One-to-One | $1 : 1$ | `RAW_VAULT.record_id` = `ANALYTICS_SCRUBBED.record_id` |
| `USER_ACCOUNTS` | `RAW_VAULT` | RBAC Restricted | $1 : N$ | Restricted to roles: `admin`, `data_officer` (JWT enforced) |
| `USER_ACCOUNTS` | `ANALYTICS_SCRUBBED` | Role-Based Query | $1 : N$ | Accessible to roles: `researcher`, `clinician`, `data_officer`, `admin` |

---

## 4. Transaction Processing & Data Flow Mechanics

```
┌─────────────────┐       1. Ingest Payload       ┌──────────────────────┐
│ Clinician User  │ ────────────────────────────> │ FastAPI Gateway      │
└─────────────────┘                               └──────────┬───────────┘
                                                             │
                                                  2. Validate Schema & Auth
                                                             │
                                                             ▼
                                                  ┌──────────────────────┐
                                                  │ Crypto & NER Engine  │
                                                  └──────────┬───────────┘
                                                             │
                              ┌──────────────────────────────┴──────────────────────────────┐
                              │ 3a. AES-256 & SHA-256                                       │ 3b. spaCy NER Redaction
                              ▼                                                             ▼
                     ┌──────────────────┐                                          ┌──────────────────┐
                     │    RAW_VAULT     │                                          │ANALYTICS_SCRUBBED│
                     │ (Encrypted PII)  │                                          │  (Scrubbed PHI)  │
                     └────────┬─────────┘                                          └────────┬─────────┘
                              │                                                             │
                              └──────────────────────────────┬──────────────────────────────┘
                                                             │ 4. Audit Log
                                                             ▼
                                                   ┌────────────────────┐
                                                   │  AUDIT_TRAIL_LOG   │
                                                   └────────────────────┘
```

1. **Ingestion Transaction**:
   - Clinician posts patient JSON to gateway.
   - Gateway validates Pydantic schema and issues `SHA-256` pseudonym hash and `AES-256-GCM` ciphertexts.
   - Source-of-truth stored in `RAW_VAULT`.

2. **Scrubbing Transaction**:
   - `spaCy` NER engine replaces PHI elements in free-text clinical notes with standard tokens (`[NAME]`, `[LOCATION]`, `[FACILITY]`, `[DATE]`, `[CONTACT]`).
   - De-identified row committed to `ANALYTICS_SCRUBBED`.

3. **Query & Audit Transaction**:
   - Researcher queries `ANALYTICS_SCRUBBED`.
   - Action, execution latency (<0.5ms), user credentials, and network IP are automatically appended to `AUDIT_TRAIL_LOG`.
