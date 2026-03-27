---
name: guardrails
description: |
  Check portfolio guardrails and assign zone status. This is the SINGLE SOURCE OF TRUTH
  for all threshold values — other skills reference this, never duplicate thresholds.
  Used by /tc:start and /tc:check. Triggers on "guardrails", "am I safe", "check limits",
  "risk status", "zone check".
---

# Guardrail Checking

## Core Guardrails

### 1. Runway
- **Metric:** Liquid assets / monthly expenses
- **Thresholds:**
  - CRITICAL: < 12 months
  - WARNING: 12-18 months
  - WATCH: 18-24 months
  - SAFE: 24-36 months
  - STRONG: > 36 months
- **Liquid assets include:** cash, savings, listed equities, stablecoins, money market funds
- **Illiquid (excluded):** property, private equity, locked positions, art, business equity
- **Monthly expenses:** from profile.md. If missing, prompt user.

### 2. Concentration — Asset Class
- **Metric:** Single asset class as % of total net worth
- **Thresholds:**
  - CRITICAL: > 70%
  - WARNING: > 50%
  - WATCH: > 40%
  - SAFE: <= 40%

### 3. Concentration — Single Entity
- **Metric:** Single entity as % of total net worth
- **Thresholds:**
  - CRITICAL: > 50%
  - WARNING: > 30%
  - WATCH: > 20%
  - SAFE: <= 20%

### 4. Goal Alignment
- **Metric:** Current trajectory vs stated goals
- **Assessment:** On track / At risk / Off track
- **Method:** For each goal, project: current + (months_remaining x monthly_contribution) vs target

## Workflow

### Step 1: Compute All Metrics
Calculate runway, concentration (class and entity), and goal alignment using current data.

### Step 2: Assign Zones
Apply thresholds above. Each guardrail gets exactly one zone.

### Step 3: Present

| Guardrail | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| Runway | >= 24 months | 38 months | SAFE |
| BTC Concentration | <= 50% | 52% | WARNING |
| Max Entity | <= 30% | 28% | SAFE |
| Goal: FI by 2030 | On track | 60% done | On Track |

### Step 4: Action Items
For CRITICAL or WARNING guardrails:
- State the specific breach with numbers
- Quantify what would fix it: "Reducing BTC by $XX would bring concentration to 45%"
- Frame as framework recommendation: "The framework suggests..."

## Rules
- NEVER suppress a CRITICAL guardrail — always surface it, every session
- Thresholds live HERE — all other skills reference this skill for threshold values
- Display is mandatory; suppression gates only control proactive display, never direct answers (Design Rule #3)
- When multiple guardrails are breached, present in severity order: CRITICAL first
