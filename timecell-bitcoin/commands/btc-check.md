---
description: >
  Deep Bitcoin analysis — temperature, selling ladder, crash survival, DCA, conviction assessment.
  Triggers: "bitcoin check", "BTC status", "selling ladder", "BTC temperature",
  "hedge status", "how's my bitcoin", "crypto deep dive"
argument-hint: ""
---

# /tc:btc-check — Bitcoin Intelligence

## When NOT to use
- Non-BTC crypto analysis — not supported
- General portfolio overview — use /tc:start (includes BTC summary automatically)
- What-if scenarios not specific to BTC — use /tc:check or financial-reasoning skill

## Budget: 2-3 tool calls max. Do NOT use WebSearch, ToolSearch, or load skills.

## Step 1: Read + Fetch (1 bash call)

    TC_DATA="${CLAUDE_PLUGIN_DATA:-.timecell}"; cat profile.md entities/*.md 2>/dev/null; echo "===BTC_SEP==="; cat references/bitcoin-formulas.md 2>/dev/null; echo "===BTC_SEP==="; cat references/bitcoin-conviction.md 2>/dev/null; echo "===BTC_SEP==="; cat references/hedge-formulas.md 2>/dev/null; echo "===BTC_SEP==="; python3 scripts/fetch-btc-data.py 2>/dev/null; echo "===BTC_SEP==="; cat "$TC_DATA/bitcoin/tier-status.md" 2>/dev/null; echo "===BTC_SEP==="; cat "$TC_DATA/bitcoin/temperature-log.md" 2>/dev/null; echo "===BTC_SEP==="; cat .claude/timecell-bitcoin.local.md 2>/dev/null

Returns: profile + entities, bitcoin formulas, conviction framework, hedge formulas, live market data (JSON), tier execution history, temperature history.

**If no entities with BTC:** Stop → "No BTC holdings found. Add a bitcoin entity first."

## Step 2: Write State (1 tool call)

Write updated state to the data directory (`${CLAUDE_PLUGIN_DATA}` or `.timecell/`) under `bitcoin/`:

**temperature-log.md** — Append one line:

    | YYYY-MM-DD HH:MM | score | zone | source |

**tier-status.md** — Update if any new tiers triggered since last check (respecting 48h sustain rule and 3-point buffer).

Create the bitcoin data directory if it doesn't exist: `mkdir -p "${CLAUDE_PLUGIN_DATA:-.timecell}/bitcoin"`

## Step 3: Respond (0 tool calls)

Compute ALL of the following inline using bitcoin-formulas.md:

### 1. BTC Temperature
- Composite score (0-100), zone name
- Trend: compare to last 3 readings from temperature-log.md (up/down/flat arrow)
- Source attribution (timecell-api / coinmetrics-fallback / manual)

### 2. Selling Status
- Which tiers are triggered at current temperature
- Cumulative % to sell, dollar amount (from liquid BTC entities)
- Distance from floor (50% of original position)
- 48h sustain status: "confirmed" if sustained, "pending N hours" if recent

### 3. Crash Survival Matrix
All 5 scenarios from bitcoin-formulas.md:
- Post-crash portfolio value
- Post-crash runway months
- Zone classification (CRITICAL/WARNING/SAFE)

### 4. Deployment Status
- Current drawdown from ATH (if available from market data)
- Which deployment tier is active (if in drawdown)
- Opportunity fund balance and deployable amount

### 5. DCA Recommendation
- Current temperature to multiplier from table
- Monthly DCA amount (multiplier x baseline from profile)

### 6. Conviction Assessment
Frame per bitcoin-conviction.md:
- Current zone framing language
- Any belief tensions with user's portfolio state
- Action items aligned to framework

### 7. Hedge Status (if hedge_positions exist in profile/entities)

If the user's profile or entities contain hedge positions (put options, collars, or similar):

Run hedge engine calls in a single bash step:

    python3 scripts/hedge-engine.py calculateHedgeCoverage '{"positions": [...], "total_btc_holdings": N, "btc_price": P}' 2>/dev/null; echo "===HEDGE_SEP==="; python3 scripts/hedge-engine.py calculateLayerExits '{"positions": [...], "btc_price": P}' 2>/dev/null; echo "===HEDGE_SEP==="; python3 scripts/hedge-engine.py calculateHedgeBudget '{"temperature": T, "portfolio_value_usd": V}' 2>/dev/null

Present:
- Coverage %, health score, nearest expiry
- Layer exits with action recommendations
- Budget status vs temperature-based target
- Reference hedge-formulas.md for all threshold explanations
- Framework attribution on all recommendations

**If no hedge_positions:** Skip this section entirely. Do not mention hedging unless the user asks.

### 8. React Dashboard Artifact
Visual summary with temperature gauge, selling ladder status, crash matrix, and DCA recommendation.

**Output rules:** Tables first, bold totals, whole % numbers, comma separators > 999, no emoji. Frame everything through conviction framework.
