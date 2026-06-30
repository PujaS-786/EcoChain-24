import json
import uuid
import hashlib
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class AnomalyDetectionAgent(Agent):
    def __init__(self):
        super().__init__("anomaly")
        
    def check_anomalies(self, supplier_id: str, period: str) -> list:
        """Runs checks across categories: statistical patterns, integrity issues, and disclosure trends."""
        self.log_action("anomaly_check_start", {"supplier_id": supplier_id, "period": period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Fetch current emissions for checking
        cursor.execute("""
            SELECT e.record_id, e.co2e, e.confidence_score, a.activity_type, a.quantity, a.details
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            WHERE e.supplier_id = ? AND a.period = ?
        """, (supplier_id, period))
        current_records = cursor.fetchall()
        
        anomalies_detected = []
        
        # Fetch historical average baseline
        cursor.execute("""
            SELECT AVG(co2e) FROM emissions_records 
            WHERE supplier_id = ? AND record_id NOT IN (
                SELECT record_id FROM activity_records WHERE period = ?
            )
        """, (supplier_id, period))
        hist_avg_row = cursor.fetchone()
        hist_avg = hist_avg_row[0] if hist_avg_row and hist_avg_row[0] is not None else None
        
        for rec in current_records:
            rec_id, co2e, confidence, act_type, quantity, details_str = rec
            details = json.loads(details_str) if details_str else {}
            
            # Category 1: Statistical patterns (e.g., consumption > 25% deviation from baseline)
            if hist_avg is not None and hist_avg > 0:
                deviation = abs(co2e - hist_avg) / hist_avg
                if deviation > 0.25:
                    anom_hash = hashlib.md5(f"statistical_{rec_id}_{supplier_id}_{period}".encode('utf-8')).hexdigest()[:12]
                    anomaly_id = f"anm_{anom_hash}"
                    desc = f"Emissions deviation of {deviation:.1%} from historical rolling average ({co2e:.1f} tons vs baseline {hist_avg:.1f} tons)."
                    severity = "CRITICAL" if deviation > 0.50 else "WARNING"
                    
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO anomalies 
                        (anomaly_id, anomaly_type, record_id, supplier_id, severity, plain_language_description, recommended_action, status, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            anomaly_id,
                            "statistical_deviation",
                            rec_id,
                            supplier_id,
                            severity,
                            desc,
                            "Verify meter readings and check for production scale adjustments.",
                            "open",
                            datetime.utcnow().isoformat() + "Z"
                        )
                    )
                    anomalies_detected.append({
                        "anomaly_id": anomaly_id,
                        "type": "statistical_deviation",
                        "severity": severity,
                        "description": desc
                    })
                    
            # Category 2: Zero emissions during active periods
            if co2e == 0.0 and quantity == 0.0 and act_type != "unknown":
                anom_hash = hashlib.md5(f"zero_{rec_id}_{supplier_id}_{period}".encode('utf-8')).hexdigest()[:12]
                anomaly_id = f"anm_{anom_hash}"
                desc = f"Reported zero consumption for active category '{act_type}' during reporting period {period}."
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO anomalies 
                    (anomaly_id, anomaly_type, record_id, supplier_id, severity, plain_language_description, recommended_action, status, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        anomaly_id,
                        "zero_emission_anomaly",
                        rec_id,
                        supplier_id,
                        "CRITICAL",
                        desc,
                        "Request confirmation of plant operational status or utility invoices.",
                        "open",
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                anomalies_detected.append({
                    "anomaly_id": anomaly_id,
                    "type": "zero_emission_anomaly",
                    "severity": "CRITICAL",
                    "description": desc
                })

            # Category 3: Interpolated/Arithmetically smooth decreases
            # In a real model, analyze history of decreases. 
            # For demonstration, check if decrease matches exactly 5.0% or 10.0% (representing potential interpolation)
            if hist_avg is not None and hist_avg > 0:
                pct_reduction = (hist_avg - co2e) / hist_avg
                # Checks if reduction is suspiciously round (representing interpolated value)
                if abs(pct_reduction - 0.05) < 0.0001 or abs(pct_reduction - 0.10) < 0.0001:
                    anom_hash = hashlib.md5(f"smoothing_{rec_id}_{supplier_id}_{period}".encode('utf-8')).hexdigest()[:12]
                    anomaly_id = f"anm_{anom_hash}"
                    desc = f"Suspiciously smooth period-over-period carbon reduction of exactly {pct_reduction:.1%}. Potential interpolation/smoothing detected."
                    
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO anomalies 
                        (anomaly_id, anomaly_type, record_id, supplier_id, severity, plain_language_description, recommended_action, status, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            anomaly_id,
                            "suspicious_smoothing",
                            rec_id,
                            supplier_id,
                            "WARNING",
                            desc,
                            "Perform manual inspection of raw source records for measurement vs estimation.",
                            "open",
                            datetime.utcnow().isoformat() + "Z"
                        )
                    )
                    anomalies_detected.append({
                        "anomaly_id": anomaly_id,
                        "type": "suspicious_smoothing",
                        "severity": "WARNING",
                        "description": desc
                    })
                    
        # 4. Data integrity check: duplicates
        cursor.execute("""
            SELECT record_id, activity_type, quantity, country, period
            FROM activity_records
            WHERE supplier_id = ? AND period = ?
        """, (supplier_id, period))
        records = cursor.fetchall()
        seen = {}
        for r in records:
            r_id, a_type, qty, cty, prd = r
            key = (a_type, qty, cty, prd)
            if key in seen:
                orig_id = seen[key]
                anom_hash = hashlib.md5(f"duplicate_{r_id}_{supplier_id}_{period}".encode('utf-8')).hexdigest()[:12]
                anomaly_id = f"anm_{anom_hash}"
                desc = f"Duplicate record detected: Activity '{a_type}' (Qty {qty} {cty}) matches prior record {orig_id} exactly."
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO anomalies 
                    (anomaly_id, anomaly_type, record_id, supplier_id, severity, plain_language_description, recommended_action, status, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        anomaly_id,
                        "duplicate_record",
                        r_id,
                        supplier_id,
                        "WARNING",
                        desc,
                        "De-duplicate records in the ERP interface or filter redundant files.",
                        "open",
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                anomalies_detected.append({
                    "anomaly_id": anomaly_id,
                    "type": "duplicate_record",
                    "severity": "WARNING",
                    "description": desc
                })
            else:
                seen[key] = r_id

        conn.commit()
        conn.close()

        # If any anomalies were found, alert
        if anomalies_detected:
            self.log_action("anomalies_found", {"count": len(anomalies_detected)})
            for anomaly in anomalies_detected:
                self.call_tool("ecochain.alert.dispatch", {
                    "supplier_id": supplier_id,
                    "severity": anomaly["severity"],
                    "message": f"Anomaly Triggered: {anomaly['description']}",
                    "channel": "email"
                })
                
        return anomalies_detected
        
    def resolve_anomaly(self, anomaly_id: str, reason_code: str, approver: str):
        """Resolves an anomaly. The original record remains untouched, but anomaly state changes."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM anomalies WHERE anomaly_id = ?", (anomaly_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Anomaly {anomaly_id} not found")
            
        cursor.execute(
            """
            UPDATE anomalies 
            SET status = 'resolved', resolution_reason = ?, resolved_by = ?, resolved_at = ?
            WHERE anomaly_id = ?
            """,
            (reason_code, approver, datetime.utcnow().isoformat() + "Z", anomaly_id)
        )
        conn.commit()
        conn.close()
        
        self.log_action("anomaly_resolved", {
            "anomaly_id": anomaly_id,
            "reason_code": reason_code,
            "resolved_by": approver
        })
