---
name: CalculationAgent
description: "GHG Protocol emissions calculator using verified emission factors and calculation methodologies. Computes Scope 1, 2, and 3 emissions with location-based and market-based alternatives. Use when: calculating carbon emissions from activity data, computing scope-specific totals, generating emissions records with confidence scores."
tools:
  - "calculate_record"
  - "calculate_scope1"
  - "calculate_scope2"
  - "calculate_scope3"
  - "apply_emission_factor"
capabilities:
  - "GHG Protocol Scope 1/2/3 calculation"
  - "Location-based and market-based reporting"
  - "Emission factor version control"
  - "Confidence scoring"
  - "Parallel calculation with ThreadPoolExecutor"
examples:
  - "Calculate Scope 3 emissions from 3 supplier invoices"
  - "Generate market-based Scope 2 for US electricity usage"
  - "Compute total Q1 carbon footprint across all scopes"
---

# Calculation Agent

## Purpose
The Calculation Agent applies verified emission factors and GHG Protocol methodologies to convert activity data into quantified emissions. It supports all three scopes and provides dual reporting for Scope 2.

## Supported Methodologies

### Scope 1 (Direct)
- Natural gas combustion (2.02 kg CO₂e/m³)
- Diesel fuel (2.68 kg CO₂e/L)
- Petrol fuel (2.31 kg CO₂e/L)
- LPG combustion (1.51 kg CO₂e/L)

### Scope 2 (Indirect - Grid)
- Location-based: By country grid mix (0.35-0.58 kg CO₂e/kWh)
- Market-based: By contract/renewable source
- Supported regions: US, DE, JP, CN, Global Average

### Scope 3 (Supply Chain)
- Logistics (air: 1.20, road: 0.08, rail: 0.02, sea: 0.01 kg CO₂e/t-km)
- Procurement (steel: 1.50, chemicals: 2.10, electronics: 0.40 kg CO₂e/USD)
- Agriculture (beef: 80.0, dairy: 120.0 kg CO₂e/head/yr)

## Emission Factors

All factors are version-controlled:
- **GHG Protocol**: v2024-V1 (fuels)
- **IEA**: v2024-V2 (electricity)
- **GLEC**: v2024-V1.2 (logistics)
- **IPCC**: Tier1-2024 (agriculture)
- **EEIO**: US-2024 (economic input-output)

## How to Use

**In ADK chat:**
> "Calculate Scope 2 emissions for 100 kWh of US grid electricity"
> "Compute total Q1 carbon footprint using location-based Scope 2"
> "Calculate Scope 3 from 50 tons shipped by road"

**Features:**
- Parallel processing of multiple records
- Confidence scoring based on data quality
- Methodology transparency and auditability
- Dual reporting for Scope 2
