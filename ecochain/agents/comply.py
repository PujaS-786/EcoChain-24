import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection
from ecochain.mcp import FRAMEWORK_REQUIREMENTS

class ComplianceAgent(Agent):
    def __init__(self):
        super().__init__("comply")
        
    def evaluate_compliance(self, period: str) -> dict:
        """Evaluates disclosure statuses across all active frameworks."""
        self.log_action("compliance_check_start", {"period": period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Gather aggregate statistics for evaluation
        # Total records, average confidence
        cursor.execute("""
            SELECT e.scope, e.co2e, e.co2e_market, e.confidence_score, a.data_quality
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            WHERE a.period = ?
        """, (period,))
        emissions = cursor.fetchall()
        
        # Calculate coverage (records that are verified vs estimated/missing)
        total_records = len(emissions)
        verified_records = sum(1 for e in emissions if e[4] == "verified")
        avg_confidence = sum(e[3] for e in emissions) / total_records if total_records > 0 else 0.0
        
        coverage_pct = (verified_records / total_records * 100.0) if total_records > 0 else 0.0
        
        results = {}
        
        for framework, requirements in FRAMEWORK_REQUIREMENTS.items():
            results[framework] = []
            
            for req in requirements:
                req_id = req["id"]
                status = "GAP"
                missing_data = ""
                responsible_agent = "ingest"
                risk_level = "low"
                fin_exposure = 0.0
                
                # Check status based on metrics
                if total_records == 0:
                    status = "GAP"
                    missing_data = "No emissions records ingested for period"
                    risk_level = "high"
                    fin_exposure = 50000.0 # Regulatory fine estimate
                else:
                    if req_id == "GHG-1.1": # Scope 1
                        has_s1 = any(e[0] == 1 for e in emissions)
                        s1_conf = [e[3] for e in emissions if e[0] == 1]
                        s1_avg_conf = sum(s1_conf)/len(s1_conf) if s1_conf else 0.0
                        
                        if has_s1 and s1_avg_conf >= 0.85:
                            status = "MET"
                        elif has_s1:
                            status = "PARTIAL"
                            missing_data = "Scope 1 data contains low-confidence estimates"
                            responsible_agent = "audit"
                            risk_level = "medium"
                            fin_exposure = 15000.0
                        else:
                            status = "GAP"
                            missing_data = "No Scope 1 emissions records detected"
                            risk_level = "critical"
                            fin_exposure = 100000.0
                            
                    elif req_id == "GHG-2.1": # Scope 2 Dual Reporting
                        has_s2 = any(e[0] == 2 for e in emissions)
                        s2_rec = [e for e in emissions if e[0] == 2]
                        has_dual = all(r[2] is not None for r in s2_rec) if s2_rec else False
                        
                        if has_s2 and has_dual:
                            status = "MET"
                        elif has_s2:
                            status = "PARTIAL"
                            missing_data = "Scope 2 market-based electricity data missing, using location-based fallbacks"
                            responsible_agent = "ingest"
                            risk_level = "medium"
                            fin_exposure = 10000.0
                        else:
                            status = "GAP"
                            missing_data = "No Scope 2 electricity inputs found"
                            risk_level = "high"
                            fin_exposure = 50000.0
                            
                    elif req_id == "ESRS-E1-4": # Materiality
                        # material assessment is process-based, let's base it on database verification status
                        if coverage_pct > 80.0:
                            status = "MET"
                        else:
                            status = "PARTIAL"
                            missing_data = "Double materiality assessment requires higher data coverage"
                            responsible_agent = "audit"
                            risk_level = "medium"
                            fin_exposure = 20000.0
                            
                    elif req_id == "ESRS-E1-6": # Scope 3 Value Chain
                        has_s3 = any(e[0] == 3 for e in emissions)
                        s3_conf = [e[3] for e in emissions if e[0] == 3]
                        s3_avg_conf = sum(s3_conf)/len(s3_conf) if s3_conf else 0.0
                        
                        if has_s3 and s3_avg_conf >= 0.80:
                            status = "MET"
                        elif has_s3:
                            status = "PARTIAL"
                            missing_data = "Scope 3 contains spend-based estimations rather than primary supplier factors"
                            responsible_agent = "audit"
                            risk_level = "medium"
                            fin_exposure = 30000.0
                        else:
                            status = "GAP"
                            missing_data = "Scope 3 categories have no tracking records"
                            risk_level = "high"
                            fin_exposure = 75000.0
                            
                    else:
                        # Default check based on global coverage
                        if coverage_pct >= 85.0:
                            status = "MET"
                        elif coverage_pct >= 60.0:
                            status = "PARTIAL"
                            missing_data = f"General data coverage is at {coverage_pct:.1f}% (target 85%)"
                            responsible_agent = "ingest"
                            risk_level = "low"
                            fin_exposure = 5000.0
                        else:
                            status = "GAP"
                            missing_data = f"General data coverage {coverage_pct:.1f}% is below 60% compliance threshold"
                            responsible_agent = "ingest"
                            risk_level = "high"
                            fin_exposure = 40000.0
                
                # Check for Scope 2 Methodological split
                # CSRD prefers market-based for Scope 2 target tracking, GHG Protocol requires both.
                if req_id == "ESRS-E1-6" and status == "MET":
                    # Flag that market-based emissions figures are mapped to CSRD compliance
                    missing_data = "Note: CSRD mapped to market-based scope 2; GHG inventory reports location-based."
                
                # Update DB
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO compliance_disclosures 
                    (framework, requirement_id, status, missing_data, responsible_agent, deadline, risk_level, financial_exposure, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        framework,
                        req_id,
                        status,
                        missing_data,
                        responsible_agent,
                        "30 business days" if status != "MET" else "N/A",
                        risk_level,
                        fin_exposure,
                        datetime.utcnow().isoformat() + "Z"
                    )
                )
                
                results[framework].append({
                    "id": req_id,
                    "name": req["name"],
                    "status": status,
                    "missing_data": missing_data,
                    "risk_level": risk_level,
                    "financial_exposure": fin_exposure
                })
                
        conn.commit()
        conn.close()
        
        self.log_action("compliance_check_success", {"coverage": coverage_pct, "avg_confidence": avg_confidence})
        return results
