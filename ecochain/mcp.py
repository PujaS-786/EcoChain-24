import json
import uuid
import os
import hashlib
from datetime import datetime
from ecochain.db import get_connection, log_audit_entry

# Versioned factor datasets
EMISSION_FACTORS = {
    "fuel": {
        "natural_gas": {"value": 2.02, "unit": "kg CO2e/m3", "version": "GHG-2024-V1"},
        "diesel": {"value": 2.68, "unit": "kg CO2e/L", "version": "GHG-2024-V1"},
        "petrol": {"value": 2.31, "unit": "kg CO2e/L", "version": "GHG-2024-V1"},
        "lpg": {"value": 1.51, "unit": "kg CO2e/L", "version": "GHG-2024-V1"}
    },
    "electricity": {
        "US": {"value": 0.37, "unit": "kg CO2e/kWh", "version": "IEA-2024-V2"},
        "DE": {"value": 0.35, "unit": "kg CO2e/kWh", "version": "IEA-2024-V2"},
        "JP": {"value": 0.42, "unit": "kg CO2e/kWh", "version": "IEA-2024-V2"},
        "CN": {"value": 0.58, "unit": "kg CO2e/kWh", "version": "IEA-2024-V2"},
        "GLOBAL_AVG": {"value": 0.45, "unit": "kg CO2e/kWh", "version": "IEA-2024-V2"}
    },
    "logistics": {
        "air": {"value": 1.20, "unit": "kg CO2e/t-km", "version": "GLEC-2024-V1.2"},
        "road": {"value": 0.08, "unit": "kg CO2e/t-km", "version": "GLEC-2024-V1.2"},
        "rail": {"value": 0.02, "unit": "kg CO2e/t-km", "version": "GLEC-2024-V1.2"},
        "sea": {"value": 0.01, "unit": "kg CO2e/t-km", "version": "GLEC-2024-V1.2"}
    },
    "agriculture": {
        "beef_cattle": {"value": 80.0, "unit": "kg CO2e/head/yr", "version": "IPCC-Tier1-2024"},
        "dairy_cow": {"value": 120.0, "unit": "kg CO2e/head/yr", "version": "IPCC-Tier1-2024"},
        "nitrogen_fertilizer": {"value": 8.0, "unit": "kg CO2e/kg", "version": "IPCC-Tier1-2024"}
    },
    "eeio": {
        "steel_metals": {"value": 1.50, "unit": "kg CO2e/USD", "version": "EEIO-US-2024"},
        "chemicals_plastics": {"value": 2.10, "unit": "kg CO2e/USD", "version": "EEIO-US-2024"},
        "electronics_it": {"value": 0.40, "unit": "kg CO2e/USD", "version": "EEIO-US-2024"},
        "paper_packaging": {"value": 0.80, "unit": "kg CO2e/USD", "version": "EEIO-US-2024"},
        "general_services": {"value": 0.05, "unit": "kg CO2e/USD", "version": "EEIO-US-2024"}
    }
}

# Framework mappings for compliance
FRAMEWORK_REQUIREMENTS = {
    "GHG_Protocol": [
        {"id": "GHG-1.1", "name": "Scope 1 Completeness", "desc": "Account for all direct combustion and process emissions"},
        {"id": "GHG-2.1", "name": "Scope 2 Dual Reporting", "desc": "Provide both Location-based and Market-based Scope 2 figures"}
    ],
    "CSRD_ESRS_E1": [
        {"id": "ESRS-E1-4", "name": "Double Materiality Assessment", "desc": "Verify physical and transition risk materiality"},
        {"id": "ESRS-E1-6", "name": "Value Chain Scope 3 Disclosures", "desc": "Provide Scope 3 emissions across all relevant categories"}
    ],
    "TCFD": [
        {"id": "TCFD-MET-1", "name": "Metrics and Targets", "desc": "Disclose Scope 1, Scope 2, and, if appropriate, Scope 3 greenhouse gas emissions and the related risks."}
    ],
    "ISO_14064": [
        {"id": "ISO-14064-1", "name": "Boundary setting and data quality", "desc": "Document boundaries and run anomaly logs check"}
    ],
    "SBTi": [
        {"id": "SBTI-ALIGN", "name": "Net-Zero target alignment check", "desc": "Track progress on Scope 1, 2, and 3 reduction targets"}
    ],
    "SFDR": [
        {"id": "SFDR-PAI-1", "name": "GHG emissions and carbon footprint", "desc": "Track mandatory Principal Adverse Impact indicators for portfolio"}
    ],
    "SEC_Climate": [
        {"id": "SEC-DISC", "name": "Material climate risks", "desc": "Disclose Scope 1 and 2 emissions if material to investors"}
    ]
}

