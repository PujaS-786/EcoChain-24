---
name: run-emissions-audit
description: "Execute complete quarterly emissions audit workflow using EcoChain agents. Coordinates ingestion, calculation, compliance, and report generation. Use when: auditing emissions for a specific period, generating board reports, verifying compliance across all standards."
tools:
  - OrchestratorAgent
  - IngestionAgent
  - CalculationAgent
  - AuditAgent
  - AnomalyDetectionAgent
  - ComplianceAgent
  - ReportAgent
---

# Run Complete Emissions Audit

## Purpose
Execute the full EcoChain 24 multi-agent audit pipeline in a single workflow.

## What Happens

1. **Ingestion** – Load and normalize supplier records
2. **Calculation** – Compute emissions (Scope 1/2/3) in parallel
3. **Audit** – Validate data quality and supplier tiers
4. **Anomaly Detection** – Flag statistical deviations
5. **Compliance** – Verify GRI/TCFD/SASB alignment
6. **Reporting** – Generate HTML dashboards

## Inputs Required

- **Period**: Q1 2024, Q2 2024, etc. (format: YYYY-Q#)
- **Suppliers**: (Optional) Specific suppliers to audit, or "all" for full dataset
- **Standards**: (Optional) Which compliance frameworks to check (GRI, TCFD, SASB, ISO, SEC)

## Outputs

- 3 HTML Reports:
  - Board Summary Dashboard
  - GHG Inventory Report
  - Supplier Scorecard
- Anomalies Detected & Resolved
- Compliance Scorecard
- Optimization Recommendations

## Example Usage

> "Run the Q1 2024 emissions audit"
> "Execute complete audit for Beta Steel and Alpha Logistics"
> "Generate Q2 audit with TCFD compliance focus"

## Timeline

Expected execution: 2-3 seconds for 3 suppliers

---

**After completion, review the generated reports and anomaly flags for next steps.**
