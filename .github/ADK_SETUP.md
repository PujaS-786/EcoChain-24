---
name: "ADK Configuration"
description: "Master configuration for Antigravity ADK integration with EcoChain 24"
version: "1.0"
---

# ADK Integration Configuration

## Overview

This configuration enables full ADK integration for the EcoChain 24 multi-agent carbon auditing system.

---

## File Structure

```
EcoChain24/
├── .github/
│   ├── agents/
│   │   ├── orchestrator.agent.md
│   │   ├── ingestion.agent.md
│   │   ├── calculation.agent.md
│   │   ├── audit.agent.md
│   │   ├── anomaly.agent.md
│   │   ├── compliance.agent.md
│   │   ├── recommendation.agent.md
│   │   └── report.agent.md
│   ├── prompts/
│   │   ├── run-emissions-audit.prompt.md
│   │   ├── analyze-supplier.prompt.md
│   │   ├── carbon-reduction-strategy.prompt.md
│   │   ├── verify-compliance.prompt.md
│   │   └── investigate-anomaly.prompt.md
│   ├── hooks/
│   │   ├── ecochain-auth.json
│   │   ├── ecochain-logging.json
│   │   └── ecochain-error.json
│   └── tools.md
├── copilot-instructions.md          # Project-level guidance
├── AGENTS.md                        # Agent registry
└── ecochain/                        # Python implementation
    ├── agents/                      # Agent source code
    ├── server.py                    # HTTP server
    ├── mcp.py                       # MCP configuration
    └── db.py                        # Database layer
```

---

## Quick Start

### 1. Verify Setup
```bash
# Check agent discovery
ls -la .github/agents/*.agent.md

# Verify prompts
ls -la .github/prompts/*.prompt.md

# Check hooks
ls -la .github/hooks/*.json
```

### 2. Try in ADK Chat
```
"Run the Q1 2024 emissions audit"
"Analyze Beta Steel emissions"
"Generate carbon reduction strategy"
```

### 3. Check Agent Status
```bash
python run_demo.py  # Verify agents are working
```

---

## Agent Discovery

ADK automatically discovers agents from:
- `.github/agents/*.agent.md` – Agent definitions
- `copilot-instructions.md` – Project instructions
- `AGENTS.md` – Agent registry

**No additional registration needed.**

---

## Prompt Discovery

ADK automatically discovers prompts from:
- `.github/prompts/*.prompt.md` – Workflow definitions

**Access via `/` command in chat** (type "/" to see available prompts)

---

## Hook Execution

Hooks are auto-executed at lifecycle events:
- `PreToolUse` – Before agent calls a tool
- `PostToolUse` – After tool execution
- `PreAgent` – Before agent starts (optional)
- `PostAgent` – After agent completes (optional)

Hooks in `.github/hooks/*.json` are auto-loaded.

---

## Tool Registration

MCP tools are registered via:
- Agent manifests (`.agent.md` files)
- Tool definitions in `.github/tools.md`
- Authorization rules in `ecochain/mcp.py`

**Current tools available:**
- ecochain.ingest.*
- ecochain.calculate.*
- ecochain.audit.*
- ecochain.anomaly.*
- ecochain.comply.*
- ecochain.recommend.*
- ecochain.report.*
- ecochain.log.*

---

## Agent Authorization

Each agent has scoped token-based access:

```python
AGENT_TOKENS = {
    "orchestrator": "tok_orchestrator_secret_1234",
    "ingest": "tok_ingest_secret_2234",
    "calculate": "tok_calculate_secret_3234",
    "audit": "tok_audit_secret_4234",
    "anomaly": "tok_anomaly_secret_5234",
    "comply": "tok_comply_secret_6234",
    "recommend": "tok_recommend_secret_8234",
    "report": "tok_report_secret_7234",
}
```

**Authorization rules:**
- Orchestrator: Full access to all tools
- Other agents: Scoped to `ecochain.<agent_name>.*` namespace + logging

---

## Execution Flow

### Scenario: "Run Q1 2024 audit"

