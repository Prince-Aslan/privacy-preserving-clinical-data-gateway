import os
import time
from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.schemas import (
    ClinicalRecordIngestRequest, IngestionResponse, UserLogin, Token, TokenData, UserRole
)
from app.security.auth import (
    MOCK_USERS, verify_password, create_access_token, get_current_user, RoleChecker
)
from app.security.crypto import crypto_engine
from app.services.ner_service import ner_engine
from app.services.db_service import db_service
from app.simulator.generator import generate_synthetic_record

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Privacy-Preserving Clinical Data Gateway REST API for Mental Health Systems (NDPA 2023 Compliant)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 1. Authentication Endpoints
# -----------------------------------------------------------------------------
@app.post(f"{settings.API_V1_STR}/auth/login", response_model=Token, tags=["Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = MOCK_USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return Token(access_token=access_token, token_type="bearer", role=user["role"], username=user["username"])

@app.post(f"{settings.API_V1_STR}/auth/login_json", response_model=Token, tags=["Authentication"])
def login_json(credentials: UserLogin):
    user = MOCK_USERS.get(credentials.username)
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return Token(access_token=access_token, token_type="bearer", role=user["role"], username=user["username"])


# -----------------------------------------------------------------------------
# 2. Clinical Data Ingestion Endpoint (Clinicians & Admins)
# -----------------------------------------------------------------------------
@app.post(f"{settings.API_V1_STR}/ingest", response_model=IngestionResponse, tags=["Clinical Gateway"])
def ingest_clinical_record(
    payload: ClinicalRecordIngestRequest,
    request: Request,
    current_user: TokenData = Depends(RoleChecker([UserRole.CLINICIAN, UserRole.ADMIN]))
):
    start_time = time.time()
    
    # 1. Cryptographic Pseudonymization & AES-256 Field Encryption
    pseudonym_id = crypto_engine.hash_sha256(payload.patient_id)
    encrypted_name = crypto_engine.encrypt_field(payload.pii.patient_name)
    encrypted_contact = crypto_engine.encrypt_field(payload.pii.contact_info)

    processed_count = 0
    raw_vault_ok = True
    analytics_scrubbed_ok = True

    for visit in payload.journey_timeline:
        visit_ts = visit.timestamp.isoformat() + "Z" if isinstance(visit.timestamp, datetime_type) else str(visit.timestamp)
        
        # 2. Populate RAW_VAULT (Restricted Source of Truth)
        vault_entry = {
            "patient_pseudonym_id": pseudonym_id,
            "encrypted_name": encrypted_name,
            "encrypted_contact": encrypted_contact,
            "age": payload.demographics.age,
            "gender": payload.demographics.gender,
            "location": payload.demographics.location,
            "timestamp": visit_ts,
            "phq9_score": visit.phq9_score,
            "diagnosis": visit.diagnosis,
            "treatment_plan": [t.dict() for t in visit.treatment_plan],
            "raw_clinical_notes": visit.clinical_notes
        }
        rec_id = db_service.insert_raw_vault(vault_entry)

        # 3. spaCy Medical NER PHI Redaction Engine
        scrubbed_notes = ner_engine.redact_text(visit.clinical_notes)

        # 4. Populate ANALYTICS_SCRUBBED (De-identified Analytics Repository)
        analytics_entry = {
            "record_id": rec_id,
            "patient_pseudonym_id": pseudonym_id,
            "age": payload.demographics.age,
            "gender": payload.demographics.gender,
            "location": payload.demographics.location,
            "timestamp": visit_ts,
            "phq9_score": visit.phq9_score,
            "diagnosis": visit.diagnosis,
            "treatment_plan": [t.dict() for t in visit.treatment_plan],
            "scrubbed_clinical_notes": scrubbed_notes
        }
        db_service.insert_analytics_scrubbed(analytics_entry)
        processed_count += 1

    elapsed_ms = (time.time() - start_time) * 1000

    # 5. Audit Logging
    db_service.log_audit_trail(
        user_id=current_user.username,
        user_role=current_user.role,
        action_type="INGESTION",
        target_table="DUAL_DATABASE",
        query_string=f"Ingested record patient_id={payload.patient_id} with {processed_count} visits",
        ip_address=request.client.host if request.client else "127.0.0.1",
        execution_time_ms=elapsed_ms,
        status="SUCCESS"
    )

    return IngestionResponse(
        status="success",
        patient_pseudonym_id=pseudonym_id,
        records_processed=processed_count,
        raw_vault_inserted=raw_vault_ok,
        analytics_scrubbed_inserted=analytics_scrubbed_ok
    )

# Auxiliary datetime type check helper
from datetime import datetime as datetime_type

# -----------------------------------------------------------------------------
# 3. Query Scrubbed Analytics Repository (Researchers, Clinicians, Admins)
# -----------------------------------------------------------------------------
@app.get(f"{settings.API_V1_STR}/query/analytics", tags=["Data Analytics"])
def query_analytics_repository(
    limit: int = 100,
    request: Request = None,
    current_user: TokenData = Depends(RoleChecker([UserRole.RESEARCHER, UserRole.CLINICIAN, UserRole.DATA_OFFICER, UserRole.ADMIN]))
):
    start_time = time.time()
    records = db_service.query_analytics_scrubbed(limit=limit)
    elapsed_ms = (time.time() - start_time) * 1000

    db_service.log_audit_trail(
        user_id=current_user.username,
        user_role=current_user.role,
        action_type="QUERY",
        target_table="ANALYTICS_SCRUBBED",
        query_string=f"SELECT * FROM ANALYTICS_SCRUBBED LIMIT {limit}",
        ip_address=request.client.host if request and request.client else "127.0.0.1",
        execution_time_ms=elapsed_ms,
        status="SUCCESS"
    )
    return {"status": "success", "count": len(records), "data": records}

# -----------------------------------------------------------------------------
# 4. Query Restricted RAW_VAULT Repository (Admins & Data Officers Only)
# -----------------------------------------------------------------------------
@app.get(f"{settings.API_V1_STR}/query/vault", tags=["Restricted Vault"])
def query_raw_vault(
    limit: int = 100,
    request: Request = None,
    current_user: TokenData = Depends(RoleChecker([UserRole.ADMIN, UserRole.DATA_OFFICER]))
):
    start_time = time.time()
    records = db_service.query_raw_vault(limit=limit)
    elapsed_ms = (time.time() - start_time) * 1000

    db_service.log_audit_trail(
        user_id=current_user.username,
        user_role=current_user.role,
        action_type="QUERY_VAULT",
        target_table="RAW_VAULT",
        query_string=f"SELECT * FROM RAW_VAULT LIMIT {limit}",
        ip_address=request.client.host if request and request.client else "127.0.0.1",
        execution_time_ms=elapsed_ms,
        status="SUCCESS"
    )
    return {"status": "success", "count": len(records), "data": records}

# -----------------------------------------------------------------------------
# 5. Audit Trail Logs (Admins & Data Officers Only)
# -----------------------------------------------------------------------------
@app.get(f"{settings.API_V1_STR}/audit", tags=["Compliance Audit"])
def get_audit_trail_logs(
    limit: int = 100,
    current_user: TokenData = Depends(RoleChecker([UserRole.ADMIN, UserRole.DATA_OFFICER]))
):
    logs = db_service.get_audit_trail(limit=limit)
    return {"status": "success", "count": len(logs), "audit_logs": logs}

# -----------------------------------------------------------------------------
# 6. Simulator Seeding Endpoint (Admins Only)
# -----------------------------------------------------------------------------
@app.post(f"{settings.API_V1_STR}/simulator/seed", tags=["Data Simulator"])
def seed_synthetic_records(
    count: int = 50,
    current_user: TokenData = Depends(RoleChecker([UserRole.ADMIN]))
):
    from app.pipeline.dagster_pipeline import run_pipeline_manually
    vault_cnt, analytics_cnt = run_pipeline_manually(count=count)
    return {
        "status": "success",
        "records_generated": count,
        "raw_vault_inserted": vault_cnt,
        "analytics_scrubbed_inserted": analytics_cnt
    }

# -----------------------------------------------------------------------------
# 7. System Health Check & Analytics Summary
# -----------------------------------------------------------------------------
@app.get(f"{settings.API_V1_STR}/analytics/summary", tags=["Data Analytics"])
def get_analytics_summary_data(
    current_user: TokenData = Depends(RoleChecker([UserRole.RESEARCHER, UserRole.CLINICIAN, UserRole.DATA_OFFICER, UserRole.ADMIN]))
):
    summary = db_service.get_analytics_summary()
    return {"status": "success", "summary": summary}

@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "healthy",
        "gateway": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "clickhouse_status": "connected" if db_service.client else "in_memory_mode"
    }

# -----------------------------------------------------------------------------
# 8. Mount Full-Stack Web Frontend UI
# -----------------------------------------------------------------------------
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

