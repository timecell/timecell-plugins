---
description: Full monthly portfolio review — comprehensive analysis, crash survival, goals, outlook
argument-hint: ""
---

# /tc:monthly — Monthly Review

Read `references/timecell.md` and follow the CIO persona.

## Pre-Check
- Need 2+ weeks of snapshots. If insufficient: run /tc:start instead.
- If session_count <= 3: redirect to /tc:start.

## Workflow

### Step 1: Portfolio Overview
Load `net-worth` skill:
- Current total net worth and month-over-month change
- Asset allocation with drift analysis
- Per-entity performance

### Step 2: Crash Survival Analysis
Model three scenarios against current portfolio:

| Scenario | Equities | Crypto | Property | Description |
|----------|----------|--------|----------|-------------|
| Mild correction | -15% | -20% | 0% | Normal market pullback |
| Severe crash | -30% | -50% | -10% | 2022-style drawdown |
| Extended bear | -40% | -60% | -15% | Prolonged recession |

For each: compute post-crash net worth, runway, and guardrail status.

### Step 3: Guardrail Audit
Load `guardrails` skill — full audit:
- All guardrails with current zones
- Trend: improving, stable, or deteriorating vs last month
- Zone changes in the past month

### Step 4: Goal Progress
Load `goal-tracking` skill:
- Progress since last monthly review
- On track / at risk assessment per goal
- Recommended adjustments if off track

### Step 5: Forward Outlook
- Key dates coming up (goal deadlines, planned purchases)
- Risks to watch
- Actions from last month: completed or still pending?

### Step 6: Generate Dashboard
React artifact with: portfolio summary, crash survival visualization, goal progress, guardrail status.

### Step 7: Memory Updates
- Append to `memory/session-log.md`
- Update `memory/context-notes.md` with new signals
- Write to `memory/learnings.md` if new patterns observed

## Output Structure
1. Net worth + monthly change (headline)
2. Allocation table with drift
3. Crash survival table (3 scenarios)
4. Guardrail audit table
5. Goal progress table
6. Forward outlook (narrative)
7. React dashboard artifact
