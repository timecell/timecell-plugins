---
description: Daily portfolio health check — net worth, allocation, guardrails, and what needs attention
argument-hint: ""
---

# /tc:start — Portfolio Health Check

## Tool Call Budget: 3-4 calls maximum

Do NOT load skills as separate tool calls. All formulas are in `references/computation-formulas.md` (already in context).

## Step 1: Read All Data (1 tool call — batch read)

Read in a single batch:
- `profile.md` — identity, goals, expenses, base currency
- Every file in `entities/` — all accounts and assets
- Latest file in `snapshots/` (most recent by filename date)
- `memory/session-log.md` — count ## entries for session count

**Session count:** Count `## YYYY-MM-DD` lines in session-log.md per the Session Count formula in computation-formulas.md.

**If no profile.md:** Stop → "Welcome to TimeCell! Run /tc:setup to get started."
**If no entities/:** Stop → "No holdings found. Run /tc:setup to add your accounts."

## Step 2: Fetch Exchange Rates (0-1 tool call)

If entities use more than one currency:
```bash
python3 scripts/fetch-exchange-rates.py
```

If single-currency portfolio: skip (0 tool calls).

## Step 3: Compute Everything Inline (0 tool calls)

Apply ALL formulas from `references/computation-formulas.md`:

1. **Net Worth** — sum entities, convert currencies
2. **Allocation** — percentage per asset class and entity
3. **Runway** — liquid assets / monthly burn
4. **Guardrail Zones** — apply thresholds to runway, concentration
5. **Snapshot Delta** — compare to previous snapshot (if exists)

**Snapshot staleness:** If latest snapshot date is > 7 days ago, note "Last snapshot is X days old."

## Step 4: Save Snapshot (1 tool call)

PreToolUse hook runs snapshot-before-write.py automatically. Write to `snapshots/YYYY-MM-DD.md`:

```
---
date: YYYY-MM-DD
base_currency: [from profile]
exchange_rates: { [rates used, if multi-currency] }
total_net_worth: [computed]
runway_months: [computed]
---

| Entity | Asset Class | Currency | Value (Local) | Value (Base) | % of Total |
|--------|------------|----------|---------------|-------------|------------|
| ... | ... | ... | ... | ... | ... |
| **Total** | | | | **$X,XXX,XXX** | **100%** |

| Guardrail | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| ... | ... | ... | ... |
```

## Step 5: Present Dashboard (0 tool calls — in response)

Apply lifecycle stage greeting from timecell.md. Lead with numbers (Speed to Value).

1. Portfolio table (net worth by entity and asset class)
2. Guardrail status table
3. Change since last snapshot (if exists)
4. 0-3 priority items (CRITICAL/WARNING guardrails only)
5. React dashboard artifact (net worth hero, allocation bars, guardrail cards)

### Plugin-Aware
If bitcoin-specific skills are available: include BTC temperature and custody sections.
If NOT available: show BTC as regular asset class with standard allocation analysis.

## Output Rules
- Tables first, narrative second
- Bold totals row
- Round percentages to whole numbers
- Comma separators for numbers > 999
- Guardrail labels: CRITICAL / WARNING / WATCH / SAFE / STRONG (no emoji)
- See `references/formatting.md` for full standards
