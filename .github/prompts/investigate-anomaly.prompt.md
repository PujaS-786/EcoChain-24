---
name: investigate-anomaly
description: "Deep-dive investigation of anomalies and unusual emissions patterns. Validates statistical outliers, identifies root causes, and recommends resolution actions. Use when: anomalies are detected, investigating data quality issues, resolving high-deviation records."
tools:
  - AnomalyDetectionAgent
  - AuditAgent
  - CalculationAgent
---

# Investigate Anomaly

## Purpose
Analyze suspicious emissions data and determine if it's valid, a data error, or a genuine operational change.

## What Happens

1. **Flagged Records** – Retrieve anomalies exceeding thresholds
2. **Statistical Analysis** – Calculate exact deviation percentages
3. **Data Validation** – Check source records and audit trail
4. **Context Check** – Compare to operational events (process changes, etc.)
5. **Resolution** – Categorize as verified, error, or investigation-pending
6. **Documentation** – Log resolution in audit trail

## Inputs Required

- **Anomaly ID**: (e.g., "anm_1fd1a9c121f4")
- **Investigation Focus**: Root cause or data quality check
- **Resolution Code**: (Optional) If already resolved

## Outputs

- Deviation analysis (% from baseline)
- Statistical significance assessment
- Audit trail for the record
- Root cause (if determined)
- Recommended resolution
- Verification status

## Example Usage

> "Investigate anomaly anm_1fd1a9c121f4"
> "Why is Beta Steel's emissions 97.9% above baseline?"
> "Verify and resolve the April spike in Green Energy data"

## Expected Duration

30-60 seconds per anomaly investigation

---

**Document all findings in audit trail for auditor review and approval.**
