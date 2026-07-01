---
name: IngestionAgent
description: "Data normalization and document parsing specialist for EcoChain. Parses supplier invoices, utility records, and ERP exports. Validates data completeness and flags missing submissions. Use when: ingesting raw data from multiple sources, normalizing records across different formats, validating data quality before processing."
tools:
  - "normalize_record"
  - "ingest_document"
  - "check_overdue_submissions"
  - "parse_invoice"
  - "validate_record"
capabilities:
  - "Multi-format document parsing (PDF, Excel, JSON)"
  - "Record normalization across sources"
  - "Data completeness validation"
  - "Missing submission detection"
  - "Format standardization"
examples:
  - "Parse supplier invoice PDF and normalize to standard record"
  - "Check for overdue Q1 submissions from Alpha Logistics"
  - "Validate all activity records have required fields"
---

# Ingestion Agent

## Purpose
The Ingestion Agent is the first step in the carbon auditing pipeline. It handles raw data from multiple sources (supplier invoices, utility bills, ERP systems) and normalizes them into a standard format for downstream processing.

## Capabilities

- **Document Parsing**: Extract data from PDFs, spreadsheets, and JSON files
- **Record Normalization**: Convert diverse formats into standardized records
- **Validation**: Ensure all required fields are present and valid
- **Submission Tracking**: Monitor overdue supplier submissions
- **Error Logging**: Record parsing failures for manual review

## Supported Formats

| Format | Source | Status |
|--------|--------|--------|
| PDF | Supplier invoices | ✅ Active |
| Excel | Utility reports | ✅ Active |
| JSON | ERP systems | ✅ Active |
| CSV | Log files | ✅ Active |

## How to Use

**In ADK chat:**
> "Parse the supplier invoice from Alpha Logistics Q1 report"
> "Check for overdue submissions from all Tier A suppliers"
> "Normalize 3 records from the raw data dump"

**Direct call:**
```python
from ecochain.agents.ingest import IngestionAgent
agent = IngestionAgent()
record = agent.normalize_record(raw_data)
```

## Output
Standardized records with:
- Unique record ID
- Source attribution
- Timestamp
- Validated fields
- Data quality score
