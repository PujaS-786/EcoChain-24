import os
import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from ecochain.db import DB_FILE, init_db, verify_audit_trail_integrity
from ecochain.agents.orchestrator import OrchestratorAgent
from ecochain.agents.anomaly import AnomalyDetectionAgent

PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")

class EcoChainHTTPHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # REST API Routes
        if path.startswith("/api/"):
            self.handle_api_get(path, parsed_url.query)
        else:
            self.handle_static_get(path)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/"):
            self.handle_api_post(path)
        else:
            self.send_error(404, "Not Found")

    def handle_static_get(self, path):
        # Default index.html
        if path == "/" or path == "":
            path = "/index.html"
            
        file_path = os.path.join(STATIC_DIR, path.lstrip("/"))
        
        # Security check: prevent directory traversal
        real_static = os.path.realpath(STATIC_DIR)
        real_file = os.path.realpath(file_path)
        if not real_file.startswith(real_static):
            self.send_error(403, "Access Denied")
            return

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            
            # Content Type
            if file_path.endswith(".html"):
                self.send_header("Content-Type", "text/html")
            elif file_path.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            elif file_path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript")
            elif file_path.endswith(".png"):
                self.send_header("Content-Type", "image/png")
            else:
                self.send_header("Content-Type", "application/octet-stream")
                
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"File {path} not found")

    def handle_api_get(self, path, query_str):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Helpers to send JSON
        def send_json(data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        try:
            if path == "/api/stats":
                # Compute dashboard summaries
                cursor.execute("SELECT SUM(co2e), SUM(co2e_market), AVG(confidence_score) FROM emissions_records")
                em_row = cursor.fetchone()
                total_co2e = em_row[0] if em_row and em_row[0] else 0.0
                total_co2e_mkt = em_row[1] if em_row and em_row[1] else total_co2e
                avg_confidence = em_row[2] if em_row and em_row[2] else 0.0

                cursor.execute("SELECT COUNT(*) FROM supplier_profiles")
                sup_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM anomalies WHERE status = 'open'")
                anm_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM compliance_disclosures WHERE status IN ('GAP', 'PARTIAL')")
                gap_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM activity_records WHERE data_quality = 'verified'")
                verified_recs = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM activity_records")
                all_recs = cursor.fetchone()[0]
                coverage = (verified_recs / all_recs * 100.0) if all_recs > 0 else 0.0

                send_json({
                    "total_co2e_location": total_co2e,
                    "total_co2e_market": total_co2e_mkt,
                    "avg_confidence": avg_confidence,
                    "supplier_count": sup_count,
                    "open_anomalies": anm_count,
                    "compliance_gaps": gap_count,
                    "data_coverage_pct": coverage
                })
                
            elif path == "/api/suppliers":
                cursor.execute("SELECT supplier_id, name, tier, data_quality_score, emission_intensity, trend, last_disclosure_at FROM supplier_profiles")
                rows = cursor.fetchall()
                send_json([
                    {
                        "supplier_id": r[0], "name": r[1], "tier": r[2], 
                        "dq_score": r[3], "intensity": r[4], "trend": r[5], "last_disclosure": r[6]
                    } for r in rows
                ])
                
            elif path == "/api/anomalies":
                cursor.execute("SELECT anomaly_id, anomaly_type, record_id, supplier_id, severity, plain_language_description, recommended_action, status, detected_at, resolved_by FROM anomalies ORDER BY detected_at DESC")
                rows = cursor.fetchall()
                send_json([
                    {
                        "anomaly_id": r[0], "anomaly_type": r[1], "record_id": r[2], "supplier_id": r[3],
                        "severity": r[4], "description": r[5], "recommended_action": r[6], "status": r[7],
                        "detected_at": r[8], "resolved_by": r[9]
                    } for r in rows
                ])
                
            elif path == "/api/compliance":
                cursor.execute("SELECT framework, requirement_id, status, missing_data, responsible_agent, deadline, risk_level, financial_exposure, checked_at FROM compliance_disclosures")
                rows = cursor.fetchall()
                send_json([
                    {
                        "framework": r[0], "requirement_id": r[1], "status": r[2], "missing_data": r[3],
                        "responsible_agent": r[4], "deadline": r[5], "risk_level": r[6], "financial_exposure": r[7], "checked_at": r[8]
                    } for r in rows
                ])
                
            elif path == "/api/recommendations":
                cursor.execute("SELECT recommendation_id, category, estimated_co2e_saving, implementation_effort, estimated_cost_delta, confidence_in_estimate, data_basis, created_at FROM recommendations ORDER BY estimated_co2e_saving DESC")
                rows = cursor.fetchall()
                send_json([
                    {
                        "recommendation_id": r[0], "category": r[1], "estimated_co2e_saving": r[2],
                        "implementation_effort": r[3], "estimated_cost_delta": r[4], "confidence_in_estimate": r[5],
                        "data_basis": json.loads(r[6]), "created_at": r[7]
                    } for r in rows
                ])
                
            elif path == "/api/logs":
                cursor.execute("SELECT entry_id, timestamp, agent_name, action, details, previous_hash, content_hash FROM audit_trail ORDER BY entry_id DESC LIMIT 100")
                rows = cursor.fetchall()
                send_json([
                    {
                        "entry_id": r[0], "timestamp": r[1], "agent_name": r[2], "action": r[3],
                        "details": json.loads(r[4]), "previous_hash": r[5], "content_hash": r[6]
                    } for r in rows
                ])
                
            elif path == "/api/logs/verify":
                valid, errors = verify_audit_trail_integrity()
                send_json({"status": "success" if valid else "tampered", "valid": valid, "errors": errors})
                
            elif path == "/api/reports":
                reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
                files = []
                if os.path.exists(reports_dir):
                    files = [f for f in os.listdir(reports_dir) if f.endswith(".html")]
                send_json({"status": "success", "reports": files})
                
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            self.send_error(500, f"Database error: {str(e)}")
        finally:
            conn.close()

    def handle_api_post(self, path):
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}

        def send_json(payload, code=200):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))

        try:
            if path == "/api/pipeline/run":
                period = data.get("period", "2024-Q1")
                # Pre-populate sample document parsing triggers if requested
                docs = []
                if data.get("load_samples"):
                    # Mock files
                    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
                    os.makedirs(reports_dir, exist_ok=True)
                    docs = [
                        "green_energy_bill.pdf",
                        "alpha_shipping_manifest.xlsx",
                        "beta_steel_invoice.pdf"
                    ]
                    # Write dummy empty documents if not present to mock ingestion
                    for doc in docs:
                        open(os.path.join(reports_dir, doc), "w").close()
                        
                orch = OrchestratorAgent()
                res = orch.run_pipeline(period, document_paths=docs)
                send_json(res)
                
            elif path == "/api/anomalies/resolve":
                anomaly_id = data.get("anomaly_id")
                reason = data.get("reason_code", "data_entry_correction")
                approver = data.get("approver", "Dashboard Administrator")
                
                if not anomaly_id:
                    self.send_error(400, "Missing anomaly_id parameter")
                    return
                    
                anm = AnomalyDetectionAgent()
                anm.resolve_anomaly(anomaly_id, reason, approver)
                send_json({"status": "success", "message": f"Anomaly {anomaly_id} resolved successfully."})
                
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            self.send_error(500, f"Error processing request: {str(e)}")

def start_server(port=PORT):
    init_db()
    server = HTTPServer(('', port), EcoChainHTTPHandler)
    print(f"EcoChain 24 Dashboard available at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        server.server_close()
