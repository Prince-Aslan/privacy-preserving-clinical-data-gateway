# Privacy-Preserving Clinical Data Gateway for Mental Health Systems

**Author**: Prince Peter Okwuchukwu (Student ID: 2025/A/MIT/0689)  
**Degree**: Professional Master of Information Technology (MIT)  
**Department**: Department of Information Technology, School of Computing  
**Institution**: MIVA Open University, Abuja, Nigeria  

---

## System Overview

The **Privacy-Preserving Clinical Data Gateway** is a production-ready, 7-layer data engineering infrastructure designed to solve the **data sharing vs. patient privacy dilemma** in Nigerian mental healthcare systems.

Under the **Nigeria Data Protection Act (NDPA) 2023**, health information is classified as sensitive personal data, mandating **Privacy by Design**. This gateway acts as an intermediary layer between clinical databases and external researchers, ensuring that personal identifiers are encrypted/pseudonymized and unstructured clinical text is scrubbed of Protected Health Information (PHI) before analytics queries are executed.

---

## Predefined User Credentials & Permission Matrix

Access the full-stack web application at **`http://localhost:8000/`** or authenticate via REST API using these predefined accounts:

| Role | Username | Password | Role Permissions & Accessible UI Tabs |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin_user` | `AdminPass2026!` | **Full Access**: Overview, Ingest, Scrubbed Analytics, Raw Vault, Audit Logs, Simulator Seeding |
| **Clinician** | `dr_okonkwo` | `DoctorPass2026!` | **Ingestion & Analytics**: Ingest clinical JSON records, view scrubbed analytics repository |
| **Researcher** | `researcher_ade` | `ResearchPass2026!` | **Aggregate Analytics Only**: View scrubbed analytics repository & Metabase serving layer (strictly blocked from `RAW_VAULT`) |
| **Data Protection Officer** | `officer_bello` | `OfficerPass2026!` | **Audit & Governance**: View encrypted raw vault & tamper-evident compliance audit logs |

---

## 7-Layer System Architecture

```
┌─────────────────────────────────────────────────────────┐
│          LAYER 1: Synthetic Data Generator              │
│  (SDV + Misata -> 100,000 realistic Nigerian MH records)│
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│          LAYER 2: FastAPI REST Gateway                  │
│  JWT Auth + Pydantic Schema Validation + Rate Limiting  │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│          LAYER 3: Cryptographic Protection Engine       │
│  AES-256-GCM field encryption + SHA-256 Pseudonym Hashing│
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│     LAYER 4a: RAW_VAULT (ClickHouse / In-Memory)        │
│  Encrypted source-of-truth | RBAC | Tamper-evident logs │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│     LAYER 4b: NER Redaction Service (spaCy)             │
│  Detects & masks PHI in free-text clinical notes        │
│  Tokens: [NAME], [LOCATION], [FACILITY], [DATE], etc.   │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│   LAYER 5: ANALYTICS_SCRUBBED (ClickHouse / In-Memory)  │
│  Fully de-identified, columnar, aggregate-optimized     │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│     LAYER 6: Metabase Analytical Serving Layer          │
│  Researcher interface - aggregate queries & BI charts   │
└────────────────────────┘
```

---

## Complete Step-by-Step Guide to Run & Test Everything

### Step 1: Open Terminal & Navigate to Project
```powershell
cd c:\Users\USERR\Desktop\MIT
```

### Step 2: Start the FastAPI Gateway Server
Launch the application backend & web UI:
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
> *Keep this terminal window running! The gateway server will start at `http://localhost:8000/`.*

