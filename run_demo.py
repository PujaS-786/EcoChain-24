import os
import json
import sqlite3
from datetime import datetime
from ecochain.db import init_db, DB_FILE, verify_audit_trail_integrity
from ecochain.agents.orchestrator import OrchestratorAgent
from ecochain.agents.anomaly import AnomalyDetectionAgent

def populate_historical_baselines():
    """Populates historical logs so calculations and anomaly detection have baselines to evaluate against."""
    print("Populating historical baselines for supplier baseline calculations...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Clear tables to ensure a fresh demo run
    cursor.execute("DELETE FROM activity_records")
    cursor.execute("DELETE FROM emissions_records")
    cursor.execute("DELETE FROM supplier_profiles")
    cursor.execute("DELETE FROM anomalies")
    cursor.execute("DELETE FROM compliance_disclosures")
    cursor.execute("DELETE FROM recommendations")
    cursor.execute("DELETE FROM alerts")
    cursor.execute("DELETE FROM audit_trail")
    cursor.execute("DELETE FROM config_store")
    
    # Setup supplier profiles
    suppliers = [
        ("sup_green_energy", "Green Energy Corp", "Tier A", 0.95, 0.22, "improving", "2023-12-15Z"),
        ("sup_alpha_logistics", "Alpha Logistics Co", "Tier B", 0.88, 0.45, "stable", "2023-12-18Z"),
        ("sup_beta_steel", "Beta Steel Ltd", "Tier D", 0.35, 1.85, "declining", "2023-11-20Z")
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO supplier_profiles VALUES (?, ?, ?, ?, ?, ?, ?)",
        suppliers
    )
    
    # Setup historical emissions logs for statistical baselines (average around 400 tons/quarter)
    # sup_green_energy historical activity record + emissions record
    cursor.execute("""
        INSERT OR REPLACE INTO activity_records VALUES 
        ('rec_hist_1', 'sup_green_energy', 'utility_api', 'verified', 0.95, '2023-12-15T08:00:00Z', 
         'electricity', 12000.0, 'kWh', 'US', '2023-Q4', '{"tariff_type":"renewable"}')
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO emissions_records VALUES
        ('rec_hist_1', 'sup_green_energy', 2, 'Scope 2 — Indirect Purchased Energy', 
         4440.0, 0.0, 'IEA-2024-V2 (0.37 kg CO2e/kWh)', 'market-based', 0.95, '2023-12-15T08:05:00Z')
    """)
    
    # sup_beta_steel historical emissions
    cursor.execute("""
        INSERT OR REPLACE INTO activity_records VALUES 
        ('rec_hist_2', 'sup_beta_steel', 'accounting_erp', 'estimated', 0.60, '2023-11-20T10:00:00Z', 
         'spend', 100000.0, 'USD', 'US', '2023-Q4', '{"sector":"steel_metals"}')
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO emissions_records VALUES
        ('rec_hist_2', 'sup_beta_steel', 3, 'Scope 3 — Upstream Purchased Goods', 
         150000.0, 150000.0, 'EEIO-US-2024 (1.50 kg CO2e/USD)', 'spend-based', 0.51, '2023-11-20T10:10:00Z')
    """)

    conn.commit()
    conn.close()
    print("Historical data populate complete.")

def main():
    print("Initializing EcoChain 24 Multi-Agent Registry...")
    init_db()
    
    # Initialize baselines
    populate_historical_baselines()
    
    print("\n--- STAGE 1: Running Pipeline Conductor ---")
    # Feed the pipeline with active supplier disclosures
    active_sups = [
        {"supplier_id": "sup_green_energy", "name": "Green Energy Corp"},
        {"supplier_id": "sup_alpha_logistics", "name": "Alpha Logistics Co"},
        {"supplier_id": "sup_beta_steel", "name": "Beta Steel Ltd"}
    ]
    
    # We will pass some mock documents to ingest representing energy invoices and shipping sheets
    docs = [
        "green_energy_bill.pdf",
        "alpha_shipping_manifest.xlsx",
        "beta_steel_invoice.pdf"
    ]
    
    # Create empty mock source documents in reports folder to satisfy files checks
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for doc in docs:
        open(os.path.join(reports_dir, doc), "w").close()
        
    orch = OrchestratorAgent()
    res = orch.run_pipeline("2024-Q1", document_paths=[os.path.join(reports_dir, d) for d in docs], active_suppliers=active_sups)
    
    print("\nPipeline Complete. Outputs summary:")
    print(json.dumps(res, indent=2))
    
    print("\n--- STAGE 2: Verifying Cryptographic Audit Log Integrity ---")
    valid, errors = verify_audit_trail_integrity()
    if valid:
        print("SUCCESS: Immutable log verification checked. 0 records tampered.")
    else:
        print("CRITICAL: Chain validation error:")
        for err in errors:
            print(f"- {err}")

    print("\n--- STAGE 3: Fetching Active System Anomalies ---")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT anomaly_id, anomaly_type, severity, plain_language_description, status FROM anomalies")
    anms = cursor.fetchall()
    print(f"Discovered {len(anms)} active system anomalies:")
    for a in anms:
        print(f"- [{a[2]}] ID: {a[0]} | Type: {a[1]} | Status: {a[4]} | Description: {a[3]}")
        
    # Manual Override Resolution Demonstration
    if anms:
        target_anomaly = anms[0][0]
        print(f"\nDemonstrating manual auditor override for anomaly: {target_anomaly}")
        detector = AnomalyDetectionAgent()
        detector.resolve_anomaly(target_anomaly, "verified_invoice_override", "Director of Supply Chain Audit")
        
        # Re-check status
        cursor.execute("SELECT status, resolution_reason, resolved_by FROM anomalies WHERE anomaly_id = ?", (target_anomaly,))
        resolved = cursor.fetchone()
        print(f"Updated status: {resolved[0]} | Code: {resolved[1]} | Auditor: {resolved[2]}")
        
    conn.close()

if __name__ == "__main__":
    main()
