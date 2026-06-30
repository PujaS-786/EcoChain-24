from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class AlertAgent(Agent):
    def __init__(self):
        super().__init__("alert")
        
    def send_test_alert(self, channel: str) -> str:
        """Sends a test alert to verify channels are functional."""
        self.log_action("send_test_alert", {"channel": channel})
        res = self.call_tool("ecochain.alert.dispatch", {
            "supplier_id": "system_test",
            "severity": "INFO",
            "message": f"EcoChain 24 operational alert channel test for {channel}",
            "channel": channel
        })
        return res.get("alert_id")

    def show_alert_history(self, supplier_id: str = None) -> list:
        """Queries the history of alerts, optionally filtering by supplier."""
        conn = get_connection()
        cursor = conn.cursor()
        if supplier_id:
            cursor.execute("SELECT * FROM alerts WHERE supplier_id = ? ORDER BY timestamp DESC", (supplier_id,))
        else:
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        alerts = [
            {"id": r[0], "timestamp": r[1], "supplier_id": r[2], "severity": r[3], "message": r[4], "channel": r[5], "status": r[6]}
            for r in rows
        ]
        return alerts

    def escalate_alert(self, alert_id: str, new_severity: str, reason: str):
        """Escalates an existing alert to a higher severity level with a documented reason."""
        self.log_action("escalate_alert_attempt", {"alert_id": alert_id, "new_severity": new_severity})
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT severity, message, supplier_id FROM alerts WHERE alert_id = ?", (alert_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Alert {alert_id} not found")
            
        old_severity, message, supplier_id = row
        
        cursor.execute(
            "UPDATE alerts SET severity = ?, message = ? WHERE alert_id = ?",
            (new_severity, f"[ESCALATED from {old_severity}]: {message} (Reason: {reason})", alert_id)
        )
        conn.commit()
        conn.close()
        
        self.log_action("escalate_alert_success", {
            "alert_id": alert_id,
            "old_severity": old_severity,
            "new_severity": new_severity,
            "reason": reason
        })
