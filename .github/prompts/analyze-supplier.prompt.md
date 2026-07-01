---
name: analyze-supplier
description: "Deep-dive analysis of a single supplier's emissions performance. Validates data quality, calculates footprint, detects anomalies, and identifies optimization opportunities. Use when: evaluating supplier performance, investigating deviations, planning supplier engagement."
tools:
  - IngestionAgent
  - CalculationAgent
  - AuditAgent
  - AnomalyDetectionAgent
  - RecommendationAgent
---

# Analyze Supplier Emissions

## Purpose
Conduct a comprehensive analysis of a specific supplier's carbon performance.

## What Happens

1. **Load Records** – Retrieve all historical records for supplier
2. **Quality Check** – Validate data completeness and accuracy
3. **Calculate Footprint** – Compute total Scope 1, 2, and 3 emissions
4. **Trend Analysis** – Compare to baseline and detect deviations
5. **Optimize** – Identify top 3 reduction opportunities
6. **Assess** – Provide tier rating and engagement recommendations

## Inputs Required

- **Supplier Name**: (e.g., "Beta Steel Ltd", "Alpha Logistics Co")
- **Time Period**: (Optional) Specific period to analyze, or "all time"
- **Focus Areas**: (Optional) Specific scopes (Scope 1, 2, 3) or categories

## Outputs

- Current emissions footprint by scope
- Trend analysis (improving/stable/declining)
- Data quality assessment
- Flagged anomalies (if any)
- Top 3 carbon reduction opportunities with ROI
- Tier rating and recommendations

## Example Usage

> "Analyze Beta Steel's carbon performance"
> "Compare Alpha Logistics emissions across all quarters"
> "Investigate the 45% emissions spike in Green Energy Corp"

## Expected Duration

1-2 seconds per supplier analysis

---

**Use findings to prioritize supplier engagement and identify quick wins for carbon reduction.**
