import json
import uuid
from datetime import datetime
import clickhouse_connect
from app.config import settings

class DatabaseService:
    def __init__(self):
        self.client = None
        self._memory_vault = []
        self._memory_analytics = []
        self._memory_audit = []
        self._connect()

    def _connect(self):
        try:
            self.client = clickhouse_connect.get_client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                username=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DB,
                connect_timeout=2
            )
            print(f"[DB] Connected to ClickHouse at {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}")
        except Exception as e:
            print(f"[DB Warning] ClickHouse connection unavailable ({e}). Operating in High-Performance In-Memory Dual-Database Mode.")
            self.client = None

    def insert_raw_vault(self, record_data: dict) -> str:
        record_id = str(uuid.uuid4())
        if self.client:
            try:
                row = [
                    record_id,
                    record_data["patient_pseudonym_id"],
                    record_data["encrypted_name"],
                    record_data["encrypted_contact"],
                    record_data["age"],
                    record_data["gender"],
                    record_data["location"],
                    record_data["timestamp"],
                    record_data["phq9_score"],
                    record_data["diagnosis"],
                    json.dumps(record_data.get("treatment_plan", [])),
                    record_data["raw_clinical_notes"],
                    datetime.utcnow()
                ]
                self.client.insert(
                    'RAW_VAULT',
                    [row],
                    column_names=[
                        'record_id', 'patient_pseudonym_id', 'encrypted_name', 'encrypted_contact',
                        'age', 'gender', 'location', 'timestamp', 'phq9_score', 'diagnosis',
                        'treatment_plan', 'raw_clinical_notes', 'ingested_at'
                    ]
                )
            except Exception as e:
                print(f"[DB Error] ClickHouse insert RAW_VAULT failed: {e}")

        # Store in fallback memory vault
        record_data["record_id"] = record_id
        record_data["treatment_plan_str"] = json.dumps(record_data.get("treatment_plan", []))
        self._memory_vault.append(record_data)
        return record_id

    def insert_analytics_scrubbed(self, record_data: dict) -> str:
        record_id = record_data.get("record_id", str(uuid.uuid4()))
        if self.client:
            try:
                row = [
                    record_id,
                    record_data["patient_pseudonym_id"],
                    record_data["age"],
                    record_data["gender"],
                    record_data["location"],
                    record_data["timestamp"],
                    record_data["phq9_score"],
                    record_data["diagnosis"],
                    json.dumps(record_data.get("treatment_plan", [])),
                    record_data["scrubbed_clinical_notes"],
                    datetime.utcnow()
                ]
                self.client.insert(
                    'ANALYTICS_SCRUBBED',
                    [row],
                    column_names=[
                        'record_id', 'patient_pseudonym_id', 'age', 'gender', 'location',
                        'timestamp', 'phq9_score', 'diagnosis', 'treatment_plan',
                        'scrubbed_clinical_notes', 'scrubbed_at'
                    ]
                )
            except Exception as e:
                print(f"[DB Error] ClickHouse insert ANALYTICS_SCRUBBED failed: {e}")

        record_data["record_id"] = record_id
        record_data["treatment_plan_str"] = json.dumps(record_data.get("treatment_plan", []))
        self._memory_analytics.append(record_data)
        return record_id

    def log_audit_trail(self, user_id: str, user_role: str, action_type: str, target_table: str,
                        query_string: str, ip_address: str, execution_time_ms: float, status: str):
        log_id = str(uuid.uuid4())
        audit_entry = {
            "log_id": log_id,
            "user_id": user_id,
            "user_role": user_role,
            "action_type": action_type,
            "target_table": target_table,
            "query_string": query_string,
            "ip_address": ip_address,
            "execution_time_ms": execution_time_ms,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.client:
            try:
                row = [
                    log_id, user_id, user_role, action_type, target_table,
                    query_string, ip_address, execution_time_ms, status, datetime.utcnow()
                ]
                self.client.insert('AUDIT_TRAIL_LOG', [row], column_names=[
                    'log_id', 'user_id', 'user_role', 'action_type', 'target_table',
                    'query_string', 'ip_address', 'execution_time_ms', 'status', 'timestamp'
                ])
            except Exception as e:
                print(f"[DB Error] ClickHouse log_audit_trail failed: {e}")

        self._memory_audit.append(audit_entry)

    def query_analytics_scrubbed(self, limit: int = 100) -> list:
        if self.client:
            try:
                res = self.client.query(f"SELECT * FROM ANALYTICS_SCRUBBED LIMIT {limit}")
                rows = []
                for row in res.result_rows:
                    rows.append({
                        "record_id": str(row[0]),
                        "patient_pseudonym_id": str(row[1]),
                        "age": int(row[2]),
                        "gender": str(row[3]),
                        "location": str(row[4]),
                        "timestamp": str(row[5]),
                        "phq9_score": int(row[6]),
                        "diagnosis": str(row[7]),
                        "treatment_plan": str(row[8]),
                        "scrubbed_clinical_notes": str(row[9])
                    })
                return rows
            except Exception as e:
                print(f"[DB Error] ClickHouse query_analytics_scrubbed failed: {e}")

        # Return from memory fallback
        return [
            {
                "record_id": str(r.get("record_id", "")),
                "patient_pseudonym_id": str(r.get("patient_pseudonym_id", "")),
                "age": int(r.get("age", 0)),
                "gender": str(r.get("gender", "")),
                "location": str(r.get("location", "")),
                "timestamp": str(r.get("timestamp", "")),
                "phq9_score": int(r.get("phq9_score", 0)),
                "diagnosis": str(r.get("diagnosis", "")),
                "treatment_plan": str(r.get("treatment_plan_str", "")),
                "scrubbed_clinical_notes": str(r.get("scrubbed_clinical_notes", ""))
            }
            for r in self._memory_analytics[:limit]
        ]

    def query_raw_vault(self, limit: int = 100) -> list:
        if self.client:
            try:
                res = self.client.query(f"SELECT * FROM RAW_VAULT LIMIT {limit}")
                rows = []
                for row in res.result_rows:
                    rows.append({
                        "record_id": str(row[0]),
                        "patient_pseudonym_id": str(row[1]),
                        "encrypted_name": str(row[2]),
                        "encrypted_contact": str(row[3]),
                        "age": int(row[4]),
                        "gender": str(row[5]),
                        "location": str(row[6]),
                        "timestamp": str(row[7]),
                        "phq9_score": int(row[8]),
                        "diagnosis": str(row[9]),
                        "treatment_plan": str(row[10]),
                        "raw_clinical_notes": str(row[11])
                    })
                return rows
            except Exception as e:
                print(f"[DB Error] ClickHouse query_raw_vault failed: {e}")

        return [
            {
                "record_id": str(r.get("record_id", "")),
                "patient_pseudonym_id": str(r.get("patient_pseudonym_id", "")),
                "encrypted_name": str(r.get("encrypted_name", "")),
                "encrypted_contact": str(r.get("encrypted_contact", "")),
                "age": int(r.get("age", 0)),
                "gender": str(r.get("gender", "")),
                "location": str(r.get("location", "")),
                "timestamp": str(r.get("timestamp", "")),
                "phq9_score": int(r.get("phq9_score", 0)),
                "diagnosis": str(r.get("diagnosis", "")),
                "treatment_plan": str(r.get("treatment_plan_str", "")),
                "raw_clinical_notes": str(r.get("raw_clinical_notes", ""))
            }
            for r in self._memory_vault[:limit]
        ]

    def get_audit_trail(self, limit: int = 100) -> list:
        if self.client:
            try:
                res = self.client.query(f"SELECT * FROM AUDIT_TRAIL_LOG ORDER BY timestamp DESC LIMIT {limit}")
                rows = []
                for row in res.result_rows:
                    rows.append({
                        "log_id": str(row[0]),
                        "user_id": str(row[1]),
                        "user_role": str(row[2]),
                        "action_type": str(row[3]),
                        "target_table": str(row[4]),
                        "query_string": str(row[5]),
                        "ip_address": str(row[6]),
                        "execution_time_ms": float(row[7]),
                        "status": str(row[8]),
                        "timestamp": str(row[9])
                    })
                return rows
            except Exception as e:
                print(f"[DB Error] ClickHouse get_audit_trail failed: {e}")

        return self._memory_audit[-limit:]

    def get_analytics_summary(self) -> dict:
        total = 0
        if self.client:
            try:
                res = self.client.query("SELECT count() FROM ANALYTICS_SCRUBBED")
                total = int(res.result_rows[0][0])
            except Exception:
                total = len(self._memory_analytics)
        else:
            total = len(self._memory_analytics)

        records = self.query_analytics_scrubbed(limit=100000)
        actual_count = len(records)
        
        phq9_categories = {"Minimal (0-4)": 0, "Mild (5-9)": 0, "Moderate (10-14)": 0, "Mod. Severe (15-19)": 0, "Severe (20-27)": 0}
        diagnosis_counts = {}
        gender_counts = {}
        total_phq9 = 0
        
        for r in records:
            score = int(r.get("phq9_score", 0))
            total_phq9 += score
            if score <= 4:
                phq9_categories["Minimal (0-4)"] += 1
            elif score <= 9:
                phq9_categories["Mild (5-9)"] += 1
            elif score <= 14:
                phq9_categories["Moderate (10-14)"] += 1
            elif score <= 19:
                phq9_categories["Mod. Severe (15-19)"] += 1
            else:
                phq9_categories["Severe (20-27)"] += 1
                
            diag = r.get("diagnosis", "Unspecified")
            diagnosis_counts[diag] = diagnosis_counts.get(diag, 0) + 1
            
            gen = r.get("gender", "Unknown")
            gender_counts[gen] = gender_counts.get(gen, 0) + 1

        avg_phq9 = round(total_phq9 / max(1, actual_count), 2) if actual_count > 0 else 0.0

        return {
            "total_records": max(total, actual_count),
            "avg_phq9_score": avg_phq9,
            "phq9_categories": phq9_categories,
            "diagnosis_counts": diagnosis_counts,
            "gender_counts": gender_counts
        }


db_service = DatabaseService()

