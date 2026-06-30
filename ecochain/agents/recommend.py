import json
import uuid
import hashlib
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class RecommendationAgent(Agent):
    def __init__(self):
        super().__init__("recommend")
        
    def generate_recommendations(self, period: str) -> list:
        """Analyzes emissions records for reduction strategies and records recommendations."""
        self.log_action("recommendations_start", {"period": period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Fetch emissions and records for this period
        cursor.execute("""
            SELECT e.record_id, e.co2e, e.scope, a.activity_type, a.quantity, a.details, a.supplier_id
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            WHERE a.period = ?
        """, (period,))
        records = cursor.fetchall()
        
        recs = []
        
        if not records:
            conn.close()
            return []
            
        # Hotspot 1: Scope 2 Electricity (Renewable energy procurement EACs)
        electricity_records = [r for r in records if r[3] == "electricity"]
        if electricity_records:
            details = [json.loads(r[5]) if r[5] else {} for r in electricity_records]
            non_renewable = [r for r, d in zip(electricity_records, details) if d.get("tariff_type") != "renewable"]
            
            if non_renewable:
                basis_ids = [r[0] for r in non_renewable]
                basis_key = "".join(sorted(basis_ids))
                rec_hash = hashlib.md5(f"renewable_{basis_key}".encode('utf-8')).hexdigest()[:12]
                rec_id = f"rcm_{rec_hash}"
                co2_saving = sum(r[1] for r in non_renewable) # 100% savings for going 100% renewable
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO recommendations 
                    (recommendation_id, category, estimated_co2e_saving, implementation_effort, estimated_cost_delta, confidence_in_estimate, data_basis, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id,
                        "Renewable energy procurement",
                        co2_saving,
                        "low",
                        -1200.0, # cost delta (negative means additional cost/premium)
                        "high",
                        json.dumps(basis_ids),
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                recs.append({"id": rec_id, "category": "Renewable energy procurement", "saving": co2_saving})
                
        # Hotspot 2: Logistics mode optimization (e.g., freight road vs rail/sea)
        logistics_records = [r for r in records if r[3] == "logistics"]
        if logistics_records:
            details = [json.loads(r[5]) if r[5] else {} for r in logistics_records]
            road_records = [r for r, d in zip(logistics_records, details) if d.get("transport_mode") == "road"]
            
            if road_records:
                basis_ids = [r[0] for r in road_records]
                basis_key = "".join(sorted(basis_ids))
                rec_hash = hashlib.md5(f"logistics_{basis_key}".encode('utf-8')).hexdigest()[:12]
                rec_id = f"rcm_{rec_hash}"
                # Shifting from road (0.08 kg/t-km) to rail (0.02 kg/t-km) saves 75% emissions
                total_road_emissions = sum(r[1] for r in road_records)
                co2_saving = total_road_emissions * 0.75
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO recommendations 
                    (recommendation_id, category, estimated_co2e_saving, implementation_effort, estimated_cost_delta, confidence_in_estimate, data_basis, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id,
                        "Logistics mode and route optimisation",
                        co2_saving,
                        "medium",
                        2500.0, # positive means cost saving
                        "medium",
                        json.dumps(basis_ids),
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                recs.append({"id": rec_id, "category": "Logistics mode and route optimisation", "saving": co2_saving})
                
        # Hotspot 3: Supplier switching (identifies high intensity suppliers)
        cursor.execute("SELECT supplier_id, name, tier, emission_intensity FROM supplier_profiles WHERE tier IN ('Tier C', 'Tier D')")
        poor_suppliers = cursor.fetchall()
        
        for sup in poor_suppliers:
            sup_id, name, tier, intensity = sup
            # Recommends switching to a Tier A partner, estimated 30% reduction in purchase emissions
            sup_records = [r for r in records if r[6] == sup_id]
            if sup_records:
                basis_ids = [r[0] for r in sup_records]
                basis_key = "".join(sorted(basis_ids))
                rec_hash = hashlib.md5(f"switching_{sup_id}_{basis_key}".encode('utf-8')).hexdigest()[:12]
                rec_id = f"rcm_{rec_hash}"
                co2_saving = sum(r[1] for r in sup_records) * 0.30
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO recommendations 
                    (recommendation_id, category, estimated_co2e_saving, implementation_effort, estimated_cost_delta, confidence_in_estimate, data_basis, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id,
                        "Supplier switching",
                        co2_saving,
                        "high",
                        -5000.0, # negative transition delta cost
                        "medium",
                        json.dumps(basis_ids),
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                recs.append({"id": rec_id, "category": "Supplier switching", "saving": co2_saving})

        conn.commit()
        conn.close()
        
        self.log_action("recommendations_success", {"count": len(recs)})
        return recs
