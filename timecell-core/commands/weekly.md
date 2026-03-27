---
description: Weekly narrative memo — what changed, trends, and what needs attention
argument-hint: ""
---

# /tc:weekly — Weekly Review

## Budget: 2 tool calls max

## Pre-Check
Session count = `grep -c "^## [0-9]" memory/session-log.md`.
- If < 2 snapshots or session_count <= 3: redirect to /tc:start ("Let's build a few more snapshots first.")

## Step 1: Read All Data (1 bash call)

```bash
cat profile.md 2>/dev/null; echo "===SEP==="; cat snapshots/*.md 2>/dev/null | tail -n 200; echo "===SEP==="; cat decisions/*.md 2>/dev/null | tail -n 100; echo "===SEP==="; cat memory/session-log.md 2>/dev/null | tail -n 50
```

Returns: profile, recent snapshots (past 7-14 days), recent decisions, session log.

## Step 2: Compute Deltas (inline)
- Net worth change ($ and %)
- Allocation drift from 7 days ago
- Guardrail zone changes
- New entities

## Step 3: Write Memo + Log (1 tool call)

Structure (200-400 words, CIO-to-principal tone):
1. Headline (one sentence)
2. Portfolio movement (market, transactions, FX)
3. Guardrail status (zone changes)
4. Decisions made (reference decisions/)
5. Looking ahead

Append to `memory/session-log.md`.

## Rules
- NO React dashboard — narrative only
- 200-400 words
- Specific numbers and dates
- Conversational, not bullets
