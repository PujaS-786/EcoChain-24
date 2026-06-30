import sqlite3
import hashlib
import json
import os
import threading
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecochain.db")

_audit_log_lock = threading.RLock()

def get_connection():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Activity Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_records (
        record_id TEXT PRIMARY KEY,
        supplier_id TEXT,
        data_source TEXT,
        data_quality TEXT,
        confidence_score REAL,
        ingested_at TEXT,
        activity_type TEXT,
        quantity REAL,
        unit TEXT,
        country TEXT,
        period TEXT,
        details TEXT
    )
    """)
    
    # 2. Emissions Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emissions_records (
        record_id TEXT PRIMARY KEY,
        supplier_id TEXT,
        scope INTEGER,
        category TEXT,
        co2e REAL,
        co2e_market REAL,
        emission_factor_used TEXT,
        calculation_method TEXT,
        confidence_score REAL,
        calculated_at TEXT,
        FOREIGN KEY (record_id) REFERENCES activity_records(record_id)
    )
    """)
    
    # 3. Supplier Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_profiles (
        supplier_id TEXT PRIMARY KEY,
        name TEXT,
        tier TEXT,
        data_quality_score REAL,
        emission_intensity REAL,
        trend TEXT,
        last_disclosure_at TEXT
    )
    """)
    
    # 4. Anomalies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        anomaly_id TEXT PRIMARY KEY,
        anomaly_type TEXT,
        record_id TEXT,
        supplier_id TEXT,
        severity TEXT,
        plain_language_description TEXT,
        recommended_action TEXT,
        status TEXT,
        resolution_reason TEXT,
        resolved_by TEXT,
        detected_at TEXT,
        resolved_at TEXT
    )
    """)
    
    # 5. Compliance Disclosures Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compliance_disclosures (
        framework TEXT,
        requirement_id TEXT,
        status TEXT,
        missing_data TEXT,
        responsible_agent TEXT,
        deadline TEXT,
        risk_level TEXT,
        financial_exposure REAL,
        checked_at TEXT,
        PRIMARY KEY (framework, requirement_id)
    )
    """)
    
    # 6. Recommendations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        recommendation_id TEXT PRIMARY KEY,
        category TEXT,
        estimated_co2e_saving REAL,
        implementation_effort TEXT,
        estimated_cost_delta REAL,
        confidence_in_estimate TEXT,
        data_basis TEXT,
        created_at TEXT
    )
    """)
    
    # 7. Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id TEXT PRIMARY KEY,
        timestamp TEXT,
        supplier_id TEXT,
        severity TEXT,
        message TEXT,
        channel TEXT,
        status TEXT
    )
    """)
    
    # 8. Audit Trail Table (Append-only hash chain)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_trail (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        agent_name TEXT,
        action TEXT,
        details TEXT,
        previous_hash TEXT,
        content_hash TEXT
    )
    """)

    # 9. Config Store (e.g. active frameworks, period config)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_store (
        config_key TEXT PRIMARY KEY,
        config_value TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_audit_entry(agent_name: str, action: str, details_dict: dict) -> str:
    """Appends a cryptographically chained entry to the audit log."""
    with _audit_log_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        details_str = json.dumps(details_dict, sort_keys=True)
        
        # Find last entry to get its hash
        cursor.execute("SELECT entry_id, content_hash FROM audit_trail ORDER BY entry_id DESC LIMIT 1")
        last_row = cursor.fetchone()
        
        if last_row:
            previous_hash = last_row[1]
            next_id = last_row[0] + 1
        else:
            previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
            next_id = 1
            
        # Calculate hash: SHA-256 (id + timestamp + agent_name + action + details + previous_hash)
        hash_input = f"{next_id}{timestamp}{agent_name}{action}{details_str}{previous_hash}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()
        
        cursor.execute(
            "INSERT INTO audit_trail (entry_id, timestamp, agent_name, action, details, previous_hash, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (next_id, timestamp, agent_name, action, details_str, previous_hash, content_hash)
        )
        
        conn.commit()
        conn.close()
        return content_hash

def verify_audit_trail_integrity() -> tuple[bool, list[str]]:
    """Verifies that the entire audit trail hash chain is untampered."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT entry_id, timestamp, agent_name, action, details, previous_hash, content_hash FROM audit_trail ORDER BY entry_id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    errors = []
    expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    
    for idx, row in enumerate(rows):
        entry_id, timestamp, agent_name, action, details, prev_hash, stored_hash = row
        
        # Check if the previous_hash matches our expectation
        if prev_hash != expected_prev_hash:
            errors.append(f"Chain break at entry ID {entry_id}: expected prev_hash '{expected_prev_hash}', got '{prev_hash}'")
            
        # Recompute this entry's hash
        hash_input = f"{entry_id}{timestamp}{agent_name}{action}{details}{prev_hash}".encode('utf-8')
        computed_hash = hashlib.sha256(hash_input).hexdigest()
        
        if computed_hash != stored_hash:
            errors.append(f"Content hash mismatch at entry ID {entry_id}: computed '{computed_hash}', stored '{stored_hash}'")
            
        expected_prev_hash = stored_hash
        
    return len(errors) == 0, errors
