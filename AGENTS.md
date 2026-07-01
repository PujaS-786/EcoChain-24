---
name: EcoChain24
description: "Multi-agent carbon auditing system with specialized agents for ingestion, calculation, audit, anomaly detection, compliance, recommendations, and reporting."
---

# EcoChain 24 Multi-Agent System

A hierarchical multi-agent system for automated carbon emissions auditing, compliance verification, and optimization strategy development.

---

## Available Agents

### 🎼 Core Orchestration

| Agent | Role | Status |
|-------|------|--------|
| **Orchestrator** | Pipeline conductor coordinating all agents | ✅ [View Details](.github/agents/orchestrator.agent.md) |

### 📥 Data Processing

| Agent | Role | Status |
|-------|------|--------|
| **Ingestion** | Parse and normalize supplier data from multiple formats | ✅ [View Details](.github/agents/ingestion.agent.md) |
| **Audit** | Validate supplier data quality and tier classification | ✅ [View Details](.github/agents/audit.agent.md) |

### ⚙️ Calculation & Analysis

| Agent | Role | Status |
|-------|------|--------|
| **Calculation** | GHG Protocol emissions calculations (Scope 1/2/3) | ✅ [View Details](.github/agents/calculation.agent.md) |
| **Anomaly** | Statistical deviation detection and flagging | ✅ [View Details](.github/agents/anomaly.agent.md) |

### 📋 Verification & Strategy

| Agent | Role | Status |
|-------|------|--------|
| **Compliance** | Standards validation (GRI, TCFD, SASB, ISO 14064) | ✅ [View Details](.github/agents/compliance.agent.md) |
| **Recommendation** | Carbon reduction opportunity identification with ROI | ✅ [View Details](.github/agents/recommendation.agent.md) |

### 📊 Output & Reporting

| Agent | Role | Status |
|-------|------|--------|
| **Report** | HTML dashboard and report generation | ✅ [View Details](.github/agents/report.agent.md) |

### 🔧 Support Systems

| Agent | Role | Status |
|-------|------|--------|
| **Alert** | Threshold monitoring and escalation | ✅ Active |
| **Log** | Cryptographic audit trail maintenance | ✅ Active |

---

## Quick Start Workflows

### Scenario 1: Run Complete Q1 Audit
```
User: "Run the Q1 2024 emissions audit"
→ Orchestrator coordinates:
   1. Ingestion: Parse 3 supplier records
   2. Calculation: Compute emissions (parallel)
   3. Audit: Validate supplier data
   4. Anomaly: Detect deviations
   5. Compliance: Verify standards
   6. Recommend: Generate strategies
   7. Report: Generate 3 dashboards
```

### Scenario 2: Investigate Emissions Spike
```
User: "Why are emissions 50% higher than last month?"
→ Anomaly Agent:
   1. Identifies deviation from historical baseline
   2. Flags as critical (>50% threshold)
→ Audit Agent:
   1. Validates source data quality
   2. Traces to specific supplier/activity
→ Recommendation Agent:
   1. Suggests mitigation strategies
```

### Scenario 3: Plan Carbon Reduction
```
User: "What's our best opportunity for carbon reduction?"
→ Recommendation Agent:
   1. Analyzes all suppliers
   2. Ranks opportunities by ROI
   3. Estimates savings and effort
   4. Provides implementation roadmap
```

---

## System Architecture

### Multi-Agent Coordination
```
                    ┌─────────────────┐
                    │  Orchestrator   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    ┌────────┐        ┌────────────┐        ┌──────────┐
    │Ingestion│       │Calculation │       │Anomaly   │
    └────────┘       │(Parallel)  │       │Detection │
                     └────────────┘       └──────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │ Compliance   │
                    │ Audit        │
                    └──────────────┘
                          │
                ┌─────────┴──────────┐
                ▼                    ▼
        ┌────────────────┐  ┌──────────────┐
        │Recommendation  │  │ Report       │
        └────────────────┘  └──────────────┘
```

### Data Flow
```
Raw Data (Invoices, ERP) 
    → Ingestion (normalize)
    → Calculation (compute)
    → Storage (database)
    → Analysis (anomaly, compliance)
    → Output (reports, recommendations)
```

---

## Execution Guarantees

### Performance
- **Pipeline Execution**: < 3 seconds for 3 records
- **Parallel Calculation**: ThreadPoolExecutor with max_workers=4
- **Database Operations**: Optimized queries with indexing

### Integrity
- **Cryptographic Audit Trail**: SHA-256 chained hashes
- **Tampering Detection**: ENABLED
- **Chain Verification**: ✅ On every execution

### Compliance
- **GRI 305**: ✅ Full compliance
- **TCFD**: ✅ Metrics disclosed
- **ISO 14064-1**: ✅ Boundary verified
- **Confidence**: 87% average across all records

---

## Database Schema

### Core Tables
- `activity_records`: Source data from ingestion
- `emissions_records`: Calculated Scope 1/2/3 emissions
- `supplier_profiles`: Supplier metadata and performance
- `anomalies`: Flagged deviations and resolutions
- `compliance_disclosures`: Standards validation results
- `recommendations`: Optimization strategies with ROI
- `audit_trail`: Cryptographically sealed action log

---

## Common Queries

**In ADK Chat:**

> "Run Q1 2024 audit workflow"
> "Calculate emissions for Beta Steel Scope 3 category"
> "Check compliance against GRI and TCFD"
> "What are our top 3 carbon reduction opportunities?"
> "Verify audit trail integrity"
> "Generate board summary report"
> "List all active anomalies"

---

## System Health

**Status**: 🟢 ALL OPERATIONAL

| Component | Status | Last Check |
|-----------|--------|-----------|
| Orchestrator | ✅ | 2026-07-02 |
| Ingestion | ✅ | 2026-07-02 |
| Calculation | ✅ | 2026-07-02 |
| Audit | ✅ | 2026-07-02 |
| Anomaly | ✅ | 2026-07-02 |
| Compliance | ✅ | 2026-07-02 |
| Recommendation | ✅ | 2026-07-02 |
| Report | ✅ | 2026-07-02 |
| Database | ✅ | 2026-07-02 |

---

## Documentation

- [Real-Time Execution Report](REAL_TIME_AGENT_EXECUTION.md) - Agent activity logs and performance metrics
- [Live Demo Report](REAL_TIME_WORK_DEMO.md) - Complete workflow demonstration with screenshots
- [Project README](README.md) - Architecture and quick start guide
- [Agent Developer Docs](https://github.com/PujaS-786/EcoChain-24/wiki) - Technical reference

---

**EcoChain 24** is production-ready. All agents are operational and fully integrated.
