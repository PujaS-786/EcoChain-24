---
name: "EcoChain MCP Tools"
description: "Model Context Protocol tool definitions for EcoChain 24 multi-agent system. Registers all available tools for agent execution."
---

# MCP Tool Registry — EcoChain 24

## Available Tools

### Ingestion Tools
```json
{
  "ecochain.ingest.normalize": {
    "description": "Normalize raw supplier record to standard format",
    "inputs": {
      "raw_record": "dict - Raw data from supplier"
    },
    "output": "Standardized activity record"
  },
  "ecochain.ingest.parse_document": {
    "description": "Parse PDF, Excel, or JSON document from supplier",
    "inputs": {
      "document_path": "str - File path to document",
      "format": "str - pdf | excel | json"
    },
    "output": "Parsed records with extracted data"
  },
  "ecochain.ingest.check_submissions": {
    "description": "Check for overdue supplier submissions",
    "inputs": {
      "suppliers": "list - Supplier IDs",
      "period": "str - Q1 2024 format"
    },
    "output": "List of overdue submissions"
  }
}
```

### Calculation Tools
```json
{
  "ecochain.calculate.emissions": {
    "description": "Calculate Scope 1, 2, or 3 emissions from activity record",
    "inputs": {
      "record_id": "str - Activity record ID",
      "scope": "int - 1, 2, or 3"
    },
    "output": "Emissions record with tCO2e value and methodology"
  },
  "ecochain.calculate.apply_factor": {
    "description": "Apply emission factor to activity quantity",
    "inputs": {
      "activity": "str - e.g., 'natural_gas', 'electricity'",
      "quantity": "float - Amount in source units",
      "region": "str - Geographic region (optional)"
    },
    "output": "Calculated emissions in tCO2e"
  }
}
```

### Audit Tools
```json
{
  "ecochain.audit.validate": {
    "description": "Validate record completeness and data quality",
    "inputs": {
      "record_id": "str - Record to validate"
    },
    "output": "Data quality score (0-100%) and gap list"
  },
  "ecochain.audit.classify_supplier": {
    "description": "Classify supplier into tier (A/B/C/D)",
    "inputs": {
      "supplier_id": "str - Supplier ID"
    },
    "output": "Tier classification and trend (improving/stable/declining)"
  }
}
```

### Anomaly Detection Tools
```json
{
  "ecochain.anomaly.check": {
    "description": "Check for statistical deviations in dataset",
    "inputs": {
      "period": "str - Time period to check"
    },
    "output": "List of flagged anomalies with deviation %"
  },
  "ecochain.anomaly.resolve": {
    "description": "Mark anomaly as resolved with resolution code",
    "inputs": {
      "anomaly_id": "str - Anomaly ID",
      "resolution_code": "str - verified_override | data_error | investigating"
    },
    "output": "Updated anomaly status"
  }
}
```

### Compliance Tools
```json
{
  "ecochain.comply.check": {
    "description": "Verify compliance against framework requirements",
    "inputs": {
      "frameworks": "list - GRI, TCFD, SASB, ISO, SEC, CSRD",
      "period": "str - Reporting period"
    },
    "output": "Compliance scorecard with gap analysis"
  }
}
```

### Recommendation Tools
```json
{
  "ecochain.recommend.generate": {
    "description": "Generate carbon reduction opportunities",
    "inputs": {
      "focus": "str - all | supplier | energy | logistics",
      "budget": "float - Optional investment budget"
    },
    "output": "List of opportunities ranked by ROI"
  },
  "ecochain.recommend.model_scenario": {
    "description": "Model emissions reduction from specific action",
    "inputs": {
      "action": "str - e.g., 'renewable_energy', 'supplier_switch'",
      "implementation_date": "str - YYYY-MM-DD"
    },
    "output": "Projected savings and timeline"
  }
}
```

### Report Tools
```json
{
  "ecochain.report.generate": {
    "description": "Generate HTML report of specified type",
    "inputs": {
      "report_type": "str - board_summary | ghg_inventory | supplier_scorecard",
      "period": "str - Q1 2024 format"
    },
    "output": "HTML file path + URL"
  }
}
```

### Logging Tools
```json
{
  "ecochain.log.write": {
    "description": "Write immutable audit trail entry",
    "inputs": {
      "agent_name": "str - Calling agent ID",
      "action": "str - Action type",
      "details": "dict - Context and details"
    },
    "output": "Entry ID and hash"
  }
}
```

---

## Tool Authorization

Each agent has scoped access:

| Agent | Allowed Tools | Permissions |
|-------|---------------|-------------|
| orchestrator | All | Full system access |
| ingest | ecochain.ingest.* + log | Parse and normalize |
| calculate | ecochain.calculate.* + log | Emit factor application |
| audit | ecochain.audit.* + log | Data quality validation |
| anomaly | ecochain.anomaly.* + log | Deviation detection |
| comply | ecochain.comply.* + log | Standards verification |
| recommend | ecochain.recommend.* + log | Strategy generation |
| report | ecochain.report.* + log | Report generation |

---

## Example Tool Calls

### Calculate Emissions
```
Call: ecochain.calculate.emissions
Input: {
  "record_id": "rec_20260701_001",
  "scope": 2
}
Output: {
  "emissions_id": "em_001",
  "co2e": 185.0,
  "methodology": "IEA-2024-V2 US Grid",
  "confidence": 0.95
}
```

### Check Compliance
```
Call: ecochain.comply.check
Input: {
  "frameworks": ["GRI", "TCFD"],
  "period": "2024-Q1"
}
Output: {
  "GRI": {"score": 95, "gaps": 1, "issues": [...]},
  "TCFD": {"score": 100, "gaps": 0, "issues": []}
}
```

### Generate Recommendations
```
Call: ecochain.recommend.generate
Input: {
  "focus": "all",
  "budget": 50000
}
Output: [
  {
    "id": "rec_001",
    "title": "Renewable Energy",
    "saving_tco2e": 2035,
    "cost": -1200,
    "roi": "High",
    "effort": "Low"
  },
  ...
]
```

---

## Rate Limiting

- **Per Agent**: 100 calls/minute
- **Per Tool**: 50 calls/minute
- **Database**: 1000 queries/minute

---

## Error Handling

All tools return structured responses:
```json
{
  "status": "success|error|pending",
  "data": {},
  "error": "Error message if status=error",
  "audit_entry_id": "entry_xyz",
  "timestamp": "2026-07-02T18:16:10Z"
}
```

---

## Integration with ADK

Tools are auto-discovered from `.github/hooks/` and agent manifests.  
No additional registration needed beyond files in version control.
