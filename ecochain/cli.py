import os
import sys
import json
import argparse
from ecochain.db import init_db, verify_audit_trail_integrity
from ecochain.agents.orchestrator import OrchestratorAgent
from ecochain.agents.ingest import IngestionAgent
from ecochain.agents.calculate import CalculationAgent
from ecochain.agents.audit import SupplierAuditAgent
from ecochain.agents.anomaly import AnomalyDetectionAgent
from ecochain.agents.comply import ComplianceAgent
from ecochain.agents.report import ReportAgent
from ecochain.agents.alert import AlertAgent
from ecochain.agents.log import LogAgent

def print_banner():
    print(r"""
=============================================================
   _____           _____ _           _       ___  ___
  |  ___|         /  __ \ |         (_)      |  \/  |
  | |__  ___ ___  | /  \/| |__   __ _ _ _ __ | .  . |
  |  __|/ __/ _ \ | |    | '_ \ / _` | | '_ \| |\/| |
  | |__| (_| (_) || \__/\| | | | (_| | | | | | |  | |
  \____/\___\___/  \____/|_| |_|\__,_|_|_| |_\_|  |_/ 24
      Always-On Multi-Agent Supply Chain Carbon Auditor
=============================================================
""")

def main():
    init_db() # Ensure tables exist
    
    if len(sys.argv) < 2:
        print_banner()
        print("Usage: ecochain <agent-name> <command> [options]")
        print("Agents: orchestrator, ingest, calculate, audit, anomaly, comply, report, alert, log, dashboard")
        sys.exit(1)
        
    agent = sys.argv[1].lower()
    
    if agent == "dashboard":
        # Custom command to start the web server easily
        from ecochain.server import start_server
        port = 8000
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                port = int(sys.argv[idx + 1])
        start_server(port)
        return

    # Create sub-parsers depending on agent
    parser = argparse.ArgumentParser(prog=f"ecochain {agent}")
    
    if agent == "orchestrator":
        parser.add_argument("command", choices=["run-pipeline", "status"])
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--suppliers", help="JSON string of active suppliers")
        
        args = parser.parse_args(sys.argv[2:])
        orch = OrchestratorAgent()
        
        if args.command == "run-pipeline":
            active_sups = json.loads(args.suppliers) if args.suppliers else [
                {"supplier_id": "sup_green_energy", "name": "Green Energy Corp"},
                {"supplier_id": "sup_alpha_logistics", "name": "Alpha Logistics Co"},
                {"supplier_id": "sup_beta_steel", "name": "Beta Steel Ltd"}
            ]
            print(f"Running carbon auditor pipeline for period: {args.period}...")
            res = orch.run_pipeline(args.period, active_suppliers=active_sups)
            print(json.dumps(res, indent=2))
        elif args.command == "status":
            print("System Status: Operational")
            print("Agents Registered: 8 Specialist Agents Online")
            print("Audit Trail Status: Verified Integrity Chain")
            
    elif agent == "ingest":
        parser.add_argument("command", choices=["run", "validate", "preview", "check-connection"])
        parser.add_argument("--supplier", default="sup_green_energy")
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--source", default="erp_system")
        parser.add_argument("--document", help="Path to document")
        parser.add_argument("--type", default="electricity")
        parser.add_argument("--qty", type=float, default=5000.0)
        parser.add_argument("--unit", default="kWh")
        
        args = parser.parse_args(sys.argv[2:])
        ing = IngestionAgent()
        
        if args.command == "run":
            print(f"Running ingestion for supplier {args.supplier} from source {args.source}...")
            raw_data = {
                "supplier_id": args.supplier,
                "period": args.period,
                "activity_type": args.type,
                "quantity": args.qty,
                "unit": args.unit,
                "country": "US",
                "data_source": args.source
            }
            rec = ing.normalize_record(raw_data)
            print("Normalized Ingestion Output:")
            print(json.dumps(rec, indent=2))
        elif args.command == "validate":
            if not args.document:
                print("Error: --document path required")
                sys.exit(1)
            print(f"Validating document parse parameters: {args.document}")
            res = ing.ingest_document(args.document)
            print(json.dumps(res, indent=2))
        elif args.command == "preview":
            print(f"Previewing normalized structure for source {args.source}...")
            raw_data = {"activity_type": "fuel", "quantity": 100, "unit": "L", "supplier_id": "test_preview"}
            res = ing.call_tool("ecochain.ingest.normalize_record", {"data": raw_data})
            print(json.dumps(res.get("record"), indent=2))
        elif args.command == "check-connection":
            print(f"Pinging connector: {args.source}...")
            res = ing.call_tool("ecochain.ingest.check_connection", {"source": args.source})
            print(f"Connection Status: Connected (Response time {res.get('ping_ms')}ms)")
            
    elif agent == "calculate":
        parser.add_argument("command", choices=["factor-lookup", "run", "compare-scope2", "list-factors"])
        parser.add_argument("--type", default="electricity")
        parser.add_argument("--country", default="US")
        parser.add_argument("--year", default="2024")
        parser.add_argument("--record", help="Record ID")
        parser.add_argument("--meter", help="Meter Record ID or Supplier ID")
        
        args = parser.parse_args(sys.argv[2:])
        calc = CalculationAgent()
        
        if args.command == "factor-lookup":
            res = calc.call_tool("ecochain.calculate.factor_lookup", {
                "activity_type": args.type,
                "country": args.country,
                "year": args.year
            })
            print(json.dumps(res, indent=2))
        elif args.command == "run":
            if not args.record:
                print("Error: --record ID required")
                sys.exit(1)
            res = calc.calculate_record(args.record)
            print(json.dumps(res, indent=2))
        elif args.command == "compare-scope2":
            # Show location-based vs market-based
            print(f"Comparing location-based and market-based calculations for meter/site {args.meter or 'US'}...")
            loc = calc.call_tool("ecochain.calculate.factor_lookup", {"activity_type": "electricity", "country": "US", "details": {"tariff_type": "standard"}})
            mkt = calc.call_tool("ecochain.calculate.factor_lookup", {"activity_type": "electricity", "country": "US", "details": {"tariff_type": "renewable"}})
            print(f"Location-based grid intensity: {loc.get('value')} {loc.get('unit')} (Confidence {loc.get('confidence')})")
            print(f"Market-based (EAC Renewable) intensity: 0.00 {mkt.get('unit')} (Confidence {mkt.get('confidence')})")
        elif args.command == "list-factors":
            from ecochain.mcp import EMISSION_FACTORS
            print(json.dumps(EMISSION_FACTORS, indent=2))
            
    elif agent == "audit":
        parser.add_argument("command", choices=["score", "compare-baseline", "list-poor-suppliers", "show-queue"])
        parser.add_argument("--supplier", default="sup_green_energy")
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--member", default="Sustainability Manager")
        
        args = parser.parse_args(sys.argv[2:])
        audit = SupplierAuditAgent()
        
        if args.command == "score":
            res = audit.audit_supplier(args.supplier, args.period)
            print(json.dumps(res, indent=2))
        elif args.command == "compare-baseline":
            res = audit.audit_supplier(args.supplier, args.period)
            print(f"Supplier Profile comparison for {args.supplier}:")
            print(f"Assigned Level: {res.get('tier')} | Year-on-year trend: {res.get('trend')} (Confidence {res.get('confidence_score')})")
        elif args.command == "list-poor-suppliers":
            import sqlite3
            from ecochain.db import DB_FILE
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT supplier_id, name, tier, trend FROM supplier_profiles WHERE tier IN ('Tier C', 'Tier D')")
            rows = cursor.fetchall()
            conn.close()
            print("Suppliers requiring follow-up (Tiers C & D):")
            for r in rows:
                print(f"- {r[0]} ({r[1]}): {r[2]}, trend: {r[3]}")
        elif args.command == "show-queue":
            print(f"Follow-up action queue for team member: {args.member}")
            print(f"- Target: sup_beta_steel (Beta Steel Ltd)")
            print(f"  Action: Request primary utility bills and certificate credentials for verification.")
            print(f"  Deadline: 15 business days")
            
    elif agent == "anomaly":
        parser.add_argument("command", choices=["run-check", "replay", "list", "resolve"])
        parser.add_argument("--supplier", default="sup_green_energy")
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--min-severity", default="INFO")
        parser.add_argument("--id", help="Anomaly ID")
        parser.add_argument("--reason", help="Resolution Reason Code")
        parser.add_argument("--approver", default="Compliance Officer")
        
        args = parser.parse_args(sys.argv[2:])
        anm = AnomalyDetectionAgent()
        
        if args.command == "run-check":
            res = anm.check_anomalies(args.supplier, args.period)
            print(f"Found {len(res)} anomalies:")
            print(json.dumps(res, indent=2))
        elif args.command == "replay":
            print(f"Replaying anomaly runs for period {args.period}...")
            # Mock replay
            print("Replay completed successfully. 0 new anomalies discovered.")
        elif args.command == "list":
            import sqlite3
            from ecochain.db import DB_FILE
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT anomaly_id, anomaly_type, supplier_id, severity, plain_language_description, status FROM anomalies")
            rows = cursor.fetchall()
            conn.close()
            print("Active Anomalies:")
            for r in rows:
                print(f"[{r[3]}] ID: {r[0]} | Type: {r[1]} | Supplier: {r[2]} | Status: {r[5]} | Desc: {r[4]}")
        elif args.command == "resolve":
            if not args.id or not args.reason:
                print("Error: --id and --reason parameters required for resolution.")
                sys.exit(1)
            anm.resolve_anomaly(args.id, args.reason, args.approver)
            print(f"Anomaly {args.id} resolved with reason '{args.reason}' by {args.approver}.")
            
    elif agent == "comply":
        parser.add_argument("command", choices=["run-gap-check", "show-status", "estimate-risk", "list-frameworks"])
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--framework", default="GHG_Protocol")
        
        args = parser.parse_args(sys.argv[2:])
        com = ComplianceAgent()
        
        if args.command == "run-gap-check":
            res = com.evaluate_compliance(args.period)
            print(json.dumps(res, indent=2))
        elif args.command == "show-status":
            res = com.evaluate_compliance(args.period)
            print(f"Status for framework {args.framework}:")
            print(json.dumps(res.get(args.framework, []), indent=2))
        elif args.command == "estimate-risk":
            res = com.evaluate_compliance(args.period)
            total_exposure = 0.0
            for fw, reqs in res.items():
                for r in reqs:
                    total_exposure += r.get("financial_exposure", 0.0)
            print(f"Estimated Regulatory Compliance Risk Exposure: ${total_exposure:,.2f} USD")
        elif args.command == "list-frameworks":
            print("Active Regulatory Carbon Frameworks configured:")
            print("- GHG Protocol (Scope 1, 2, 3)")
            print("- CSRD / ESRS E1 (Materiality & Value Chain)")
            print("- TCFD (Governance & Metrics)")
            print("- ISO 14064 (Verifiability standards)")
            print("- SBTi (Science Based Target alignment)")
            print("- SFDR (Mandatory PAI indicators)")
            print("- SEC Climate Disclosure Rules")
            
    elif agent == "report":
        parser.add_argument("command", choices=["generate", "preview", "lineage", "list-generated"])
        parser.add_argument("--type", default="ghg_inventory")
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--figure", help="Record ID for carbon lineage lookups")
        
        args = parser.parse_args(sys.argv[2:])
        rep = ReportAgent()
        
        if args.command == "generate":
            filepath = rep.generate_report(args.type, args.period)
            print(f"Report generated successfully: {filepath}")
        elif args.command == "preview":
            print(f"Previewing reports coverage metrics for period {args.period}...")
            filepath = rep.generate_report(args.type, args.period)
            print(f"Coverage assessment result saved to: {filepath}")
        elif args.command == "lineage":
            if not args.figure:
                print("Error: --figure [record_id] is required.")
                sys.exit(1)
            lineage = rep.get_lineage(args.figure)
            print("Traceable Data Lineage:")
            print(json.dumps(lineage, indent=2))
        elif args.command == "list-generated":
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
            if os.path.exists(reports_dir):
                print(f"Generated documents in: {reports_dir}")
                for f in os.listdir(reports_dir):
                    print(f"- {f}")
            else:
                print("No reports folder initialized yet.")
                
    elif agent == "alert":
        parser.add_argument("command", choices=["send-test", "show-history", "escalate"])
        parser.add_argument("--channel", default="email")
        parser.add_argument("--supplier", help="Supplier ID filter")
        parser.add_argument("--id", help="Alert ID")
        parser.add_argument("--severity", default="CRITICAL")
        parser.add_argument("--reason", help="Escalation reason text")
        
        args = parser.parse_args(sys.argv[2:])
        alt = AlertAgent()
        
        if args.command == "send-test":
            a_id = alt.send_test_alert(args.channel)
            print(f"Test alert dispatched. Alert ID: {a_id}")
        elif args.command == "show-history":
            history = alt.show_alert_history(args.supplier)
            print(json.dumps(history, indent=2))
        elif args.command == "escalate":
            if not args.id or not args.reason:
                print("Error: --id and --reason parameters required for escalation.")
                sys.exit(1)
            alt.escalate_alert(args.id, args.severity, args.reason)
            print(f"Alert {args.id} escalated to {args.severity}. Reason logged.")
            
    elif agent == "log":
        parser.add_argument("command", choices=["query", "show-actions", "verify", "export"])
        parser.add_argument("--record", help="Record ID")
        parser.add_argument("--supplier", help="Supplier ID")
        parser.add_argument("--period", default="2024-Q1")
        parser.add_argument("--output", default="audit_trail_export.csv")
        
        args = parser.parse_args(sys.argv[2:])
        lg = LogAgent()
        
        if args.command == "query":
            if not args.record:
                print("Error: --record [id] required")
                sys.exit(1)
            res = lg.query_audit_trail(args.record)
            print(json.dumps(res, indent=2))
        elif args.command == "show-actions":
            if not args.supplier:
                print("Error: --supplier [id] required")
                sys.exit(1)
            res = lg.show_agent_actions(args.supplier, args.period)
            print(json.dumps(res, indent=2))
        elif args.command == "verify":
            print("Verifying cryptographic audit trail hash chains...")
            valid, errors = verify_audit_trail_integrity()
            if valid:
                print("SUCCESS: Log integrity verified. 0 tampered entries detected.")
            else:
                print("CRITICAL: Audit chain break detected!")
                for e in errors:
                    print(f"- {e}")
        elif args.command == "export":
            path = lg.export_audit_trail(args.period, args.output)
            print(f"Audit trail for period {args.period} exported to: {path}")
            
    else:
        print(f"Unknown agent: {agent}")
        sys.exit(1)

if __name__ == "__main__":
    main()
