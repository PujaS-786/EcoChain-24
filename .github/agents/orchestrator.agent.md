---
name: OrchestratorAgent
description: "Multi-agent pipeline conductor for EcoChain carbon auditing workflow. Coordinates ingestion, calculation, audit, anomaly detection, compliance, recommendations, and reporting agents. Use when: orchestrating end-to-end emissions accounting workflows, managing parallel agent execution, coordinating data flows between specialized agents."
tools:
  - "call_tool"
  - "log_action"
  - "concurrent_execution"
capabilities:
  - "Pipeline orchestration"
  - "Parallel agent coordination"
  - "Error handling and recovery"
  - "Full system privileges"
examples:
  - "Run the complete Q1 2024 emissions audit workflow"
  - "Execute parallel calculation on 3 supplier records"
  - "Coordinate multi-agent anomaly detection and resolution"
---

# Orchestrator Agent

## Purpose
The Orchestrator Agent serves as the conductor of the EcoChain 24 multi-agent system. It manages the complete carbon auditing pipeline, from data ingestion through compliance verification and report generation.

## Key Responsibilities

- **Pipeline Management**: Orchestrates the complete workflow from raw data to auditable reports
- **Parallel Execution**: Manages ThreadPoolExecutor for concurrent emissions calculations
- **Agent Coordination**: Calls specialized agents in sequence or parallel as needed
- **Error Handling**: Catches and logs failures with audit trail entries
- **System Health**: Monitors agent performance and database integrity

## Typical Workflow

```
START
├─ Initialize agent registry
├─ Call Ingestion Agent (normalize records)
├─ Fan-out Calculation Agent (parallel on 3+ records)
├─ Call Audit Agent (validate supplier data)
├─ Call Anomaly Agent (detect deviations)
├─ Call Compliance Agent (verify standards)
├─ Call Recommendation Agent (optimize strategies)
├─ Call Report Agent (generate dashboards)
└─ END
```

## How to Use

**Run complete demo:**
```bash
python run_demo.py
```

**In ADK chat:**
> "Run the Q1 2024 emissions audit workflow with latest supplier data"

**Capabilities:**
- Execute end-to-end auditing pipelines
- Process multiple suppliers concurrently
- Recover from agent failures
- Maintain cryptographic audit trails
