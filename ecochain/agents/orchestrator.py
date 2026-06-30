import json
import concurrent.futures
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.agents.ingest import IngestionAgent
from ecochain.agents.calculate import CalculationAgent
from ecochain.agents.audit import SupplierAuditAgent
from ecochain.agents.anomaly import AnomalyDetectionAgent
from ecochain.agents.comply import ComplianceAgent
from ecochain.agents.recommend import RecommendationAgent
from ecochain.agents.report import ReportAgent
from ecochain.db import get_connection

class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__("orchestrator")
        self.ingest_agent = IngestionAgent()
        self.calc_agent = CalculationAgent()
        self.audit_agent = SupplierAuditAgent()
        self.anomaly_agent = AnomalyDetectionAgent()
        self.comply_agent = ComplianceAgent()
        self.recommend_agent = RecommendationAgent()
        self.report_agent = ReportAgent()
        
    def run_pipeline(self, period: str, raw_records: list = None, document_paths: list = None, active_suppliers: list = None) -> dict:
        """Main conductor of the multi-agent carbon auditing flow."""
        self.log_action("pipeline_start", {"period": period})
        
        # 1. Verification of expected suppliers
        if active_suppliers:
            self.ingest_agent.check_overdue_submissions(active_suppliers, period)
            
        # 2. Ingest structured inputs & parse unstructured documents
        activity_records = []
        
        # Ingestion
        if raw_records:
            for raw in raw_records:
                try:
                    record = self.ingest_agent.normalize_record(raw)
                    activity_records.append(record)
                except Exception as e:
                    self.log_action("pipeline_ingest_failure", {"raw": raw, "error": str(e)})
                    
        if document_paths:
            for doc in document_paths:
                res = self.ingest_agent.ingest_document(doc)
                if res.get("status") == "success":
                    activity_records.append(res["record"])
                else:
                    self.log_action("pipeline_doc_skip", {"path": doc, "result": res})
                    
        if not activity_records:
            # Load existing records for this period from DB if no new inputs were passed
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT record_id FROM activity_records WHERE period = ?", (period,))
            rows = cursor.fetchall()
            conn.close()
            activity_records = [{"record_id": r[0]} for r in rows]
            
        if not activity_records:
            self.log_action("pipeline_end_empty", {"period": period})
            return {"status": "empty", "message": "No activity records to process."}

        # 3. Fan-out Parallelism for Emissions Calculation
        self.log_action("parallel_calculation_start", {"count": len(activity_records)})
        emissions_outputs = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_rec = {
                executor.submit(self.calc_agent.calculate_record, rec["record_id"]): rec 
                for rec in activity_records if "rec_missing_" not in rec["record_id"]
            }
            for future in concurrent.futures.as_completed(future_to_rec):
                rec = future_to_rec[future]
                try:
                    res = future.result()
                    emissions_outputs.append(res)
                except Exception as e:
                    self.log_action("parallel_calculation_failure", {"record_id": rec["record_id"], "error": str(e)})

        # 4. Supplier Auditing
        supplier_ids = list(set(e["supplier_id"] for e in emissions_outputs if e["supplier_id"]))
        for sup_id in supplier_ids:
            self.audit_agent.audit_supplier(sup_id, period)
            
        # 5. Anomaly Detection
        for sup_id in supplier_ids:
            self.anomaly_agent.check_anomalies(sup_id, period)
            
        # 6. Conflict Detection & Mitigation
        # "If the Emissions Calc Agent and the Supplier Audit Agent return results for the same record
        # that are logically inconsistent, you do not choose one. You freeze that record, log the conflict
        # with both results, and route it to the Compliance Agent for a framework-based resolution."
        self._detect_and_resolve_conflicts(period)

        # 7. Compliance Assessment
        self.comply_agent.evaluate_compliance(period)
        
        # 8. Recommendations Generation
        self.recommend_agent.generate_recommendations(period)
        
        # 9. Report Outputs Generation
        reports_generated = {}
        report_types = ["ghg_inventory", "supplier_scorecard", "board_summary"]
        for r_type in report_types:
            try:
                filepath = self.report_agent.generate_report(r_type, period)
                reports_generated[r_type] = filepath
            except Exception as e:
                self.log_action("pipeline_report_failure", {"type": r_type, "error": str(e)})
                
        pipeline_result = {
            "status": "success",
            "period": period,
            "processed_records": len(activity_records),
            "emissions_calculated": len(emissions_outputs),
            "reports": reports_generated
        }
        self.log_action("pipeline_end", pipeline_result)
        return pipeline_result

    def _detect_and_resolve_conflicts(self, period: str):
        """Checks for mismatches between calculation data quality claims and supplier audit tiers."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query records where emissions claim 'verified' status, but supplier profile rating is 'Tier D' (conflict!)
        cursor.execute("""
            SELECT e.record_id, e.supplier_id, e.co2e, s.tier
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            JOIN supplier_profiles s ON e.supplier_id = s.supplier_id
            WHERE a.period = ? AND a.data_quality = 'verified' AND s.tier = 'Tier D'
        """, (period,))
        conflicts = cursor.fetchall()
        conn.close()
        
        for conf in conflicts:
            rec_id, sup_id, co2e, tier = conf
            self.log_action("logical_conflict_detected", {
                "record_id": rec_id,
                "supplier_id": sup_id,
                "calculated_co2e": co2e,
                "supplier_tier": tier,
                "reason": "Verified record claimed from Tier D supplier (data mismatch)."
            })
            
            # FREEZE the record: downgrade data quality to 'estimated' and lower confidence score to 0.40
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE activity_records SET data_quality = 'estimated', confidence_score = 0.40 WHERE record_id = ?",
                (rec_id,)
            )
            # Recompute emissions confidence score
            cursor.execute(
                "UPDATE emissions_records SET confidence_score = 0.40 * 0.85 WHERE record_id = ?",
                (rec_id,)
            )
            conn.commit()
            conn.close()
            
            # Log resolution
            self.log_action("logical_conflict_mitigated", {
                "record_id": rec_id,
                "resolution": "Record frozen and downgraded to estimated data quality. Routed to Compliance verification."
            })
            
            # Alert compliance officer
            self.call_tool("ecochain.alert.dispatch", {
                "supplier_id": sup_id,
                "severity": "CRITICAL",
                "message": f"Conflict resolved: Record {rec_id} from supplier {sup_id} downgraded due to Tier D profile status.",
                "channel": "email"
            })