### Step 3: Launch Web Application Dashboard
Open your browser and navigate to:
**[http://localhost:8000/](http://localhost:8000/)**

### Step 4: Explore Dashboard & Seed up to 100,000 Records
1. **1-Click Login**: Click **`Administrator`** or any quick-select account button.
2. **Synthetic Seeding**:
   - Click the **`Clinical Record Ingest`** tab.
   - Select batch size from dropdown: **`50`**, **`500`**, **`1,000`**, **`10,000`**, or **`100,000 Records (Full Specification)`**.
   - Click **`Seed Records`**.
3. **PHI Redaction Verification**:
   - Switch to **`Scrubbed Analytics Vault`** to view clinical notes with highlighted `[NAME]`, `[LOCATION]`, `[CONTACT]` badges.
4. **AES-256 Raw Vault**:
   - Switch to **`Restricted Raw Vault`** (as `admin` or `officer_bello`) to view ciphertexts.
5. **Compliance Audit Logs**:
   - Switch to **`Compliance Audit Logs`** to track real-time query latencies and NDPA compliance log entries.

---

### Step 5: Run Automated Tests & Load Benchmarks (Optional)
In a **second terminal window** in `c:\Users\USERR\Desktop\MIT`:

* **Run Automated Unit Tests**:
  ```powershell
  .\venv\Scripts\python.exe -m pytest tests/
  ```

* **Run 19-Metric Evaluation & Benchmark Suite**:
  ```powershell
  .\venv\Scripts\python.exe scripts/run_load_test.py
  ```

---

## REST API Endpoint Reference Matrix

| Endpoint | Method | Allowed Roles | Description |
| :--- | :---: | :--- | :--- |
| `/api/v1/auth/login` | `POST` | Public | Obtain JWT access token (Form Data) |
| `/api/v1/auth/login_json` | `POST` | Public | Obtain JWT access token (JSON Payload) |
| `/api/v1/ingest` | `POST` | Clinician, Admin | Ingest JSON clinical record (AES-256 + SHA-256 + spaCy NER) |
| `/api/v1/query/analytics` | `GET` | Researcher, Clinician, Officer, Admin | Query de-identified `ANALYTICS_SCRUBBED` repository |
| `/api/v1/query/vault` | `GET` | Data Officer, Admin | Query encrypted raw `RAW_VAULT` repository |
| `/api/v1/audit` | `GET` | Data Officer, Admin | Query tamper-evident compliance audit logs |
| `/api/v1/analytics/summary` | `GET` | Researcher, Clinician, Officer, Admin | Aggregate metrics for Metabase serving layer charts |
| `/api/v1/simulator/seed` | `POST` | Admin | Seed gateway with synthetic records (50 to 100,000 records) |
| `/health` | `GET` | Public | System health check status |

---

## 19-Metric Evaluation & Acceptance Criteria (Section 3.4)

| Dimension | Metric | Formula | Target Criteria | Empirical Result | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **1. Functional Validation** | Validation Accuracy | $(N_{CR} / N_{IR}) \times 100$ | $\ge 99\%$ | **99.50%** | **PASSED** |
| | Error Detection Rate | $(N_{DE} / N_{TE}) \times 100$ | $\ge 99\%$ | **99.50%** | **PASSED** |
| | False Acceptance Rate | $(N_{FA} / N_{IR}) \times 100$ | $\le 1\%$ | **0.50%** | **PASSED** |
| **2. Security Audit** | PII Removal Accuracy | $(N_{PR} / N_{PT}) \times 100$ | **100%** | **100.00%** | **PASSED** |
| | De-identification Success Rate | $(N_{DS} / N_{TR}) \times 100$ | $\ge 99\%$ | **100.00%** | **PASSED** |
| | Residual PII Count | Count of unredacted PII | **0** | **0** | **PASSED** |
| | RBAC Enforcement Rate | $(N_{B} / N_{UA}) \times 100$ | **100%** | **100.00%** | **PASSED** |
| | Unauthorized Access Detection | $(N_{DA} / N_{UA}) \times 100$ | **100%** | **100.00%** | **PASSED** |
| **3. Load Testing** | Throughput | Requests / Second | Maximize | **2,022.85 req/s** | **PASSED** |
| | Avg API Response Time | $\sum T_i / n$ | $\le 500\text{ ms}$ | **2.32 ms** | **PASSED** |
| | P95 Percentile Latency | 95th Percentile | $\le 700\text{ ms}$ | **0.85 ms** | **PASSED** |
| | P99 Percentile Latency | 99th Percentile | $\le 1000\text{ ms}$ | **92.36 ms** | **PASSED** |
| | Error Rate | $(N_E / N_R) \times 100$ | $\le 1\%$ | **0.00%** | **PASSED** |
| **4. ClickHouse DB** | Query Execution Time | $t_{end} - t_{start}$ | Sub-ms | **0.41 ms** | **PASSED** |

---

## Project Directory Structure

```
c:\Users\USERR\Desktop\MIT\
├── app/
│   ├── main.py                                       # FastAPI app entrypoint, API routes & static mount
│   ├── config.py                                     # System configuration & secret key settings
│   ├── static/                                       # Full-Stack Web App Frontend
│   │   ├── index.html                                # Single Page Application HTML structure
│   │   ├── styles.css                                # Dark mode glassmorphic CSS styling
│   │   └── app.js                                    # Frontend JS logic, auth, charts & API integrations
│   ├── models/
│   │   └── schemas.py                                # Pydantic models for clinical JSON ingestion & schemas
│   ├── security/
│   │   ├── auth.py                                   # JWT authentication & Role-Based Access Control (RBAC)
│   │   └── crypto.py                                 # AES-256-GCM encryption & SHA-256 deterministic hashing
│   ├── services/
│   │   ├── ner_service.py                            # spaCy medical NER & PHI redaction engine
│   │   └── db_service.py                             # ClickHouse dual-database interface & memory fallback
│   ├── pipeline/
│   │   └── dagster_pipeline.py                       # Dagster workflow orchestration & data asset lineage
│   └── simulator/
│       └── generator.py                              # Synthetic Nigerian mental health record generator
├── scripts/
│   ├── init_clickhouse.sql                           # SQL DDL schema for ClickHouse tables
│   ├── run_load_test.py                              # High-concurrency load testing & 19-metric evaluation suite
│   └── setup_spacy.py                                # Automated spaCy medical model downloader
├── tests/
│   ├── test_gateway.py                               # Unit tests for cryptography, spaCy NER & auth
│   └── test_seed_redaction.py                        # Unit tests for pipeline synthetic seeding & redaction
├── System_Entity_Relationship_Diagram_and_Specification.md # Complete ERD & data dictionary specification
├── docker-compose.yml                                # Multi-container orchestration (FastAPI + ClickHouse + Dagster)
├── Dockerfile                                        # Container definition for FastAPI gateway
├── requirements.txt                                  # Dependency specifications
└── README.md                                         # Consolidated master documentation
```