# Service identity tokens (hardcoded mapping for simplicity of validation)
AGENT_TOKENS = {
    "orchestrator": "tok_orchestrator_secret_1234",
    "ingest": "tok_ingest_secret_2234",
    "calculate": "tok_calculate_secret_3234",
    "audit": "tok_audit_secret_4234",
    "anomaly": "tok_anomaly_secret_5234",
    "comply": "tok_comply_secret_6234",
    "report": "tok_report_secret_7234",
    "recommend": "tok_recommend_secret_8234",
    "alert": "tok_alert_secret_9234",
    "log": "tok_log_secret_0234"
}

def authorize_agent(agent_name: str, token: str, tool_name: str) -> bool:
    """Enforces token verification and namespace constraints.
    - Orchestrator can call any tool.
    - Agents can only call tools in their namespace (e.g. Ingest -> ecochain.ingest.*) + ecochain.log.
    """
    if AGENT_TOKENS.get(agent_name) != token:
        return False
    
    if agent_name == "orchestrator":
        return True # Conductors have full privileges
    
    # Check namespace
    allowed_prefix = f"ecochain.{agent_name}."
    if tool_name.startswith(allowed_prefix) or tool_name.startswith("ecochain.log."):
        return True
        
    return False

# INGEST TOOLS
def ingest_normalize_record(data: dict) -> dict:
    """Normalizes activity data inputs into a standard schema."""
    activity_type = data.get("activity_type")
    quantity = float(data.get("quantity", 0))
    unit = data.get("unit")
    country = data.get("country", "US")
    period = data.get("period")
    supplier_id = data.get("supplier_id")
    source = data.get("data_source", "manual")
    
    # Simple quality assessment
    data_quality = data.get("data_quality", "verified")
    confidence = float(data.get("confidence_score", 1.0))
    
    # Generate record_id deterministically if not present to avoid duplication
    if "record_id" not in data:
        # Extract filename if it is a parsed document path to make it path-agnostic
        source_clean = source
        if source_clean.startswith("parsed_document:"):
            doc_name = os.path.basename(source_clean.split("parsed_document:")[-1])
            source_clean = f"parsed_document:{doc_name}"
            
        key_str = f"{supplier_id}_{source_clean}_{activity_type}_{period}"
        record_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()[:12]
        record_id = f"rec_{record_hash}"
    else:
        record_id = data["record_id"]
        
    ingested_at = datetime.utcnow().isoformat() + "Z"
    
    normalized = {
        "record_id": record_id,
        "supplier_id": supplier_id,
        "data_source": source,
        "data_quality": data_quality,
        "confidence_score": confidence,
        "ingested_at": ingested_at,
        "activity_type": activity_type,
        "quantity": quantity,
        "unit": unit,
        "country": country,
        "period": period,
        "details": json.dumps(data.get("details", {}))
    }
    return normalized

def ingest_parse_document(doc_path: str) -> dict:
    """Simulates parsing a document (e.g. PDF/Excel invoice) with text extraction."""
    # In a real environment, read file bytes, run parse algorithms
    # Mocking behavior based on filename keywords
    base = doc_path.lower()
    
    # Setup dummy supplier IDs for mocking
    supplier_id = "sup_default"
    if "green" in base:
        supplier_id = "sup_green_energy"
    elif "alpha" in base:
        supplier_id = "sup_alpha_logistics"
    elif "beta" in base:
        supplier_id = "sup_beta_steel"
        
    # Default outputs
    parsed_data = {
        "activity_type": "fuel",
        "quantity": 1200.0,
        "unit": "L",
        "country": "US",
        "period": "2024-Q1",
        "supplier_id": supplier_id,
        "data_source": f"parsed_document:{os.path.basename(doc_path)}",
        "data_quality": "verified",
        "confidence_score": 0.85,
        "details": {"fuel_type": "diesel"}
    }
    
    if "electricity" in base or "bill" in base:
        parsed_data["activity_type"] = "electricity"
        parsed_data["quantity"] = 5500.0
        parsed_data["unit"] = "kWh"
        parsed_data["details"] = {"tariff_type": "standard"}
        if "renewable" in base:
            parsed_data["details"]["tariff_type"] = "renewable"
            parsed_data["confidence_score"] = 0.95
    elif "manifest" in base or "shipping" in base or "route" in base:
        parsed_data["activity_type"] = "logistics"
        parsed_data["quantity"] = 15000.0 # t-km
        parsed_data["unit"] = "t-km"
        parsed_data["details"] = {"transport_mode": "road", "fuel_type": "diesel"}
        parsed_data["confidence_score"] = 0.90
    elif "low_conf" in base:
        parsed_data["confidence_score"] = 0.65 # Will trigger quarantine
        
    return parsed_data

