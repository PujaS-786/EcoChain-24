import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class CalculationAgent(Agent):
    def __init__(self):
        super().__init__("calculate")
        
    def calculate_record(self, record_id: str) -> dict:
        """Converts an activity record into a verified CO2e record."""
        self.log_action("calculation_start", {"record_id": record_id})
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_records WHERE record_id = ?", (record_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            self.log_action("calculation_error", {"record_id": record_id, "reason": "Record not found"})
            raise ValueError(f"Activity record {record_id} not found")
            
        (
            _,
            supplier_id,
            data_source,
            data_quality,
            input_confidence,
            _,
            activity_type,
            quantity,
            unit,
            country,
            period,
            details_str
        ) = row
        
        details = json.loads(details_str) if details_str else {}
        
        # Look up emission factor via MCP
        res = self.call_tool("ecochain.calculate.factor_lookup", {
            "activity_type": activity_type,
            "country": country,
            "year": period.split("-")[0] if "-" in period else "2024",
            "details": details
        })
        
        if res.get("status") != "success":
            conn.close()
            self.log_action("calculation_factor_error", {"record_id": record_id, "error": res.get("message")})
            raise RuntimeError(f"Factor lookup failed: {res.get('message')}")
            
        factor_val = res["value"]
        factor_unit = res["unit"]
        factor_ver = res["version"]
        factor_confidence = res["confidence"]
        
        # Calculate carbon emissions
        co2e = quantity * factor_val
        co2e_market = None
        calc_method = "physical"
        
        # Determine GHG Scope and Category
        scope = 3
        category = "Scope 3 — Upstream Purchased Goods"
        
        if activity_type == "fuel":
            scope = 1
            category = "Scope 1 — Direct Combustion"
            calc_method = "physical"
        elif activity_type == "electricity":
            scope = 2
            category = "Scope 2 — Indirect Purchased Energy"
            # Dual Scope 2 Reporting
            # Location-based applies the standard grid factor
            # Market-based applies supplier-specific factor if valid EAC exists, else matches location-based
            calc_method = "location-based"
            if details.get("tariff_type") == "renewable":
                # Market-based carbon emission for 100% renewable EAC is 0
                co2e_market = 0.0
                calc_method = "market-based"
            else:
                co2e_market = co2e # Default market-based matches location-based
        elif activity_type in ["spend", "eeio"]:
            scope = 3
            category = "Scope 3 — Upstream Purchased Goods"
            calc_method = "spend-based"
        elif activity_type == "logistics":
            scope = 3
            category = "Scope 3 — Transport and Distribution"
            calc_method = "physical"
        elif activity_type == "agriculture":
            scope = 3
            category = "Scope 3 — Upstream Agriculture"
            calc_method = "physical"
            
        # Combine confidence scores (input data quality * emission factor reliability)
        # Note: input_confidence is standard 0.0 to 1.0
        combined_confidence = input_confidence * factor_confidence
        
        # Write emissions output
        cursor.execute(
            """
            INSERT OR REPLACE INTO emissions_records 
            (record_id, supplier_id, scope, category, co2e, co2e_market, emission_factor_used, calculation_method, confidence_score, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                supplier_id,
                scope,
                category,
                co2e,
                co2e_market,
                f"{factor_ver} ({factor_val} {factor_unit})",
                calc_method,
                combined_confidence,
                datetime.utcnow().isoformat() + "Z"
            )
        )
        conn.commit()
        conn.close()
        
        output = {
            "record_id": record_id,
            "supplier_id": supplier_id,
            "scope": scope,
            "category": category,
            "co2e": co2e,
            "co2e_market": co2e_market,
            "emission_factor_used": f"{factor_ver} ({factor_val} {factor_unit})",
            "calculation_method": calc_method,
            "confidence_score": combined_confidence
        }
        
        self.log_action("calculation_success", output)
        return output
