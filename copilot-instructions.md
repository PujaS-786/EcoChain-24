---
name: "EcoChain24 Instructions"
description: "Project-level guidance for EcoChain 24 carbon auditing system. Understand the multi-agent architecture, agent coordination, and typical workflows."
---

# EcoChain 24 — Project Instructions

## About This Project

**EcoChain 24** is an autonomous hierarchical multi-agent system for carbon emissions auditing and supply chain sustainability analysis. It automates:
- Data ingestion from suppliers, utilities, and ERP systems
- GHG Protocol emissions calculations (Scope 1, 2, and 3)
- Anomaly detection and compliance verification
- Carbon reduction recommendation generation
- Executive reporting and stakeholder communication

---

## Agent System Overview

### 10 Specialized Agents Working Together

1. **Orchestrator** – Coordinates the complete pipeline
2. **Ingestion** – Parses and normalizes supplier data
3. **Calculation** – Computes GHG Protocol emissions
4. **Audit** – Validates supplier data quality
5. **Anomaly** – Detects statistical deviations
6. **Compliance** – Verifies standards alignment (GRI, TCFD, SASB, etc.)
7. **Recommendation** – Identifies carbon reduction opportunities with ROI
8. **Report** – Generates HTML dashboards and audit reports
9. **Alert** – Monitors thresholds and escalates issues
10. **Log** – Maintains cryptographic audit trails

---

## How to Work with EcoChain Agents

### For Emissions Auditing

> "Run the Q1 2024 emissions audit workflow"

This triggers the Orchestrator to:
1. Load supplier records via Ingestion Agent
2. Calculate emissions in parallel via Calculation Agent
3. Validate data via Audit Agent
4. Detect anomalies via Anomaly Agent
5. Verify compliance via Compliance Agent
6. Generate recommendations via Recommendation Agent
7. Produce reports via Report Agent

### For Specific Calculations

> "Calculate Scope 2 emissions for 500 kWh of US grid electricity"

The Calculation Agent will:
- Apply the 2024 IEA emission factor for US (0.37 kg CO₂e/kWh)
- Compute: 500 kWh × 0.37 = 185 kg CO₂e
- Return with methodology and confidence score

### For Anomaly Investigation

> "Why did Beta Steel emissions increase 45% this month?"

The Anomaly Detection Agent will:
- Compare to historical rolling average
- Flag as potential issue (45% > 50% threshold)
- Trace to specific records or activity changes
- Recommend auditor review

### For Carbon Reduction Strategy

> "What's the best ROI opportunity for carbon reduction?"

The Recommendation Agent will:
- Analyze all suppliers and processes
- Calculate cost-benefit of each opportunity
- Rank by ROI ($/tCO₂e reduced)
- Provide implementation timeline

### For Compliance Verification

> "Is this report compliant with GRI 305 and TCFD?"

The Compliance Agent will:
- Validate against framework requirements
- Score completeness (0-100%)
- Identify specific gaps
- Suggest remediation actions

### For Report Generation

> "Generate a board summary report for Q1 2024"

The Report Agent will:
- Create polished HTML dashboard
- Include KPIs, trends, and recommendations
- Add compliance verification badges
- Generate with EcoChain 24 branding

---

## Key Concepts

### The Three Scopes

| Scope | What | Examples |
|-------|------|----------|
| **Scope 1** | Direct combustion & process emissions | Natural gas heating, company vehicles, manufacturing |
| **Scope 2** | Indirect grid electricity emissions | Purchased electricity (location or market-based) |
| **Scope 3** | Supply chain & other indirect | Supplier activities, logistics, waste, business travel |

### Emission Factors

All calculations use verified, version-controlled emission factors:
- **Natural gas**: 2.02 kg CO₂e/m³ (GHG-2024-V1)
- **Electricity**: 0.35-0.58 kg CO₂e/kWh by country (IEA-2024-V2)
- **Logistics**: 0.01-1.20 kg CO₂e/t-km by mode (GLEC-2024-V1.2)
- **Steel procurement**: 1.50 kg CO₂e/USD (EEIO-US-2024)

### Compliance Frameworks

The system validates against multiple standards:
- **GRI 305** – Greenhouse Gas Emissions
- **TCFD** – Task Force on Climate-related Financial Disclosures
- **SASB** – Sustainability Accounting Standards Board
- **ISO 14064-1** – Greenhouse Gas Quantification
- **SEC Climate Rule** – Material climate risk disclosure
- **CSRD/ESRS** – EU Corporate Sustainability Reporting

### Audit Trail Security

All agent actions are recorded in a cryptographic chain:
- SHA-256 hashing for immutability
- Chained previous_hash → content_hash
- Tamper detection enabled
- Full action logging (who, what, when, why)

---

## Common Workflows

### Workflow 1: Complete Quarterly Audit
```
1. User: "Run Q1 2024 audit"
2. Orchestrator initializes pipeline
3. Ingestion: Load 3 supplier records + utility data
4. Calculation: Compute emissions (parallel)
5. Audit: Validate supplier data quality
6. Anomaly: Check for statistical deviations
7. Compliance: Verify GRI/TCFD/SASB alignment
8. Recommend: Generate top 5 opportunities
9. Report: Generate 3 dashboards
10. Result: 3 HTML reports + anomaly flags
```

