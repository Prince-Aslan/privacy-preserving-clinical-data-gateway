from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# -----------------------------------------------------------------------------
# 1. Ingestion Schemas (JSON Payload)
# -----------------------------------------------------------------------------
class DirectPII(BaseModel):
    patient_name: str = Field(..., example="Prince Okwuchukwu")
    contact_info: str = Field(..., example="+234-803-123-4567")

class Demographics(BaseModel):
    age: int = Field(..., ge=0, le=120, example=28)
    gender: str = Field(..., example="Female")
    location: str = Field(..., example="Lagos, Nigeria")

class TreatmentItem(BaseModel):
    type: str = Field(..., example="Medication")
    name: str = Field(..., example="Sertraline")
    dosage: Optional[str] = Field(None, example="50mg")

class JourneyEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    phq9_score: int = Field(..., ge=0, le=27, example=18)
    clinical_notes: str = Field(..., example="Patient reports severe insomnia and low energy. Patient's name is Chidi living in Ikeja.")
    diagnosis: str = Field(..., example="Major Depressive Disorder (Moderate)")
    treatment_plan: List[TreatmentItem] = Field(default_factory=list)

class ClinicalRecordIngestRequest(BaseModel):
    patient_id: str = Field(..., example="SYN-992-X")
    pii: DirectPII
    demographics: Demographics
    journey_timeline: List[JourneyEntry]

# -----------------------------------------------------------------------------
# 2. Authentication & User Schemas
# -----------------------------------------------------------------------------
class UserRole(str):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    DATA_OFFICER = "data_officer"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# -----------------------------------------------------------------------------
# 3. Response Schemas
# -----------------------------------------------------------------------------
class IngestionResponse(BaseModel):
    status: str = "success"
    patient_pseudonym_id: str
    records_processed: int
    raw_vault_inserted: bool
    analytics_scrubbed_inserted: bool

class AnalyticsRecord(BaseModel):
    record_id: str
    patient_pseudonym_id: str
    age: int
    gender: str
    location: str
    timestamp: str
    phq9_score: int
    diagnosis: str
    treatment_plan: str
    scrubbed_clinical_notes: str

class VaultRecord(BaseModel):
    record_id: str
    patient_pseudonym_id: str
    encrypted_name: str
    encrypted_contact: str
    age: int
    gender: str
    location: str
    timestamp: str
    phq9_score: int
    diagnosis: str
    treatment_plan: str
    raw_clinical_notes: str

class AuditTrailItem(BaseModel):
    log_id: str
    user_id: str
    user_role: str
    action_type: str
    target_table: str
    query_string: str
    ip_address: str
    execution_time_ms: float
    status: str
    timestamp: str
