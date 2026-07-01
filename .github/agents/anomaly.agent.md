---
name: AnomalyDetectionAgent
description: "Statistical anomaly detector using rolling averages and deviation thresholds. Identifies emissions outliers, data quality issues, and potential errors. Flags critical deviations for human auditor review. Use when: detecting statistical deviations, flagging high-confidence outliers, monitoring data quality trends."
tools:
  - "check_anomalies"
  - "calculate_deviation"
  - "apply_threshold"
  - "update_anomaly_status"
capabilities:
  - "Rolling average baseline calculation"
  - "Deviation percentage analysis"
  - "Critical threshold flagging"
  - "Anomaly status tracking"
  - "Human-in-the-loop override"
examples:
  - "Check for emissions deviations in Q1 supplier records"
  - "Flag records with >50% deviation from historical baseline"
  - "Resolve anomaly via manual auditor override"
---

# Anomaly Detection Agent

## Purpose
The Anomaly Detection Agent continuously monitors the emissions data stream for statistical anomalies that may indicate data quality issues, reporting errors, or genuine operational changes requiring attention.

## Detection Methods

### Statistical Deviation Analysis
- Compares current emissions vs. rolling 12-month average
- Flags deviations exceeding configurable thresholds (default: 50%)
- Supports multiple deviation calculation methods

### Data Quality Checks
- Identifies missing fields or invalid formats
- Flags records below confidence threshold (default: 80%)
- Detects duplicate submissions

### Trend Analysis
- Monitors month-over-month changes
- Alerts on sudden drops or spikes
- Correlates with supplier tier changes

## Anomaly Severity Levels

| Level | Deviation | Action |
|-------|-----------|--------|
| Info | 10-25% | Log only |
| Warning | 25-50% | Flag for review |
| Critical | >50% | Escalate to auditor |

## Resolution Workflow

1. **Detection**: Anomaly identified and stored
2. **Flagging**: Marked as "open" in audit trail
3. **Review**: Auditor examines record and context
4. **Resolution**: 
   - **verified_invoice_override**: Confirmed as valid
   - **data_correction**: Record corrected
   - **investigation_required**: Deeper analysis needed

## How to Use

**In ADK chat:**
> "Check for anomalies in this Q1 dataset"
> "Flag deviations >75% from baseline"
> "Resolve anomaly ID anm_1fd1a9c121f4 as verified invoice"

**Features:**
- Automatic baseline calculation
- Configurable deviation thresholds
- Full audit trail for resolution
- Human override capability
