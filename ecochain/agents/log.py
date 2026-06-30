import csv
import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection, verify_audit_trail_integrity

class LogAgent(Agent):
    def __init__(self):
        super().__init__("log")
        
    def query_audit_trail(self, record_id: str) -> list:
        """Finds all transactions, normalization steps, and calculations for a record."""
        self.log_action("query_audit_trail", {"record_id": record_id})
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT entry_id, timestamp, agent_name, action, details FROM audit_trail WHERE details LIKE ? ORDER BY entry_id ASC", (f"%{record_id}%",))
        rows = cursor.fetchall()
        conn.close()
        
        entries = [
            {"entry_id": r[0], "timestamp": r[1], "agent": r[2], "action": r[3], "details": json.loads(r[4])}
            for r in rows
        ]
        return entries
        
    def show_agent_actions(self, supplier_id: str, period: str) -> list:
        """Shows actions performed on a supplier's data during a period."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Details contain both supplier_id and period
        cursor.execute(
            "SELECT entry_id, timestamp, agent_name, action, details FROM audit_trail WHERE details LIKE ? AND details LIKE ? ORDER BY entry_id ASC",
            (f"%{supplier_id}%", f"%{period}%")
        )
        rows = cursor.fetchall()
        conn.close()
        
        actions = [
            {"entry_id": r[0], "timestamp": r[1], "agent_name": r[2], "action": r[3], "details": json.loads(r[4])}
            for r in rows
        ]
        return actions

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Invokes the database hash chain validation check."""
        self.log_action("verify_integrity_start", {})
        is_valid, errors = verify_audit_trail_integrity()
        
        if not is_valid:
            self.log_action("verify_integrity_tamper_detected", {"errors": errors})
            # Trigger alert
            self.call_tool("ecochain.alert.dispatch", {
                "supplier_id": "system_security",
                "severity": "CRITICAL",
                "message": f"Security Alert: Audit trail tamper detection failed! Errors: {', '.join(errors)}",
                "channel": "email"
            })
        else:
            self.log_action("verify_integrity_success", {})
            
        return is_valid, errors

    def export_audit_trail(self, period: str, output_path: str) -> str:
        """Exports the audit trail of a period to a CSV file."""
        self.log_action("export_audit_trail", {"period": period, "output_path": output_path})
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT entry_id, timestamp, agent_name, action, details, previous_hash, content_hash FROM audit_trail WHERE details LIKE ? ORDER BY entry_id ASC", (f"%{period}%",))
        rows = cursor.fetchall()
        conn.close()
        
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["entry_id", "timestamp", "agent_name", "action", "details", "previous_hash", "content_hash"])
            for row in rows:
                writer.writerow(row)
                
        return output_path
