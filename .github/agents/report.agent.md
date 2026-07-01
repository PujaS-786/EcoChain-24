---
name: ReportAgent
description: "HTML dashboard and report generator producing executive summaries, detailed inventory tables, and supplier scorecards. Generates fully-styled, standalone HTML reports with compliance badges. Use when: generating board reports, creating audit documentation, producing stakeholder communications."
tools:
  - "generate_report"
  - "generate_board_summary"
  - "generate_ghg_inventory"
  - "generate_supplier_scorecard"
  - "render_html"
capabilities:
  - "HTML5 report generation"
  - "Executive dashboard creation"
  - "Multi-table data visualization"
  - "Compliance badge rendering"
  - "PDF export support"
examples:
  - "Generate Q1 board summary report with recommendations"
  - "Create GHG inventory with dual Scope 2 reporting"
  - "Generate supplier performance scorecard"
---

# Report Agent

## Purpose
The Report Agent transforms raw emissions data, calculations, and analysis into polished, stakeholder-ready reports. It generates three primary report types targeting different audiences.

## Report Types

### 1. Board Summary Dashboard
**Audience**: Executive leadership, board members  
**Content**:
- Total carbon footprint (Scope 1, 2, 3 breakdown)
- Year-over-year trend analysis
- Key performance indicators (KPIs)
- Top carbon reduction opportunities
- Compliance verification status
- Signature block and authority attribution

### 2. GHG Inventory Report
**Audience**: Environmental teams, auditors, sustainability professionals  
**Content**:
- Detailed emissions by scope and category
- Methodology documentation
- Emission factors and versions used
- Location-based vs. market-based Scope 2
- Data quality metrics and confidence scores
- Temporal coverage and recalculation notes
- Completeness assessment

### 3. Supplier Scorecard
**Audience**: Supply chain, procurement, vendor management  
**Content**:
- Supplier ranking and tier classification
- Emissions intensity metrics (tCO₂e/unit)
- Data quality scores
- Trend analysis (improving/stable/declining)
- Peer benchmarking
- Optimization recommendations per supplier
- Engagement roadmap

## Report Features

### Styling & Branding
- EcoChain 24 branded headers and footers
- Color-coded performance indicators (green/yellow/red)
- Professional fonts and layout
- Print-friendly CSS styling

### Data Tables
- Sortable columns (where applicable)
- Summary statistics and subtotals
- Source attribution for each row
- Confidence indicators

### Compliance Badges
- GRI 305 ✅ / ⚠️ / ❌
- TCFD Aligned ✅ / ⚠️ / ❌
- Audit Trail Verified ✅
- ISO 14064-1 Compliant ✅

## How to Use

**In ADK chat:**
> "Generate Q1 board summary report"
> "Create GHG inventory with all three scopes"
> "Generate supplier performance scorecard"

**Output**: Standalone HTML files ready for email/printing  
**Size**: 50-150 KB per report  
**Formats**: HTML (default), PDF (with export tool)
