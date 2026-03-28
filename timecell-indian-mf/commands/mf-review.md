---
description: Deep Indian mutual fund review — SEBI classification, underperformers, ELSS lock-in, SIP health, expense ratio audit
argument-hint: ""
---

# /tc:mf-review — Indian Mutual Fund Intelligence

## Budget: 2-3 tool calls max. Do NOT use WebSearch, ToolSearch, or load skills.

## Step 1: Read + Fetch (1 bash call)

    cat profile.md entities/*.md 2>/dev/null; echo "===MF_SEP==="; cat references/mf-computation-formulas.md 2>/dev/null; echo "===MF_SEP==="; cat references/mf-category-classification.md 2>/dev/null; echo "===MF_SEP==="; cat references/indian-entity-types.md 2>/dev/null; echo "===MF_SEP==="; cat references/inr-formatting.md 2>/dev/null; echo "===MF_SEP==="; python3 scripts/fetch-mf-data.py 2>/dev/null; echo "===MF_SEP==="; python3 scripts/fetch-zerodha-data.py --mf-only 2>/dev/null; echo "===MF_SEP==="; cat .timecell/indian-mf/category-snapshot.json 2>/dev/null; echo "===MF_SEP==="; cat .timecell/indian-mf/underperformer-log.md 2>/dev/null

Returns: profile + entities, computation formulas, category classification, entity types, INR formatting, live NAV data (JSON), Zerodha MF data (JSON), category snapshot history, underperformer log.

**If no MF holdings found in profile or Zerodha:** Stop -> "No mutual fund holdings found. Add MF schemes to your profile or connect Zerodha."

## Step 2: Write State (1 tool call)

Write updated state to `.timecell/indian-mf/`:

**category-snapshot.json** — Current category allocation snapshot:

    {"date": "YYYY-MM-DD", "equity_pct": N, "debt_pct": N, "hybrid_pct": N, "other_pct": N, "scheme_count": N, "total_aum": N}

**underperformer-log.md** — Append one line per flagged underperformer:

    | YYYY-MM-DD | scheme_name | 1Y_return | category_avg | delta | severity |

Create `.timecell/indian-mf/` directory if it doesn't exist (use `mkdir -p` in the write command).

## Step 3: Respond (0 tool calls)

Compute ALL of the following inline using mf-computation-formulas.md. Format all INR amounts per inr-formatting.md.

### 1. MF Portfolio Summary
- Total AUM (INR, Lakh/Crore notation)
- Scheme count, data freshness (NAV date, Zerodha sync time)
- Entity breakdown if multi-entity (HUF, company, personal)

### 2. Category Allocation vs Targets
- Equity / Debt / Hybrid / Other split (actual %)
- Drift from target allocation (if set in profile)
- SEBI category breakdown within equity (large/mid/small/flexi/sectoral)
- Flag: sectoral/thematic > 15% of MF portfolio

### 3. ELSS Lock-in Matrix
- Per-SIP-installment unlock dates (from mf-computation-formulas.md ELSS rules)
- Total locked amount, total unlocked amount
- Next unlock date and amount
- 80C utilization (if deduction data available)

### 4. SIP Health
- Active SIPs: count, monthly commitment (INR)
- Paused/stopped SIPs flagged
- SIP-to-lump-sum ratio
- Missing SIPs (schemes without active SIP that should have one)

### 5. Underperformer Deep Dive
- Each scheme: 1Y return vs SEBI category average
- XIRR for SIP investments (using mf-computation-formulas.md algorithm)
- Delta classification: mild / significant / severe
- Action recommendation: hold / review / exit

### 6. Direct vs Regular Audit
- Schemes on regular plan (detected from fund name)
- Estimated annual savings from switching to direct
- Priority list: largest savings first

### 7. Expense Ratio Flags
- Schemes where TER > category median + 50bps
- Category median TER comparison table
- Total portfolio-weighted TER

### 8. React Dashboard Artifact
Visual summary with:
- Category allocation pie/donut chart
- Underperformer heatmap
- SIP health status indicators
- ELSS lock-in timeline
- Direct vs regular breakdown

**Output rules:** Tables first, bold totals, use INR Lakh/Crore notation per inr-formatting.md, comma separators, no emoji. Use indian-entity-types.md for entity-specific tax context.
