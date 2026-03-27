---
description: Full monthly portfolio review — comprehensive analysis, crash survival, goals, outlook
argument-hint: ""
---

# /tc:monthly — Monthly Review

## Tool Call Budget: 4-5 calls maximum

Do NOT load skills. All formulas in `references/computation-formulas.md` (already in context).

## Pre-Check
- Session count from session-log.md entry count (per Session Count formula)
- If session_count <= 3: redirect to /tc:start → "Let's build a few more snapshots first."
- Need 2+ snapshots for trends. If fewer: run /tc:start instead.

## Step 1: Read All Data (1 tool call — batch read)

Read in a single batch:
- `profile.md`
- Every file in `entities/`
- ALL files in `snapshots/` (for trend analysis)
- `memory/session-log.md`, `memory/values.md`, `memory/context-notes.md`
- All files in `decisions/` (for pending actions)

## Step 2: Fetch Exchange Rates (0-1 tool call)

```bash
python3 scripts/fetch-exchange-rates.py
```

Skip if single-currency portfolio.

## Step 3: Compute Everything Inline (0 tool calls)

Apply ALL formulas from `references/computation-formulas.md`:

### Portfolio Overview
Net worth, allocation, runway, guardrails — same as /start.

### Month-over-Month Trends
```
FOR each snapshot in date order:
  track total_net_worth, allocation_pcts, guardrail_zones
nw_mom_change = latest_nw - month_ago_nw
nw_mom_pct = ROUND(nw_mom_change / month_ago_nw * 100, 1)
Flag allocation drift > 5% for any class.
```

### Crash Survival
Apply **Crash Survival** formulas from computation-formulas.md (3 scenarios).
For each: post-crash NW, runway, and guardrail status.

### Goal Progress
Apply **Goal Progress** formulas from computation-formulas.md.

### Guardrail Calibration
```
FOR each guardrail:
  current_zone vs month_ago_zone
  trend = "Improving" / "Stable" / "Deteriorating"
```

## Step 4: Write Snapshot + Session Log (1-2 tool calls)

Write snapshot to `snapshots/YYYY-MM-DD.md` (same format as /start).

Append to `memory/session-log.md`:
```
## YYYY-MM-DD — Monthly Review
- Net worth: $X,XXX,XXX (MoM: +X.X%)
- Guardrails: [zone summary]
- Goals: [status summary]
- Key items: [CRITICAL/WARNING items]
```

## Step 5: Present Monthly Memo (0 tool calls)

Apply lifecycle stage greeting. Lead with numbers.

1. Net worth + monthly change (headline)
2. Allocation table with drift
3. Crash survival table (3 scenarios: post-crash NW + runway)
4. Guardrail audit table (with trend column)
5. Goal progress table
6. Forward outlook (narrative: key dates, risks, pending decisions)
7. React dashboard artifact

### Plugin-Aware
If bitcoin-specific skills available: BTC temperature, conviction framework, BTC-specific crash scenarios.

## Output Rules
- 500-800 words + dashboard artifact
- Lead with numbers (Speed to Value)
- Tables for data, narrative for outlook only
- Reference specific dates and amounts from snapshots
