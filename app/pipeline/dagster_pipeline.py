import time
from dagster import asset, Definitions
from app.simulator.generator import generate_synthetic_record
from app.security.crypto import crypto_engine
from app.services.ner_service import ner_engine
from app.services.db_service import db_service

@asset(description="Ingest raw clinical JSON records (High-Risk Ingestion Asset)")
def raw_clinical_records():
    """Generates or fetches raw JSON clinical records with PII."""
    raw_records = [generate_synthetic_record(i) for i in range(10)]
    return raw_records

@asset(description="AES-256 Field Encryption & SHA-256 Pseudonymization Asset (RAW_VAULT Population)")
def encrypted_vault_records(raw_clinical_records):
    """Encrypts PII with AES-256 and hashes patient ID with SHA-256 for RAW_VAULT."""
    vault_entries = []
    for record in raw_clinical_records:
        pseudonym_id = crypto_engine.hash_sha256(record["patient_id"])
        enc_name = crypto_engine.encrypt_field(record["pii"]["patient_name"])
        enc_contact = crypto_engine.encrypt_field(record["pii"]["contact_info"])

        for visit in record["journey_timeline"]:
            entry = {
                "patient_pseudonym_id": pseudonym_id,
                "encrypted_name": enc_name,
                "encrypted_contact": enc_contact,
                "age": record["demographics"]["age"],
                "gender": record["demographics"]["gender"],
                "location": record["demographics"]["location"],
                "timestamp": visit["timestamp"],
                "phq9_score": visit["phq9_score"],
                "diagnosis": visit["diagnosis"],
                "treatment_plan": visit["treatment_plan"],
                "raw_clinical_notes": visit["clinical_notes"]
            }
            record_id = db_service.insert_raw_vault(entry)
            entry["record_id"] = record_id
            vault_entries.append(entry)
    return vault_entries

@asset(description="spaCy Medical NER PHI Redaction Asset (ANALYTICS_SCRUBBED Population)")
def deidentified_analytics_records(encrypted_vault_records):
    """Applies spaCy NER PHI redaction to free-text clinical notes and populates ANALYTICS_SCRUBBED."""
    analytics_entries = []
    for entry in encrypted_vault_records:
        scrubbed_notes = ner_engine.redact_text(entry["raw_clinical_notes"])
        analytics_entry = {
            "record_id": entry["record_id"],
            "patient_pseudonym_id": entry["patient_pseudonym_id"],
            "age": entry["age"],
            "gender": entry["gender"],
            "location": entry["location"],
            "timestamp": entry["timestamp"],
            "phq9_score": entry["phq9_score"],
            "diagnosis": entry["diagnosis"],
            "treatment_plan": entry["treatment_plan"],
            "scrubbed_clinical_notes": scrubbed_notes
        }
        db_service.insert_analytics_scrubbed(analytics_entry)
        analytics_entries.append(analytics_entry)
    return analytics_entries

defs = Definitions(
    assets=[raw_clinical_records, encrypted_vault_records, deidentified_analytics_records]
)

def run_pipeline_manually(count: int = 10):
    start_time = time.time()
    raw = [generate_synthetic_record(i) for i in range(count)]
    vault_entries = []
    analytics_entries = []

    for record in raw:
        pseudonym_id = crypto_engine.hash_sha256(record["patient_id"])
        enc_name = crypto_engine.encrypt_field(record["pii"]["patient_name"])
        enc_contact = crypto_engine.encrypt_field(record["pii"]["contact_info"])

        for visit in record["journey_timeline"]:
            vault_entry = {
                "patient_pseudonym_id": pseudonym_id,
                "encrypted_name": enc_name,
                "encrypted_contact": enc_contact,
                "age": record["demographics"]["age"],
                "gender": record["demographics"]["gender"],
                "location": record["demographics"]["location"],
                "timestamp": visit["timestamp"],
                "phq9_score": visit["phq9_score"],
                "diagnosis": visit["diagnosis"],
                "treatment_plan": visit["treatment_plan"],
                "raw_clinical_notes": visit["clinical_notes"]
            }
            rec_id = db_service.insert_raw_vault(vault_entry)

            scrubbed_notes = ner_engine.redact_text(visit["clinical_notes"])
            analytics_entry = {
                "record_id": rec_id,
                "patient_pseudonym_id": pseudonym_id,
                "age": record["demographics"]["age"],
                "gender": record["demographics"]["gender"],
                "location": record["demographics"]["location"],
                "timestamp": visit["timestamp"],
                "phq9_score": visit["phq9_score"],
                "diagnosis": visit["diagnosis"],
                "treatment_plan": visit["treatment_plan"],
                "scrubbed_clinical_notes": scrubbed_notes
            }
            db_service.insert_analytics_scrubbed(analytics_entry)

            vault_entries.append(vault_entry)
            analytics_entries.append(analytics_entry)

    elapsed = (time.time() - start_time) * 1000
    db_service.log_audit_trail(
        user_id="dagster_pipeline_service",
        user_role="admin",
        action_type="PIPELINE_TRANSFORMATION",
        target_table="DUAL_DATABASE",
        query_string=f"Processed {len(raw)} records into RAW_VAULT and ANALYTICS_SCRUBBED",
        ip_address="127.0.0.1",
        execution_time_ms=elapsed,
        status="SUCCESS"
    )
    return len(vault_entries), len(analytics_entries)
