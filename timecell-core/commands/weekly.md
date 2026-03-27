---
description: Weekly narrative memo — what changed, trends, and what needs attention
argument-hint: ""
---

# /tc:weekly — Weekly Review

Read `references/timecell.md` and follow the CIO persona.

## Pre-Check
- Need 2+ snapshots for trend comparison. If only 1: redirect to /tc:start with "Let's build a few more snapshots first."
- If session_count <= 3: redirect to /tc:start with brief explanation.

## Workflow

### Step 1: Read Data
- All snapshots from past 7-14 days
- `decisions/` for recent decision entries
- `memory/session-log.md` for recent activity
- `profile.md` for context

### Step 2: Compute Deltas
- Net worth change (absolute and %)
- Allocation drift from 7 days ago
- Guardrail zone changes
- New entities added or removed

### Step 3: Write Narrative Memo

Structure (200-400 words, conversational CIO-to-principal tone):

1. **Headline** — one-sentence week summary
2. **Portfolio Movement** — what changed and why (market moves, transactions, FX)
3. **Guardrail Status** — zone changes this week
4. **Decisions Made** — reference entries in decisions/
5. **Looking Ahead** — what to watch next week

### Step 4: Log
Append to `memory/session-log.md`.

## Rules
- NO React dashboard artifact — narrative memo only
- 200-400 words target
- Reference specific numbers and dates
- Conversational tone, not bullet-point summary
