---
description: Risk assessment and stress test — portfolio resilience, guardrail audit, risk verdict
argument-hint: "[optional: specific scenario, e.g. 'BTC drops 50%']"
---

# /tc:check — Risk Assessment

Read `references/timecell.md` and follow the CIO persona.

## Workflow

### Step 1: Determine Scope
If user provided a specific scenario (e.g., "BTC drops 50%"):
- Model that specific scenario first
- Then offer: "Want to see the full stress test suite?"

If no specific scenario: run standard suite (Step 2).

### Step 2: Stress Test Suite

| Scenario | Description | Assumptions |
|----------|-------------|-------------|
| Market correction | Normal pullback | Equities -20%, crypto -30% |
| Crypto winter | Crypto-focused drawdown | Crypto -60%, equities -10% |
| Broad crash | Multi-asset recession | Equities -40%, crypto -50%, property -15% |
| Income loss | Employment disruption | Zero income for 12 months |
| Black swan | Tail risk event | Worst asset -80%, all others -20% |

For each scenario, compute:
- Post-shock net worth
- Post-shock allocation
- Post-shock runway (months)
- Guardrail zone changes

### Step 3: Guardrail Audit
Load `guardrails` skill — full status check.

### Step 4: Risk Verdict
Synthesize into a clear verdict:
- **RESILIENT** — survives all scenarios with runway > 24 months
- **ADEQUATE** — survives most but vulnerable to severe scenarios
- **FRAGILE** — one or more scenarios breach critical thresholds

### Step 5: Present
Lead with the verdict:
```
Risk Verdict: RESILIENT / ADEQUATE / FRAGILE
```

Then: stress test table, guardrail audit, specific recommendations.

### Step 6: Generate Dashboard
React artifact with stress test results and guardrail status visualization.

## Rules
- Always show runway impact — this is what matters most
- Frame recommendations through the framework
- If specific scenario requested, model that FIRST before offering full suite
