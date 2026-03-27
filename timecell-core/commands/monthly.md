---
description: Full monthly portfolio review — comprehensive analysis, crash survival, goals, outlook
argument-hint: ""
---

# /tc:monthly — Monthly Review

## Budget: 3 tool calls max

## Pre-Check
Session count = `grep -c "^## [0-9]" memory/session-log.md`.
- If session_count <= 3 or < 2 snapshots: redirect to /tc:start ("Let's build a few more snapshots first.")

## Step 1: Read All Data (1 bash call)

```bash
cat profile.md entities/*.md snapshots/*.md memory/*.md decisions/*.md 2>/dev/null; echo "===SEP==="; python3 scripts/fetch-exchange-rates.py 2>/dev/null
```

Returns: profile, entities, all snapshots (for trends), memory, decisions, exchange rates.

## Step 2: Compute Everything Inline (0 tool calls)

**Portfolio overview:** Net worth, allocation, runway, guardrails (same as /start).

**MoM trends:**
- nw_change = latest - month_ago, pct = change/month_ago × 100
- Flag allocation drift > 5%

**Crash survival (3 scenarios):**
- Mild: Equities −15%, Crypto −20%
- Severe: Equities −30%, Crypto −50%, Property −10%
- Extended: Equities −40%, Crypto −60%, Property −15%
- Compute post-crash NW, runway for each

**Goal progress:**
- projected = current + (months_remaining × monthly_contribution)
- On Track if projected >= target, At Risk if >= 80% of target, Off Track otherwise

**Guardrail calibration:** current_zone vs month_ago_zone → Improving/Stable/Deteriorating

**Thresholds:**
- Runway: CRITICAL < 12mo, WARNING 12-18mo, SAFE 24-36mo, STRONG > 36mo
- Entity: CRITICAL > 50%, WARNING > 30%
- Asset class: CRITICAL > 70%, WARNING > 50%

## Step 3: Write Snapshot + Log (1-2 tool calls)

Write `snapshots/YYYY-MM-DD.md` (same format as /start).

Append to `memory/session-log.md`:
```
## YYYY-MM-DD — Monthly Review
- Net worth: $X,XXX,XXX (MoM: +X.X%)
- Guardrails: [summary]
- Goals: [summary]
```

## Step 4: Present (0 tool calls)

Apply lifecycle greeting. Lead with numbers.

1. Net worth + MoM change
2. Allocation table with drift
3. Crash survival table
4. Guardrail audit with trend
5. Goal progress table
6. Forward outlook (narrative)
7. React dashboard artifact

**Plugin-Aware:** If `btc-check` command exists: read `references/bitcoin-formulas.md` and add BTC temperature, selling status, and BTC-specific crash scenarios to the monthly review. Otherwise: standard crypto analysis only.

**Output:** 500-800 words + dashboard. Tables for data, narrative for outlook. Reference specific dates/amounts.