```
User Request
    │
    ├─→ ADK Match Agent: OrchestratorAgent
    │
    ├─→ Orchestrator calls:
    │   ├─ IngestionAgent.normalize_record()
    │   ├─ CalculationAgent.calculate_record() [parallel x3]
    │   ├─ AuditAgent.audit_record()
    │   ├─ AnomalyDetectionAgent.check_anomalies()
    │   ├─ ComplianceAgent.check_compliance()
    │   ├─ RecommendationAgent.generate_recommendations()
    │   └─ ReportAgent.generate_report()
    │
    ├─→ Hook Execution:
    │   ├─ PreToolUse: Authorize agent
    │   ├─ PostToolUse: Log to audit trail
    │   └─ Error handler: Catch failures
    │
    └─→ Return Results
        ├─ 3 HTML reports
        ├─ Anomalies detected
        ├─ Compliance score
        └─ Recommendations
```

---

## Common Workflows

### Workflow 1: Complete Audit (via Prompt)
```
User: "Run Q1 2024 audit"
   ↓
ADK loads: run-emissions-audit.prompt.md
   ↓
Calls OrchestratorAgent (8 sequential/parallel agent calls)
   ↓
Output: 3 reports + anomalies + recommendations
```

### Workflow 2: Specific Analysis (via Agent)
```
User: "Analyze Beta Steel"
   ↓
ADK loads: analyze-supplier.prompt.md
   ↓
Calls CalculationAgent + AuditAgent + RecommendationAgent
   ↓
Output: Footprint + data quality + optimization opportunities
```

### Workflow 3: Direct Agent Call
```
User: "Calculate Scope 2 emissions for 500 kWh"
   ↓
ADK loads: CalculationAgent
   ↓
Agent calls: ecochain.calculate.apply_factor()
   ↓
Output: 185 kg CO₂e with methodology
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Agent discovery | <100ms |
| Prompt resolution | <50ms |
| Hook execution | <500ms |
| Full audit pipeline | <3 sec |
| Database query | <100ms |

---

## Troubleshooting

### Agent Not Discoverable?
1. Check `.github/agents/` directory exists
2. Verify `.agent.md` files have correct frontmatter
3. Ensure YAML syntax is valid (quotes around special characters)
4. Check `copilot-instructions.md` is present at root

### Prompt Not Showing?
1. Verify `.github/prompts/*.prompt.md` files exist
2. Check frontmatter has `name` and `description`
3. Ensure tool names match agent names
4. Check AGENTS.md registry

### Hooks Not Executing?
1. Verify `.github/hooks/*.json` files exist
2. Check JSON syntax is valid
3. Verify hook command is executable
4. Check agent logs for hook errors

### Tool Not Available?
1. Verify tool registered in agent manifest
2. Check agent has authorization for tool
3. Verify tool exists in `ecochain/mcp.py`
4. Check audit trail for authorization failures

---

## Monitoring & Debugging

### View Audit Trail
```bash
sqlite3 ecochain.db "SELECT * FROM audit_trail ORDER BY entry_id DESC LIMIT 10;"
```

### Check Agent Logs
```bash
python -c "from ecochain.agents.orchestrator import OrchestratorAgent; a = OrchestratorAgent(); print('Agent initialized')"
```

### Verify Database
```bash
python -c "from ecochain.db import verify_audit_trail_integrity; print(verify_audit_trail_integrity())"
```

---

## Security & Compliance

### Cryptographic Audit Trail
- ✅ SHA-256 hashing
- ✅ Chained hashes (tamper detection)
- ✅ Immutable records
- ✅ Full action logging

### Agent Authorization
- ✅ Token-based scoping
- ✅ Namespace restrictions
- ✅ Tool-level access control
- ✅ Audit logging of all tool calls

### Standards Compliance
- ✅ GRI 305
- ✅ TCFD
- ✅ SASB
- ✅ ISO 14064-1
- ✅ SEC Climate Rule

---

## Integration Checklist

- ✅ Agent manifests created (.github/agents/)
- ✅ Prompts created (.github/prompts/)
- ✅ Hooks configured (.github/hooks/)
- ✅ Tool registry documented (.github/tools.md)
- ✅ Agent discovery enabled (AGENTS.md)
- ✅ Project instructions (copilot-instructions.md)
- ✅ All agents operational and tested
- ✅ Audit trail functional and verified
- ✅ Authorization system active

---

## Next Steps

1. **Test Agents**: Try prompt queries in ADK chat
2. **Monitor Execution**: Watch real-time agent coordination
3. **Review Reports**: Check generated HTML reports
4. **Validate Compliance**: Run compliance checks
5. **Plan Strategy**: Use recommendations for carbon goals

---

**EcoChain 24 is fully integrated with Antigravity ADK and ready for production use!**