### Workflow 2: Supplier Emissions Analysis
```
1. User: "Analyze Beta Steel emissions vs. baseline"
2. Anomaly Agent: Calculate deviation %
3. Audit Agent: Validate data quality
4. Calculation Agent: Review scope breakdown
5. Recommendation Agent: Suggest improvements
6. Result: Detailed analysis + optimization plan
```

### Workflow 3: Carbon Reduction Planning
```
1. User: "Plan our carbon reduction strategy"
2. Recommendation Agent: Identify opportunities
3. Compliance Agent: Ensure alignment with targets
4. Calculation Agent: Model scenario outcomes
5. Report Agent: Generate presentation deck
6. Result: Roadmap with cost-benefit analysis
```

---

## Database Structure

### Key Tables

**activity_records**: Raw data from suppliers/utilities
- record_id, supplier_id, period, activity_type, quantity, unit, confidence_score

**emissions_records**: Calculated emissions
- emissions_id, record_id, scope, co2e, co2e_market, methodology, confidence_score

**supplier_profiles**: Vendor data
- supplier_id, name, tier (A/B/C/D), data_quality_score, trend, last_update

**anomalies**: Flagged deviations
- anomaly_id, emissions_id, type (statistical_deviation, data_quality_error), deviation_%, status (open/resolved/investigating), resolution_code, auditor_name

**compliance_disclosures**: Standards validation
- disclosure_id, framework (GRI/TCFD/SASB), requirement_id, status (compliant/gap/N/A), remediation_notes

**recommendations**: Carbon reduction strategies
- recommendation_id, category, description, estimated_saving_tco2e, cost_usd, effort (low/medium/high), roi, timeline

**audit_trail**: Cryptographic action log
- entry_id, timestamp, agent_name, action, details, previous_hash, content_hash

---

## Performance Characteristics

| Metric | Target | Typical |
|--------|--------|---------|
| **Full pipeline execution** | <3 sec | 2.3 sec |
| **Parallel calculation** | 4 concurrent | 3-4 records |
| **Records per second** | >1.0 rec/s | 1.3 rec/s |
| **Average confidence** | >85% | 87% |
| **Compliance score** | >90% | 100% |
| **Audit trail chain** | Verified | 45+ entries |

---

## Pro Tips

### Maximize Agent Effectiveness

1. **Use descriptive requests**: "Calculate Scope 3 logistics for 50 tons shipped by road" is better than "Calculate emissions"
2. **Specify scope**: "GRI 305 compliance check" vs. generic "Compliance check"
3. **Provide context**: Include supplier name, time period, activity type
4. **Request specific outputs**: "Generate board summary with top 3 recommendations"

### Interpret Results

1. **Confidence scores** indicate data quality (0-100%). Scores <80% warrant review.
2. **Anomaly flags** are statistical - always validate with source data.
3. **Recommendations** include effort estimates - plan implementation accordingly.
4. **Compliance scores** show framework alignment - 90%+ is target.

### Handle Ambiguities

- If a request is vague, agents will make reasonable assumptions and log them in the audit trail
- Check audit_trail table for detailed reasoning
- Always review high-consequence decisions with source data

---

## Troubleshooting

### Agent Not Responding?
1. Check if agent name is correct (see AGENTS.md for list)
2. Verify ADK registration in .github/agents/
3. Review copilot-instructions.md and agent .agent.md files

### Calculation Seems Off?
1. Verify emission factor version matches your framework requirement
2. Check units (kg, tons, kWh, etc.)
3. Review methodology in Calculation Agent docs

### Compliance Gap?
1. Review FRAMEWORK_REQUIREMENTS in ecochain/mcp.py
2. Check compliance_disclosures table for specific gaps
3. Contact Compliance Agent for remediation guidance

### Missing Data?
1. Verify supplier submission deadlines in check_overdue_submissions()
2. Check activity_records table for ingestion errors
3. Review Ingestion Agent logs in audit_trail

---

## Resources

- **AGENTS.md** – Master registry of all agents
- **README.md** – Project overview and architecture
- **REAL_TIME_AGENT_EXECUTION.md** – Live execution logs and audit trail
- **REAL_TIME_WORK_DEMO.md** – Complete workflow demonstration
- **ecochain/agents/*** – Agent source code
- **ecochain/mcp.py** – MCP configuration and emission factors

---

## Next Steps

1. **Explore AGENTS.md** for detailed agent capabilities
2. **Review REAL_TIME_AGENT_EXECUTION.md** to see agents in action
3. **Try a sample query** in ADK chat (e.g., "Run demo audit")
4. **Check audit logs** to understand agent reasoning
5. **Customize workflows** for your sustainability goals

---

**EcoChain 24 is ready to automate your carbon auditing workflow!**

Ask any agent by name or describe what you need, and the system will coordinate the appropriate specialists to deliver auditable, compliant emissions reporting.
