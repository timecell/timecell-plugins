# Visual Dashboard Templates

Data content specifications for React dashboard artifacts. For styling rules see `formatting.md`. For when to produce artifacts see `timecell.md` (React Artifact Guidelines).

Available libraries: React, Tailwind CSS, Recharts, shadcn/ui, Lucide icons.

## 1. Portfolio Dashboard

**Triggers:** /tc:start, /tc:monthly

**Data sections:**
- **Hero card:** Net worth (large), delta from previous snapshot (amount + %), date
- **Allocation chart:** Horizontal bar chart — one bar per asset class, labeled with % and absolute value. NOT pie chart (bars are more readable at 4-8 categories)
- **Entity table:** Entity name, value, % of total, asset class. Bold totals row
- **Guardrail summary:** Compact status row — one indicator per guardrail, zone label (CRITICAL/WARNING/WATCH/SAFE/STRONG)

**Data sources:** Net worth from computation-formulas.md, allocation from entity sums, guardrails from skill-guardrails thresholds.

## 2. Crash Survival Waterfall

**Triggers:** /tc:check, /tc:monthly (crash survival section)

**Data sections:**
- **Scenario comparison:** Grouped bar or waterfall chart — current net worth as baseline, then post-crash values for Mild/Severe/Extended scenarios
- **Impact table:** Scenario name, post-crash net worth, net worth delta, post-crash runway (months), risk verdict
- **Resilience badge:** Single verdict — RESILIENT / ADEQUATE / FRAGILE with color (green/amber/red)

**Data sources:** Shock multipliers from check.md and monthly.md. Post-crash = sum of (entity_value x scenario_multiplier). Resilience grade from computation-formulas.md.

## 3. Guardrail Status Board

**Triggers:** /tc:start, /tc:check, /tc:monthly

**Data sections:**
- **Status cards:** One card per guardrail — metric name, threshold, actual value, zone label. Color-coded: red=CRITICAL, amber=WARNING, yellow=WATCH, green=SAFE, blue=STRONG
- **Trend indicator:** Arrow or label showing direction vs previous snapshot (Improving/Stable/Deteriorating) — only when previous snapshot available
- **Action items:** For CRITICAL/WARNING zones — specific breach description and fix suggestion

**Data sources:** Thresholds from skill-guardrails.md (single source of truth). Actuals computed inline. Trends from snapshot comparison.

## 4. Goal Progress

**Triggers:** /tc:monthly (goal progress section)

**Data sections:**
- **Progress bars:** One per goal — current % filled, target amount labeled, projected completion date
- **Status badge:** On Track (green) / At Risk (amber) / Off Track (red) / Achieved (blue)
- **Gap callout:** For at-risk/off-track goals — monthly increase needed to get back on track

**Data sources:** Goals from profile.md ## Goals section. Trajectory from computation-formulas.md goal progress formulas. Status thresholds from skill-goal-tracking.md.
