---
name: verify-compliance
description: "Check emissions disclosures against GRI, TCFD, SASB, ISO 14064, and SEC standards. Identifies compliance gaps and provides remediation guidance. Use when: preparing reports, verifying standards alignment, conducting compliance audits."
tools:
  - ComplianceAgent
  - CalculationAgent
---

# Verify Compliance Status

## Purpose
Validate that emissions disclosures meet all applicable compliance frameworks.

## What Happens

1. **Framework Mapping** – Check against selected standards
2. **Gap Analysis** – Identify missing requirements
3. **Scoring** – Calculate compliance percentage (0-100%)
4. **Root Cause** – Diagnose why gaps exist
5. **Remediation** – Suggest specific actions to close gaps

## Inputs Required

- **Frameworks**: Which standards to check (GRI, TCFD, SASB, ISO 14064, SEC, CSRD/ESRS)
- **Scope**: Full company or specific business unit
- **Report Period**: Q1 2024, 2024 annual, etc.

## Outputs

- Compliance scorecard (0-100% per framework)
- Specific gap identification
- Priority-ranked remediation actions
- Timeline to full compliance
- Resource requirements

## Example Usage

> "Check GRI 305 and TCFD compliance for Q1 report"
> "Verify we meet SEC climate disclosure requirements"
> "Full compliance audit against all major standards"

## Expected Duration

1-2 seconds per compliance check

---

**Gap remediation typically requires 1-2 weeks of effort per framework.**
