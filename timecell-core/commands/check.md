---
description: Risk assessment and stress test — portfolio resilience, guardrail audit, risk verdict
argument-hint: "[optional: specific scenario, e.g. 'BTC drops 50%']"
---

# /tc:check — Risk Assessment

## Budget: 3 tool calls max

Read data (1) → write snapshot (1) → present (0). All computation inline.

## Step 1: Determine Scope
If user gave specific scenario (e.g., "BTC drops 50%"): model that first, then offer full suite.
Otherwise: run standard suite (Step 2).

## Step 2: Stress Test Suite (compute inline)

**Shock scenarios:**

| Scenario | Equities | Crypto | Property | Cash/FI |
|----------|----------|--------|----------|---------|
| Mild | −15% | −20% | 0% | 0% |
| Severe | −30% | −50% | −10% | 0% |
| Extended bear | −40% | −60% | −15% | 0% |

For each: compute post-crash net worth, runway.

**Risk verdict:**
- RESILIENT: all scenarios → runway > 24mo
- ADEQUATE: severe crash → runway > 12mo
- FRAGILE: any scenario breaches critical

## Step 3: Guardrail Audit (inline)

Apply thresholds:
- Runway: CRITICAL < 12mo, WARNING 12-18mo, SAFE 24-36mo, STRONG > 36mo
- Single entity: CRITICAL > 50%, WARNING > 30%
- Asset class: CRITICAL > 70%, WARNING > 50%

## Step 4: Write Snapshot + Present

Write `snapshots/YYYY-MM-DD.md`. Then present:
1. Risk verdict
2. Stress test table
3. Guardrail audit
4. Recommendations
5. React dashboard artifact

**Response Style:** Read `response_style` from profile.md -> CIO Preferences. Default: `dashboard`. If `conversational`: lead with verdict in prose, inline numbers. If `auto`: conversational unless user requests data.

**Rules:** Runway impact is key. Frame via framework. Specific scenario first if requested.

**Plugin-Aware:** If `btc-check` command exists: read `references/bitcoin-formulas.md` and extend stress test suite with the 5 bitcoin-specific crash scenarios (btc_crash_25/50/75, market_crash_20/40). Include BTC temperature context in risk verdict. Otherwise: use standard crypto shock multipliers only.
