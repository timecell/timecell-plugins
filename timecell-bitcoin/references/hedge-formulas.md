# Hedge Formulas — Computation Reference

> Read this file when computing hedge budgets, layer exits, CAGR impact,
> coverage health, collar decisions, sensitivity matrices, or breakeven analysis.
> All deterministic computation lives in `scripts/hedge-engine.py`.

## Budget Tiers (by temperature)

| Temp Range | Cycle Phase | Target % | Ceiling % | OTM Range | Tenor (days) |
|------------|-------------|----------|-----------|-----------|--------------|
| < 35 | accumulation | 0.75 | 1.25 | 50-60% | 180-365 |
| 35-59 | mid_cycle | 1.25 | 1.75 | 45-50% | 90-180 |
| 60-74 | late_cycle | 1.75 | 2.25 | 30-40% | 60-180 |
| >= 75 | overheated | 2.25 | 2.25 | 20-30% | 30-90 |

## Credit Impulse Modifier

| Condition | Multiplier | Label |
|-----------|------------|-------|
| US < -0.3 AND CN < -0.3 | 1.5x | both_decelerating |
| US < -0.3 OR CN < -0.3 | 1.25x | one_decelerating |
| US > 0.3 AND CN > 0.3 | 1.0x | both_accelerating |
| Otherwise | 1.0x | neutral |

Adjusted target = target_pct * multiplier, capped at ceiling_pct.

## Layer Classification (by delta)

| |delta| Range | Layer |
|---------------|-------|
| >= 0.04 | buffer |
| 0.015 - 0.039 | core |
| < 0.015 | disaster |

Default (delta unknown): core.

## Exit Recommendations (by layer x profit multiple)

| Layer | Threshold | Action | Exit % |
|-------|-----------|--------|--------|
| buffer | >= 3x | full_exit | 100% |
| buffer | >= 2x | partial_exit_50 | 50% |
| core | >= 8x | full_exit | 100% |
| core | >= 5x | partial_exit_50 | 50% |
| core | >= 3x | partial_exit_25 | 25% |
| disaster | >= 20x | partial_exit_majority | 75% |
| disaster | >= 10x | partial_exit_25 | 25% |
| disaster | >= 5x | recycle_premium | 0% |

## CAGR Formula

    Unhedged: ((1 + r)^(n-1) * (1 - crash))^(1/n) - 1
    Hedged:   ((1 + r - c)^(n-1) * (1 - crash + recovery))^(1/n) - 1
    Improvement = hedged_cagr - unhedged_cagr

Where: r = normal_return, c = annual_cost, n = cycle_length, recovery = recovery_of_loss * crash_magnitude.

## Coverage Health Score (0-100)

| Component | Weight | Scoring |
|-----------|--------|---------|
| Coverage % | 40 | >=60%: 40, >=50%: 35, >=40%: 25, >=25%: 15, else: 5 |
| Days to expiry | 35 | >=90d: 35, >=60d: 30, >=30d: 20, >=14d: 10, else: 0 |
| Avg strike vs spot | 25 | 40-65%: 25, 30-75%: 20, else: 10 |

Crash payoff computed at 50% BTC drop. Recovery_of_loss = payoff / portfolio_loss.

## Collar Triggers

| Condition | Trigger |
|-----------|---------|
| annualized_cost > ceiling_pct | budget_breach |
| temp > 80 AND RV/IV < 0.75 | hot_market (overrides budget_breach) |

Call strike guidance: temp > 95: delta 25, OTM 30-50%. temp > 80: delta 15, OTM 50-75%. else: delta 10, OTM 70-100%.

## Hedge Ratio (by temperature zone)

| Temp Range | Ratio | Zone |
|------------|-------|------|
| < 30 | 100% | Extreme Fear |
| 30-49 | 85% | Fear |
| 50-64 | 70% | Neutral |
| 65-79 | 50% | Caution |
| >= 80 | 35% | Extreme Greed |

Action: |diff| < 5% = maintain, diff > 0 = increase, diff < 0 = decrease.

## Breakeven Algorithm

Binary search over cycle_length (2-200 years) to find max years where hedge improvement > 0. Returns break_even_years and annual_probability (1/years * 100).

## Key Invariants

- Floor NEVER below 0.75%
- All functions: stateless, JSON-in JSON-out
- Zero external dependencies (stdlib only)
