---
description: >
  Deep Indian mutual fund review — SEBI classification, underperformers, ELSS lock-in, SIP health, expense ratio audit.
  Triggers: "mutual fund review", "MF check", "SIP status", "underperformers",
  "ELSS lock-in", "expense ratio", "how are my mutual funds"
argument-hint: ""
---

# /tc:mf-review — Indian Mutual Fund Intelligence

## When NOT to use
- Direct equity or stock analysis — not covered
- Fixed deposits, insurance, or non-MF debt instruments — not covered
- General portfolio overview — use /tc:start
- Non-Indian mutual funds — not supported (SEBI classification specific)

## Budget: 2-3 tool calls max. Do NOT use WebSearch, ToolSearch, or load skills.

## Step 1: Read + Fetch (1 bash call)

    cat profile.md entities/*.md 2>/dev/null; echo "===MF_SEP==="; cat references/mf-computation-formulas.md 2>/dev/null; echo "===MF_SEP==="; cat references/mf-category-classification.md 2>/dev/null; echo "===MF_SEP==="; cat references/indian-entity-types.md 2>/dev/null; echo "===MF_SEP==="; cat references/inr-formatting.md 2>/dev/null; echo "===MF_SEP==="; cat references/mf-review-workflow.md 2>/dev/null; echo "===MF_SEP==="; python3 scripts/fetch-mf-data.py 2>/dev/null; echo "===MF_SEP==="; python3 scripts/fetch-zerodha-data.py --mf-only 2>/dev/null; echo "===MF_SEP==="; cat .timecell/indian-mf/category-snapshot.json 2>/dev/null; echo "===MF_SEP==="; cat .timecell/indian-mf/underperformer-log.md 2>/dev/null; echo "===MF_SEP==="; cat .claude/timecell-indian-mf.local.md 2>/dev/null

**If no MF holdings found in profile or Zerodha:** Stop -> "No mutual fund holdings found. Add MF schemes to your profile or connect Zerodha."

## Step 2: Write State (1 tool call)

Write updated state to `.timecell/indian-mf/`:

**category-snapshot.json** — Current category allocation snapshot:

    {"date": "YYYY-MM-DD", "equity_pct": N, "debt_pct": N, "hybrid_pct": N, "other_pct": N, "scheme_count": N, "total_aum": N}

**underperformer-log.md** — Append one line per flagged underperformer:

    | YYYY-MM-DD | scheme_name | 1Y_return | category_avg | delta | severity |

Create `.timecell/indian-mf/` directory if it doesn't exist (use `mkdir -p` in the write command).

## Step 3: Respond (0 tool calls)

Apply references/mf-review-workflow.md — all 8 sections including React dashboard artifact.