# CALCULATION TOOLS
def calculate_factor_lookup(activity_type: str, country: str, year: str, details: dict) -> tuple[float, str, str, float]:
    """Looks up versioned factors, applying confidence deduction for regional fallbacks."""
    penalty = 0.0
    if activity_type == "fuel":
        fuel_type = details.get("fuel_type", "diesel")
        f_data = EMISSION_FACTORS["fuel"].get(fuel_type, EMISSION_FACTORS["fuel"]["diesel"])
        return f_data["value"], f_data["unit"], f_data["version"], 1.0
        
    elif activity_type == "electricity":
        # Check Scope 2 location-based factor
        f_data = EMISSION_FACTORS["electricity"].get(country)
        if not f_data:
            # Fallback to regional average and deduct 0.10 confidence
            f_data = EMISSION_FACTORS["electricity"]["GLOBAL_AVG"]
            penalty = 0.10
        return f_data["value"], f_data["unit"], f_data["version"], 1.0 - penalty
        
    elif activity_type == "logistics":
        mode = details.get("transport_mode", "road")
        f_data = EMISSION_FACTORS["logistics"].get(mode, EMISSION_FACTORS["logistics"]["road"])
        return f_data["value"], f_data["unit"], f_data["version"], 1.0
        
    elif activity_type == "agriculture":
        ag_type = details.get("ag_type", "beef_cattle")
        f_data = EMISSION_FACTORS["agriculture"].get(ag_type, EMISSION_FACTORS["agriculture"]["beef_cattle"])
        return f_data["value"], f_data["unit"], f_data["version"], 1.0
        
    elif activity_type == "spend" or activity_type == "eeio":
        sector = details.get("sector", "general_services")
        f_data = EMISSION_FACTORS["eeio"].get(sector, EMISSION_FACTORS["eeio"]["general_services"])
        return f_data["value"], f_data["unit"], f_data["version"], 0.85 # EEIO baseline is lower confidence
        
    # Default fallback
    return 0.1, "kg CO2e/unit", "FALLBACK-V1", 0.50

# DISPATCHER
def call_mcp_tool(agent_name: str, token: str, tool_name: str, args: dict) -> dict:
    """Entry point for executing registered tools via MCP."""
    if not authorize_agent(agent_name, token, tool_name):
        log_audit_entry("mcp_server", "authorization_failure", {
            "agent_name": agent_name,
            "tool_name": tool_name,
            "reason": "Token scope mismatch or invalid token"
        })
        return {"status": "error", "message": f"Unauthorized tool execution: {tool_name} for agent {agent_name}"}
        
    try:
        # Write to log namespace tool
        if tool_name == "ecochain.log.write":
            entry_hash = log_audit_entry(args.get("calling_agent"), args.get("action"), args.get("details"))
            return {"status": "success", "entry_hash": entry_hash}
            
        elif tool_name == "ecochain.ingest.normalize_record":
            normalized = ingest_normalize_record(args.get("data"))
            return {"status": "success", "record": normalized}
            
        elif tool_name == "ecochain.ingest.parse_document":
            parsed = ingest_parse_document(args.get("doc_path"))
            return {"status": "success", "parsed_data": parsed}
            
        elif tool_name == "ecochain.ingest.check_connection":
            return {"status": "success", "connected": True, "ping_ms": 15}
            
        elif tool_name == "ecochain.calculate.factor_lookup":
            val, unit, ver, conf = calculate_factor_lookup(
                args.get("activity_type"),
                args.get("country"),
                args.get("year", "2024"),
                args.get("details", {})
            )
            return {"status": "success", "value": val, "unit": unit, "version": ver, "confidence": conf}
            
        elif tool_name == "ecochain.alert.dispatch":
            conn = get_connection()
            cursor = conn.cursor()
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            timestamp = datetime.utcnow().isoformat() + "Z"
            cursor.execute(
                "INSERT INTO alerts (alert_id, timestamp, supplier_id, severity, message, channel, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (alert_id, timestamp, args.get("supplier_id"), args.get("severity"), args.get("message"), args.get("channel", "email"), "unread")
            )
            conn.commit()
            conn.close()
            return {"status": "success", "alert_id": alert_id}
            
        else:
            return {"status": "error", "message": f"Tool {tool_name} not implemented in MCP registry"}
            
    except Exception as e:
        log_audit_entry("mcp_server", "tool_execution_error", {
            "agent_name": agent_name,
            "tool_name": tool_name,
            "error": str(e)
        })
        return {"status": "error", "message": f"Exception raised during tool execution: {str(e)}"}
