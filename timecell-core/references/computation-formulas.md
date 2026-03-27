# Computation Formulas

Single source of truth for all TimeCell core calculations. Commands and skills reference this file — never duplicate formulas elsewhere.

**Computation Integrity:** All numbers presented to the user MUST come from formulas in this file. Never invent explanations for numbers — trace every value to its formula.

**NOTE:** Commands inline their own thresholds for speed. This file is the canonical reference for skills and freeform CIO queries. If thresholds change, update BOTH this file and the command files.

---

## Net Worth

```
FOR each entity in entities/:
  IF entity.currency = base_currency:
    base_value = local_value
  ELSE:
    base_value = local_value * (base_currency_usd_rate / entity_currency_usd_rate)

FOR each asset_class IN [cash, equities, property, crypto, fixed-income, alternatives]:
  class_total = SUM(base_value for entities in that class)

total_net_worth = SUM(all class_totals)
```

**Self-check:** Sum of entity base_values must equal total_net_worth within 0.1%.

---

## Allocation

```
FOR each asset_class:
  allocation_pct = ROUND(class_total / total_net_worth * 100)
FOR each entity:
  entity_pct = ROUND(entity_base_value / total_net_worth * 100)
Adjust largest position so percentages sum to exactly 100%.
```

---

## Runway

```
liquid_assets = SUM(base_value) for entities with type IN [cash, equities, crypto, fixed-income, money-market]
  EXCLUDE: property, alternatives, business equity, locked positions
monthly_burn = monthly_expenses - monthly_income (from profile.md)

IF monthly_burn <= 0: runway = "Indefinite (positive cash flow of $X,XXX/month)"
ELSE: runway_months = ROUND(liquid_assets / monthly_burn)
  IF runway_months > 24: display as "N years" (round to 0.5 if < 10yr)
  ELSE: display as "N months"
IF liquid_assets = 0 AND monthly_burn > 0: runway = 0
```

---

## Guardrail Zones

### Runway Thresholds

| Zone | Threshold |
|------|-----------|
| CRITICAL | < 12 months |
| WARNING | 12–18 months |
| WATCH | 18–24 months |
| SAFE | 24–36 months |
| STRONG | > 36 months |

### Concentration — Asset Class

| Zone | Threshold |
|------|-----------|
| CRITICAL | > 70% |
| WARNING | > 50% |
| WATCH | > 40% |
| SAFE | <= 40% |

### Concentration — Single Entity

| Zone | Threshold |
|------|-----------|
| CRITICAL | > 50% |
| WARNING | > 30% |
| WATCH | > 20% |
| SAFE | <= 20% |

### Zone Assignment Algorithm

```
Compare actual to thresholds IN ORDER (most severe first):
  CRITICAL → WARNING → WATCH → SAFE → STRONG
```

Every guardrail gets exactly one zone. Assign the first (most severe) threshold that matches and stop.

---

## Goal Progress

```
months_remaining = (target_date - today) in months
projected = current_progress + (months_remaining * monthly_contribution)
(0% growth assumption)
Achieved if current >= target
On Track if projected >= target
At Risk if projected >= 0.8 * target
Off Track otherwise
gap_per_month = (target - projected) / months_remaining
```

---

## Currency Conversion

```
base_value = local_value * (base_usd_rate / local_usd_rate)
For BTC: btc_base_value = btc_quantity * btc_usd_price / base_usd_rate
```

### Rounding Rules

| Value | Rule |
|-------|------|
| Fiat >= $10,000 | Whole dollars (no decimals) |
| Fiat < $10,000 | 2 decimal places |
| BTC quantities | 4 decimal places |
| Exchange rates | 4 decimal places |
| Percentages | Whole numbers |

---

## FX Impact Isolation

```
value_change = current_base_value - previous_base_value
fx_impact = previous_local_value * (current_rate - previous_rate)
real_change = value_change - fx_impact
```

Use this when comparing snapshots across dates to separate genuine value changes from FX movement.

---

## Crash Survival (Core — Simple Drawdown)

### Shock Scenarios

| Scenario | Equities | Crypto | Property | Cash / FI |
|----------|----------|--------|----------|-----------|
| Mild | −15% | −20% | 0% | 0% |
| Severe | −30% | −50% | −10% | 0% |
| Extended bear | −40% | −60% | −15% | 0% |

```
FOR each scenario, FOR each entity:
  shocked_value = base_value * (1 + shock_pct_for_entity_type)
Compute: post_crash_nw, post_crash_liquid, post_crash_runway
Apply guardrail zones to post-crash results.
```

**Resilience Grade** (from crash survival results):
- RESILIENT: all scenarios post-crash runway > 24mo
- ADEQUATE: severe scenario post-crash runway > 12mo
- FRAGILE: any scenario breaches CRITICAL runway

**Note:** timecell-bitcoin add-on provides a more sophisticated model for BTC-heavy portfolios.

---

## Snapshot Delta

```
nw_change = current_nw - previous_nw
nw_change_pct = ROUND(nw_change / previous_nw * 100, 1)
Flag allocation shifts > 5% and guardrail zone changes.
```

---

## Session Count

```
session_count = count of "## YYYY-MM-DD" lines in memory/session-log.md
IF session-log.md doesn't exist: session_count = 1
```

### Lifecycle Stages

| Stage | Sessions |
|-------|----------|
| Onboarding | 1–3 |
| Discovery | 4–10 |
| Partnership | 11–30 |
| Trusted Advisor | 30+ |
