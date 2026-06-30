import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class IngestionAgent(Agent):
    def __init__(self):
        super().__init__("ingest")
        
    def normalize_record(self, raw_data: dict) -> dict:
        """Calls ecochain.ingest.normalize_record to normalize incoming data."""
        self.log_action("normalize_attempt", {"supplier_id": raw_data.get("supplier_id")})
        res = self.call_tool("ecochain.ingest.normalize_record", {"data": raw_data})
        if res.get("status") == "success":
            record = res["record"]
            
            # Write to database
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO activity_records 
                (record_id, supplier_id, data_source, data_quality, confidence_score, ingested_at, activity_type, quantity, unit, country, period, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["record_id"],
                    record["supplier_id"],
                    record["data_source"],
                    record["data_quality"],
                    record["confidence_score"],
                    record["ingested_at"],
                    record["activity_type"],
                    record["quantity"],
                    record["unit"],
                    record["country"],
                    record["period"],
                    record["details"]
                )
            )
            conn.commit()
            conn.close()
            
            self.log_action("normalize_success", {"record_id": record["record_id"], "supplier_id": record["supplier_id"]})
            return record
        else:
            self.log_action("normalize_failure", {"error": res.get("message")})
            raise ValueError(f"Normalization failed: {res.get('message')}")

    def ingest_document(self, doc_path: str) -> dict:
        """Parses a document, normalizes, and quarantines if parse confidence is low."""
        self.log_action("parse_document_attempt", {"doc_path": doc_path})
        res = self.call_tool("ecochain.ingest.parse_document", {"doc_path": doc_path})
        
        if res.get("status") == "success":
            parsed_data = res["parsed_data"]
            confidence = parsed_data.get("confidence_score", 1.0)
            
            if confidence < 0.75:
                # Quarantine the record
                self.log_action("parse_quarantine", {
                    "doc_path": doc_path,
                    "confidence": confidence,
                    "reason": "Document parse confidence below 0.75 threshold"
                })
                # Dispatch an alert to compliance team
                self.call_tool("ecochain.alert.dispatch", {
                    "supplier_id": parsed_data.get("supplier_id"),
                    "severity": "WARNING",
                    "message": f"Document parse confidence {confidence:.2f} for {doc_path} is below 0.75 threshold. Record quarantined.",
                    "channel": "email"
                })
                return {"status": "quarantined", "confidence": confidence, "doc_path": doc_path}
            
            # If good confidence, normalize and store
            normalized = self.normalize_record(parsed_data)
            return {"status": "success", "record": normalized}
        else:
            self.log_action("parse_document_failure", {"doc_path": doc_path, "error": res.get("message")})
            return {"status": "failed", "error": res.get("message")}

    def check_overdue_submissions(self, active_suppliers: list, current_period: str):
        """Scans for expected submissions and alerts if missing."""
        self.log_action("check_overdue_start", {"period": current_period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        missing_suppliers = []
        for supplier in active_suppliers:
            supplier_id = supplier.get("supplier_id")
            name = supplier.get("name")
            
            # Check if we have an activity record for this supplier and period
            cursor.execute(
                "SELECT COUNT(*) FROM activity_records WHERE supplier_id = ? AND period = ?",
                (supplier_id, current_period)
            )
            count = cursor.fetchone()[0]
            if count == 0:
                missing_suppliers.append((supplier_id, name))
        conn.close()

        for supplier_id, name in missing_suppliers:
            self.log_action("missing_submission_detected", {"supplier_id": supplier_id, "period": current_period})
            # Write a placeholder missing data record
            conn = get_connection()
            cursor = conn.cursor()
            placeholder_id = f"rec_missing_{supplier_id}_{current_period}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO activity_records 
                (record_id, supplier_id, data_source, data_quality, confidence_score, ingested_at, activity_type, quantity, unit, country, period, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    placeholder_id,
                    supplier_id,
                    "system_scheduler",
                    "missing",
                    0.0,
                    datetime.utcnow().isoformat() + "Z",
                    "unknown",
                    0.0,
                    "N/A",
                    "US",
                    current_period,
                    json.dumps({"reason": "overdue_submission"})
                )
            )
            conn.commit()
            conn.close()
            
            # Trigger warning alert
            self.call_tool("ecochain.alert.dispatch", {
                "supplier_id": supplier_id,
                "severity": "WARNING",
                "message": f"Expected carbon disclosure data from supplier {name} for period {current_period} is overdue.",
                "channel": "email"
            })
