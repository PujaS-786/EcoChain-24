import os
import json
from datetime import datetime
from ecochain.agents.base import Agent
from ecochain.db import get_connection

class ReportAgent(Agent):
    def __init__(self):
        super().__init__("report")
        
    def generate_report(self, report_type: str, period: str) -> str:
        """Generates a beautifully formatted HTML carbon intelligence report or a Gap Notice."""
        self.log_action("generate_report_start", {"type": report_type, "period": period})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Calculate Coverage and Confidence
        cursor.execute("""
            SELECT e.co2e, e.confidence_score, a.data_quality, a.data_source
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            WHERE a.period = ?
        """, (period,))
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            # If no data, write a Gap Notice
            return self._write_gap_notice(report_type, period, "No data available in emissions database.", 0.0, 0.0, [])
            
        total_records = len(rows)
        verified_count = sum(1 for r in rows if r[2] == "verified")
        coverage_pct = (verified_count / total_records * 100.0) if total_records > 0 else 0.0
        avg_confidence = sum(r[1] for r in rows) / total_records if total_records > 0 else 0.0
        data_sources = list(set(r[3] for r in rows))
        
        # Check coverage threshold (60% limit for compliance reports)
        is_compliance_report = report_type in ["ghg_inventory", "csrd_package", "tcfd_report", "iso_verification"]
        if is_compliance_report and coverage_pct < 60.0:
            conn.close()
            reason = f"Verified data coverage of {coverage_pct:.1f}% falls below the mandatory 60% regulatory threshold."
            return self._write_gap_notice(report_type, period, reason, coverage_pct, avg_confidence, data_sources)
            
        # Get data based on report type
        report_data = {}
        
        # Fetch emissions by scope
        cursor.execute("""
            SELECT scope, SUM(co2e), SUM(co2e_market)
            FROM emissions_records e
            JOIN activity_records a ON e.record_id = a.record_id
            WHERE a.period = ?
            GROUP BY scope
        """, (period,))
        scopes = cursor.fetchall()
        report_data["scopes"] = {s[0]: {"location": s[1], "market": s[2] if s[2] is not None else s[1]} for s in scopes}
        
        # Fetch supplier ratings
        cursor.execute("SELECT name, tier, data_quality_score, emission_intensity, trend FROM supplier_profiles")
        suppliers = cursor.fetchall()
        report_data["suppliers"] = [
            {"name": s[0], "tier": s[1], "dq_score": s[2], "intensity": s[3], "trend": s[4]} for s in suppliers
        ]
        
        # Fetch compliance disclosures
        cursor.execute("SELECT framework, requirement_id, status, missing_data, risk_level FROM compliance_disclosures")
        disclosures = cursor.fetchall()
        report_data["disclosures"] = [
            {"framework": d[0], "req_id": d[1], "status": d[2], "missing": d[3], "risk": d[4]} for d in disclosures
        ]
        
        # Fetch recommendations and filter by current period's data_basis
        cursor.execute("SELECT category, estimated_co2e_saving, implementation_effort, estimated_cost_delta, confidence_in_estimate, data_basis FROM recommendations")
        recs = cursor.fetchall()
        
        # Get active record IDs for this period to verify basis
        cursor.execute("SELECT record_id FROM activity_records WHERE period = ?", (period,))
        period_record_ids = set(row[0] for row in cursor.fetchall())
        
        filtered_recs = []
        for r in recs:
            try:
                basis_ids = json.loads(r[5])
                if any(bid in period_record_ids for bid in basis_ids):
                    filtered_recs.append(r)
            except Exception:
                filtered_recs.append(r)
                
        report_data["recommendations"] = [
            {"category": r[0], "saving": r[1], "effort": r[2], "cost_delta": r[3], "confidence": r[4]} for r in filtered_recs
        ]
        
        # Fetch anomalies (resolved vs open)
        cursor.execute("SELECT anomaly_type, severity, status, plain_language_description, resolution_reason FROM anomalies")
        anms = cursor.fetchall()
        report_data["anomalies"] = [
            {"type": a[0], "severity": a[1], "status": a[2], "desc": a[3], "resolved_reason": a[4]} for a in anms
        ]
        
        conn.close()
        
        # 2. Write HTML document
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"{report_type}_{period}_{datetime.utcnow().strftime('%Y%m%d')}.html"
        filepath = os.path.join(reports_dir, filename)
        
        html_content = self._build_html_document(report_type, period, report_data, coverage_pct, avg_confidence, data_sources)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        self.log_action("generate_report_success", {"type": report_type, "filepath": filepath})
        return filepath
        
    def get_lineage(self, record_id: str) -> dict:
        """Traces the complete lineage from a raw record to calculated emissions and audit logs."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM activity_records WHERE record_id = ?", (record_id,))
        raw_row = cursor.fetchone()
        
        if not raw_row:
            conn.close()
            return {"status": "error", "message": f"Lineage error: Record {record_id} not found."}
            
        cursor.execute("SELECT * FROM emissions_records WHERE record_id = ?", (record_id,))
        em_row = cursor.fetchone()
        
        # Retrieve logs relating to this record
        cursor.execute("SELECT timestamp, agent_name, action, details FROM audit_trail WHERE details LIKE ?", (f"%{record_id}%",))
        logs = cursor.fetchall()
        conn.close()
        
        lineage = {
            "record_id": record_id,
            "raw_input": {
                "supplier_id": raw_row[1],
                "data_source": raw_row[2],
                "data_quality": raw_row[3],
                "confidence_score": raw_row[4],
                "ingested_at": raw_row[5],
                "activity_type": raw_row[6],
                "quantity": raw_row[7],
                "unit": raw_row[8],
                "country": raw_row[9],
                "period": raw_row[10],
                "details": json.loads(raw_row[11]) if raw_row[11] else {}
            },
            "calculation_output": {
                "scope": em_row[2],
                "category": em_row[3],
                "co2e": em_row[4],
                "co2e_market": em_row[5],
                "emission_factor_used": em_row[6],
                "calculation_method": em_row[7],
                "confidence_score": em_row[8],
                "calculated_at": em_row[9]
            } if em_row else None,
            "audit_trail_events": [
                {"timestamp": l[0], "agent": l[1], "action": l[2], "details": json.loads(l[3])} for l in logs
            ]
        }
        return lineage
        
    def _write_gap_notice(self, report_type: str, period: str, reason: str, coverage: float, confidence: float, sources: list) -> str:
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"gap_notice_{report_type}_{period}.html"
        filepath = os.path.join(reports_dir, filename)
        
        sources_str = ", ".join(sources) if sources else "None connected"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Regulatory Gap Notice — {report_type.upper()}</title>
    <style>
        body {{
            background: #0f172a;
            color: #f8fafc;
            font-family: 'Outfit', 'Inter', sans-serif;
            margin: 0;
            padding: 40px;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 16px;
            padding: 30px;
            max-width: 700px;
            margin: 50px auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(239, 68, 68, 0.15);
        }}
        h1 {{
            color: #ef4444;
            font-size: 24px;
            margin-top: 0;
            border-bottom: 1px solid rgba(239, 68, 68, 0.2);
            padding-bottom: 15px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
            background: rgba(15, 23, 42, 0.4);
            padding: 15px;
            border-radius: 8px;
        }}
        .metric {{
            text-align: center;
            flex: 1;
        }}
        .metric-val {{
            font-size: 20px;
            font-weight: bold;
            color: #ef4444;
        }}
        .metric-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: #94a3b8;
            margin-top: 5px;
        }}
        p {{
            line-height: 1.6;
            color: #cbd5e1;
        }}
        ul {{
            color: #cbd5e1;
            line-height: 1.6;
        }}
        footer {{
            margin-top: 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 15px;
            font-size: 11px;
            color: #64748b;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Regulatory Gap Notice</h1>
        <p><strong>Report:</strong> {report_type.replace('_', ' ').upper()}</p>
        <p><strong>Period:</strong> {period}</p>
        
        <div class="metric-row">
            <div class="metric">
                <div class="metric-val">{coverage:.1f}%</div>
                <div class="metric-label">Data Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-val">{confidence:.2f}</div>
                <div class="metric-label">Avg Confidence</div>
            </div>
        </div>
        
        <p><strong>Reason for Non-Issuance:</strong></p>
        <p style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px;">
            {reason}
        </p>
        
        <p><strong>Required Actions to Resolve Gaps:</strong></p>
        <ul>
            <li>Contact suppliers with missing or unverified energy invoices.</li>
            <li>Retrieve raw utility energy bills to increase data completeness above 60.0% coverage.</li>
            <li>Run the anomaly audit check on pending data submissions.</li>
        </ul>
        
        <footer>
            Report Type: {report_type} | Generated: {timestamp} | Data Coverage: {coverage:.1f}% | Confidence Score: {confidence:.2f} | Sources: {sources_str}
        </footer>
    </div>
</body>
</html>"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        self.log_action("generate_gap_notice", {"type": report_type, "filepath": filepath})
        return filepath
        
    def _build_html_document(self, report_type: str, period: str, data: dict, coverage: float, confidence: float, sources: list) -> str:
        timestamp = datetime.utcnow().isoformat() + "Z"
        sources_str = ", ".join(sources) if sources else "None connected"
        
        # Build section content based on scopes
        s1 = data["scopes"].get(1, {"location": 0.0, "market": 0.0})
        s2 = data["scopes"].get(2, {"location": 0.0, "market": 0.0})
        s3 = data["scopes"].get(3, {"location": 0.0, "market": 0.0})
        total_loc = s1["location"] + s2["location"] + s3["location"]
        total_mkt = s1["market"] + s2["market"] + s3["market"]
        
        # Format HTML with a premium CSS look (harmonious colors, dark mode, Outfit fonts, etc.)
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report_type.replace('_', ' ').upper()} — EcoChain 24</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 30, 49, 0.7);
            --accent-glow: rgba(59, 130, 246, 0.15);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.08);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 40px;
        }}
        .header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 40px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header p {{
            margin: 5px 0 0 0;
            color: var(--text-secondary);
        }}
        .meta-box {{
            text-align: right;
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;
        }}
        .card:hover {{
            transform: translateY(-2px);
        }}
        .metric-title {{
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            margin-top: 10px;
            color: #3b82f6;
        }}
        .metric-sub {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 5px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin: 30px 0 15px 0;
            border-left: 4px solid #3b82f6;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-secondary);
            font-size: 13px;
            text-transform: uppercase;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-met {{ background: rgba(16, 185, 129, 0.15); color: var(--success); }}
        .badge-partial {{ background: rgba(245, 158, 11, 0.15); color: var(--warning); }}
        .badge-gap {{ background: rgba(239, 68, 68, 0.15); color: var(--danger); }}
        
        .badge-a {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
        .badge-b {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; }}
        .badge-c {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
        .badge-d {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}

        footer {{
            margin-top: 60px;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
            font-size: 12px;
            color: var(--text-secondary);
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>{report_type.replace('_', ' ').upper()}</h1>
            <p>Carbon Accounting period: {period} | Organizational Boundary: Operations</p>
        </div>
        <div class="meta-box">
            <div>Verification Authority: EcoChain 24 Audit System</div>
            <div>Data coverage: {coverage:.1f}% | Avg Confidence: {confidence:.2f}</div>
        </div>
    </div>
    
    <div class="grid">
        <div class="card">
            <div class="metric-title">Scope 1 (Direct)</div>
            <div class="metric-value">{s1["location"]:.2f}</div>
            <div class="metric-sub">Tonnes CO₂e from fuel combustion</div>
        </div>
        <div class="card">
            <div class="metric-title">Scope 2 (Indirect Grid)</div>
            <div class="metric-value">{s2["location"]:.2f}</div>
            <div class="metric-sub">Dual market-based method: {s2["market"]:.2f} t CO₂e</div>
        </div>
        <div class="card">
            <div class="metric-title">Scope 3 (Supply Chain)</div>
            <div class="metric-value">{s3["location"]:.2f}</div>
            <div class="metric-sub">Upstream and logistics intensity</div>
        </div>
    </div>

    <div class="section-title">Summary Emissions Inventory (Dual-reporting metrics)</div>
    <table>
        <thead>
            <tr>
                <th>Scope Description</th>
                <th>Location-Based (t CO₂e)</th>
                <th>Market-Based (t CO₂e)</th>
                <th>Methodology applied</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Scope 1: Fuels & Process</td>
                <td>{s1["location"]:.4f}</td>
                <td>{s1["market"]:.4f}</td>
                <td>Physical primary factors</td>
            </tr>
            <tr>
                <td>Scope 2: Purchased Electricity</td>
                <td>{s2["location"]:.4f}</td>
                <td>{s2["market"]:.4f}</td>
                <td>Location vs. EAC dual reporting</td>
            </tr>
            <tr>
                <td>Scope 3: Shared Value Chain</td>
                <td>{s3["location"]:.4f}</td>
                <td>{s3["market"]:.4f}</td>
                <td>Physical & EEIO fallback calculations</td>
            </tr>
            <tr style="font-weight: 600; background: rgba(255,255,255,0.02);">
                <td>Total Footprint</td>
                <td>{total_loc:.4f}</td>
                <td>{total_mkt:.4f}</td>
                <td>Aggregated Carbon Inventory</td>
            </tr>
        </tbody>
    </table>

    <div class="section-title">Framework Disclosures status</div>
    <table>
        <thead>
            <tr>
                <th>Framework</th>
                <th>Requirement ID</th>
                <th>Status</th>
                <th>Lineage details / Gaps notes</th>
            </tr>
        </thead>
        <tbody>
            {"".join(f'''<tr>
                <td>{d["framework"]}</td>
                <td>{d["req_id"]}</td>
                <td><span class="badge badge-{d["status"].lower()}">{d["status"]}</span></td>
                <td>{d["missing"]}</td>
            </tr>''' for d in data["disclosures"])}
        </tbody>
    </table>

    <div class="section-title">Suppliers scoring summary</div>
    <table>
        <thead>
            <tr>
                <th>Supplier name</th>
                <th>Assigned tier</th>
                <th>Data quality score</th>
                <th>Emission Intensity (t CO₂e / unit)</th>
                <th>Trend direction</th>
            </tr>
        </thead>
        <tbody>
            {"".join(f'''<tr>
                <td>{s["name"]}</td>
                <td><span class="badge badge-{s["tier"][-1].lower()}">{s["tier"]}</span></td>
                <td>{s["dq_score"]:.2f}</td>
                <td>{s["intensity"]:.4f}</td>
                <td>{s["trend"]}</td>
            </tr>''' for s in data["suppliers"])}
        </tbody>
    </table>

    <div class="section-title">Optimization recommendations</div>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Est saving (t CO₂e/yr)</th>
                <th>Effort</th>
                <th>Est cost saving (USD)</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>
            {"".join(f'''<tr>
                <td>{r["category"]}</td>
                <td>{r["saving"]:.1f}</td>
                <td>{r["effort"]}</td>
                <td>{r["cost_delta"]:.2f}</td>
                <td>{r["confidence"]}</td>
            </tr>''' for r in data["recommendations"])}
        </tbody>
    </table>

    <footer>
        Report Type: {report_type.upper()} | Generated: {timestamp} | Data Coverage: {coverage:.1f}% | Confidence Score: {confidence:.2f} | Sources: {sources_str}
    </footer>
</body>
</html>"""
        return html
