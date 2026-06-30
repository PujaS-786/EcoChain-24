import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class SupplierAuditAgent(Agent):
    def __init__(self):
        super().__init__("audit")
        
    def audit_supplier(self, supplier_id: str, period: str) -> dict:
        """Audits a supplier's emissions data quality and patterns, assigning a Tier (A-D)."""
        self.log_action("supplier_audit_start", {"supplier_id": supplier_id, "period": period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Fetch current emissions
        cursor.execute("SELECT co2e, confidence_score, calculation_method FROM emissions_records WHERE supplier_id = ?", (supplier_id,))
        rows = cursor.fetchall()
        
        if not rows:
            # No data submitted
            current_tier = "Tier D"
            dq_score = 0.0
            avg_intensity = 0.0
            trend = "unknown"
        else:
            total_co2e = sum(r[0] for r in rows)
            dq_score = sum(r[1] for r in rows) / len(rows)
            
            # Fetch supplier details to compute intensity (e.g., carbon per production volume)
            # In mock data, let's assume we have production capacity / output
            cursor.execute("SELECT name FROM supplier_profiles WHERE supplier_id = ?", (supplier_id,))
            prof = cursor.fetchone()
            supplier_name = prof[0] if prof else supplier_id
            
            # Mock intensity based on co2e
            avg_intensity = total_co2e / 1000.0 # arbitrary scaling factor for intensity
            
            # Determine baseline and trend
            # Fetch historical emissions
            cursor.execute("""
                SELECT AVG(co2e) FROM emissions_records 
                WHERE supplier_id = ? AND record_id NOT IN (
                    SELECT record_id FROM activity_records WHERE period = ?
                )
            """, (supplier_id, period))
            baseline_row = cursor.fetchone()
            baseline = baseline_row[0] if baseline_row and baseline_row[0] is not None else total_co2e
            
            if total_co2e < baseline * 0.9:
                trend = "improving"
            elif total_co2e > baseline * 1.1:
                trend = "declining"
            else:
                trend = "stable"
                
            # Score Tier
            # Tier A - Verified primary data, low intensity, improving trend, high confidence
            # Tier B - Mostly verified, average intensity, minor gaps, stable
            # Tier C - Mixed data quality, above-average intensity, gaps
            # Tier D - Missing/unverified data, high intensity, no disclosure
            if dq_score >= 0.85 and trend == "improving":
                current_tier = "Tier A"
            elif dq_score >= 0.75 and trend in ["stable", "improving"]:
                current_tier = "Tier B"
            elif dq_score >= 0.50:
                current_tier = "Tier C"
            else:
                current_tier = "Tier D"

        # 2. Get previous tier to detect sharp declines
        cursor.execute("SELECT tier, name FROM supplier_profiles WHERE supplier_id = ?", (supplier_id,))
        profile_row = cursor.fetchone()
        
        supplier_name = profile_row[1] if profile_row else f"Supplier {supplier_id}"
        prev_tier = profile_row[0] if profile_row else "Tier B" # Default to B for comparisons
        
        # Save profile update
        cursor.execute(
            """
            INSERT OR REPLACE INTO supplier_profiles 
            (supplier_id, name, tier, data_quality_score, emission_intensity, trend, last_disclosure_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                supplier_id,
                supplier_name,
                current_tier,
                dq_score,
                avg_intensity,
                trend,
                datetime.utcnow().isoformat() + "Z"
            )
        )
        conn.commit()
        conn.close()
        
        self.log_action("supplier_profile_updated", {
            "supplier_id": supplier_id,
            "tier": current_tier,
            "previous_tier": prev_tier,
            "dq_score": dq_score,
            "trend": trend
        })
        
        # Check for critical tier drop (e.g. B -> D, A -> C, A -> D)
        tier_values = {"Tier A": 4, "Tier B": 3, "Tier C": 2, "Tier D": 1}
        prev_val = tier_values.get(prev_tier, 3)
        curr_val = tier_values.get(current_tier, 1)
        
        if prev_val - curr_val >= 2:
            # Critical Drop Alert
            self.call_tool("ecochain.alert.dispatch", {
                "supplier_id": supplier_id,
                "severity": "CRITICAL",
                "message": f"Critical rating drop for supplier {supplier_name} from {prev_tier} to {current_tier}! Immediate operational review required.",
                "channel": "email"
            })
            self.log_action("critical_tier_drop", {"supplier_id": supplier_id, "prev": prev_tier, "curr": current_tier})
            
        # 3. Create follow-up records for Tier C and Tier D
        if current_tier in ["Tier C", "Tier D"]:
            missing_reason = "Missing primary verification certificates" if current_tier == "Tier C" else "Missing/unreported carbon disclosures"
            followup_details = {
                "action": f"Request primary utility bills and certificate credentials for verification.",
                "assigned_to": "Sustainability Procurement Manager",
                "deadline": "15 business days",
                "target_supplier": supplier_name,
                "reason": missing_reason
            }
            
            # Send assignment alert
            self.call_tool("ecochain.alert.dispatch", {
                "supplier_id": supplier_id,
                "severity": "WARNING",
                "message": f"Action Assigned: Follow up with {supplier_name} ({current_tier}). Details: {followup_details['action']}. Target deadline: {followup_details['deadline']}.",
                "channel": "email"
            })
            
        return {
            "supplier_id": supplier_id,
            "name": supplier_name,
            "tier": current_tier,
            "previous_tier": prev_tier,
            "confidence_score": dq_score,
            "trend": trend
        }
