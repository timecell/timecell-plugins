---
description: Daily portfolio health check — net worth, allocation, guardrails, and what needs attention
argument-hint: ""
---

# /tc:start — Portfolio Health Check

## Budget: 2 tool calls max. Do NOT use WebSearch, ToolSearch, or load skills.

## Step 1: Read + Fetch (1 bash call)

```bash
cat profile.md entities/*.md 2>/dev/null; echo "===SEP==="; ls -t snapshots/*.md 2>/dev/null | head -1 | xargs cat 2>/dev/null; echo "===SEP==="; grep -c "^## [0-9]" memory/session-log.md 2>/dev/null || echo 1; echo "===SEP==="; python3 scripts/fetch-exchange-rates.py 2>/dev/null
```

Returns: profile, entities, latest snapshot, session count, exchange rates (BTC price under "BTC" key).

**If no profile.md:** Stop → "Welcome to TimeCell! Run /tc:setup to get started."
**If no entities/:** Stop → "No holdings found. Run /tc:setup to add your accounts."

## Step 2: Compute + Write snapshot (1 tool call)

Compute from step 1 data:
- **Net worth:** sum entity values, convert currencies. BTC price under "BTC" key in rates.
- **Allocation:** entity_value / total × 100, round to whole %
- **Runway:** (cash + treasuries + liquid crypto at market) / monthly_burn
- **Guardrails** (thresholds below)
- **Delta** from previous snapshot

**Guardrail thresholds:**
- Runway: CRITICAL < 12mo, WARNING < 24mo, SAFE 24-36mo, STRONG > 36mo
- Single entity: CRITICAL > 50%, WARNING > 40%
- Asset class: WARNING > 50%
- Liquid = cash, treasuries, equities, crypto

Write snapshot to `snapshots/YYYY-MM-DD.md` with tables.

## Step 3: Respond (0 tool calls)

Apply lifecycle stage greeting (session count → stage: 1-3 welcome+starters, 4-10 welcome+hint, 11+ agenda).

1. Portfolio table
2. Guardrail table
3. Delta
4. CRITICAL items only
5. React dashboard artifact

**Plugin-Aware:** If `btc-check` command exists: run `python3 scripts/fetch-btc-data.py` as part of Step 1 bash call, read `references/bitcoin-formulas.md`, and add BTC Temperature + Selling Status + Crash Readiness sections. Otherwise: treat BTC as a regular asset with price from exchange rates.

**Output rules:** Tables first, bold totals, whole % numbers, comma separators > 999, no emoji.
