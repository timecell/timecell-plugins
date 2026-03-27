---
description: Daily portfolio health check — net worth, allocation, guardrails, and what needs attention
argument-hint: ""
---

# /tc:start — Portfolio Health Check

Read `references/timecell.md` and follow the CIO persona.

## Pre-Checks
1. Run `python3 scripts/check-snapshot-staleness.py` — note result
2. If no profile.md: redirect to /tc:setup
3. If no files in entities/: "No holdings found. Run /tc:setup to add your accounts."

## Workflow

### Step 1: Read All Data
- Read `profile.md` and every file in `entities/`
- Read latest snapshot in `snapshots/` (if any)

### Step 2: Compute
- Load the `net-worth` skill — compute total, breakdown by asset class
- Load the `allocation` skill — check concentration
- Load the `guardrails` skill — check all guardrails and assign zones
- Load the `runway` skill — compute months of safety

### Step 3: Compare to Last Snapshot
If previous snapshot exists:
- Net worth delta (absolute and %)
- Allocation shifts
- Guardrail zone changes

### Step 4: Save Snapshot
Write to `snapshots/YYYY-MM-DD.md`:
```
---
date: YYYY-MM-DD
base_currency: [from profile]
exchange_rates: { ... }
---

| Entity | Asset Class | Currency | Value (Local) | Value (Base) | % of Total |
|--------|------------|----------|---------------|-------------|------------|
| ... | ... | ... | ... | ... | ... |

| Guardrail | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| ... | ... | ... | ... |
```

### Step 5: Present as Dashboard
Generate a React artifact dashboard with:
- Net worth headline number
- Asset allocation (horizontal bar chart)
- Guardrail status cards
- Week-over-week change (if previous snapshot exists)

Lead with the numbers. Table first, narrative second.

### Step 6: Plugin-Aware Sections
If bitcoin-specific skills are available: include BTC temperature and custody sections.
If NOT available: show BTC as regular asset class with standard allocation analysis.

## Output Priority
1. Portfolio table (net worth by asset class)
2. Guardrail status table
3. Change since last snapshot
4. 0-3 priority items (CRITICAL/WARNING only)
5. React dashboard artifact
