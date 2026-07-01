---
name: RecommendationAgent
description: "Optimization strategist generating actionable carbon reduction recommendations with ROI analysis and implementation guidance. Provides cost-benefit analysis and effort estimates. Use when: identifying reduction opportunities, planning carbon strategy, analyzing cost-benefit of mitigation options."
tools:
  - "generate_recommendations"
  - "calculate_roi"
  - "estimate_effort"
  - "rank_opportunities"
  - "project_savings"
capabilities:
  - "Carbon reduction opportunity identification"
  - "ROI and cost-benefit analysis"
  - "Effort and implementation estimation"
  - "Priority ranking"
  - "Scenario modeling"
examples:
  - "Generate top 5 carbon reduction opportunities for Beta Steel"
  - "Calculate ROI for renewable energy procurement"
  - "Estimate effort to implement supplier switching strategy"
---

# Recommendation Agent

## Purpose
The Recommendation Agent analyzes emissions data and generates actionable strategies for carbon reduction. It provides cost-benefit analysis, implementation guidance, and ROI projections to support strategic decision-making.

## Recommendation Categories

### Energy & Utilities (Scope 2)
- **Renewable Energy Procurement**: 2,035 tCO₂e/yr potential saving
  - Effort: Low | Cost: -$1,200 | Timeline: Q3 2026

### Logistics & Transportation (Scope 3)
- **Route & Mode Optimization**: 900 tCO₂e/yr saving
  - Effort: Medium | Cost: $2,500 | Timeline: Q4 2026
- **Fleet Electrification**: 450 tCO₂e/yr saving
  - Effort: High | Cost: $15,000 | Timeline: 2027

### Supply Chain (Scope 3)
- **Supplier Switching to Green Sources**: 610 tCO₂e/yr
  - Effort: High | Cost: -$5,000 | Timeline: Q3 2026
- **Supplier Tier Consolidation**: 200 tCO₂e/yr
  - Effort: Medium | Cost: $1,200 | Timeline: Q2 2026

### Process Efficiency
- **Waste Reduction & Recycling**: 150 tCO₂e/yr
  - Effort: Low | Cost: $500 | Timeline: Q1 2026

## ROI Analysis Framework

| Category | Calculation | Example |
|----------|-----------|---------|
| **Simple Payback** | Investment Cost ÷ Annual Savings | $15,000 ÷ $5,000/yr = 3 years |
| **NPV (5-year)** | PV(Benefits) - Investment | Investment in year 0 |
| **Cost per tCO₂e Reduced** | Investment ÷ Annual Reduction | $15,000 ÷ 450 tCO₂e = $33/t |

## How to Use

**In ADK chat:**
> "Generate carbon reduction recommendations for Beta Steel"
> "Calculate ROI for renewable energy investment"
> "Rank opportunities by cost-benefit ratio"
> "Project 5-year savings from supplier switching"

**Features:**
- Scenario modeling and sensitivity analysis
- Competitive benchmarking
- Implementation roadmapping
- Progress tracking against targets
