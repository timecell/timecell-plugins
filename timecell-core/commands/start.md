---
description: >
  Daily portfolio health check — net worth, allocation, guardrails, and what needs attention.
  Triggers: "how am I doing", "portfolio check", "daily snapshot", "what's my net worth",
  "show me my portfolio", "financial overview", "where do I stand"
argument-hint: ""
---

# /tc:start — Portfolio Health Check

## When NOT to use
- Deep what-if analysis or scenario modeling — use financial-reasoning skill
- Estate or succession questions — use /tc:estate-check
- Bitcoin-specific deep dive — use /tc:btc-check
- Mutual fund drill-down — use /tc:mf-review

## Budget: 2 tool calls max. Do NOT use WebSearch, ToolSearch, or load skills.

## Step 1: Read + Fetch (1 bash call)

```bash
cat profile.md entities/*.md 2>/dev/null; echo "===SEP==="; ls -t snapshots/*.md 2>/dev/null | head -1 | xargs cat 2>/dev/null; echo "===SEP==="; grep -c "^## [0-9]" memory/session-log.md 2>/dev/null || echo 1; echo "===SEP==="; python3 scripts/fetch-exchange-rates.py 2>/dev/null; echo "===SEP==="; cat .claude/timecell.local.md 2>/dev/null
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

## Role Check (0 tool calls — uses Step 1 data)

Read `role:` from profile.md (default: `principal`). If `role: operator`:
- Suppress lifecycle greeting, strategy, pack beliefs, memory enrichment
- If `managed_entities >= 2`: use multi-entity view (aggregated portfolio, entity health table sorted by worst zone, cross-entity alerts per `references/computation-formulas.md`). Filter entities by `managed_by` matching operator name.
- If single entity: standard operator view (holdings + guardrails, no strategy)
- Greeting: "Good [time], [name]. [N] entities under management."
- Footer: "Data current as of [date]. Operational view — strategy deferred to principals."

## Step 3: Respond (0 tool calls)

**Principal (default):** Apply lifecycle stage greeting. Show: portfolio table, guardrail table, delta, CRITICAL items, React dashboard artifact.

**Operator single entity:** Flat greeting, holdings table, guardrails, delta, alerts only.

**Operator multi-entity:** Flat greeting, aggregated portfolio, entity health table, cross-entity alerts, React dashboard.

**Plugin-Aware:** If `btc-check` command exists: run `python3 scripts/fetch-btc-data.py` as part of Step 1 bash call, read `references/bitcoin-formulas.md`, and add BTC Temperature + Selling Status + Crash Readiness sections. Otherwise: treat BTC as a regular asset with price from exchange rates.

**Response Style:** Read `response_style` from profile.md -> CIO Preferences. Default: `dashboard`. If `conversational`: weave numbers into prose instead of tables. If `auto`: use conversational unless user requests data.

**Output rules:** Tables first, bold totals, whole % numbers, comma separators > 999, no emoji.
