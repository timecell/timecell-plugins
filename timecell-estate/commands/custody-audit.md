---
description: >
  Custody posture assessment — self-custody ratio, key security, backup, recovery cadence, geographic distribution, succession readiness.
  Triggers: "custody audit", "custody check", "custody review", "self-custody", "key security", "backup check", "recovery test"
argument-hint: ""
---

# /tc:custody-audit — Custody Posture Assessment

## When NOT to use
- Estate document completeness → use /tc:estate-check
- Key package generation → use /tc:create-key-package
- General Bitcoin analysis → use /tc:btc-check

## Tool Call Budget: 2-3

## Persona
Family Office OS — thorough, direct, security-focused. Custody is existential for Bitcoin holders.

## Prerequisites
- memory/profile.md must exist and include a BTC Custody Setup or Custody Setup section
- If no custody data: "I don't have your custody details. Tell me about your custody setup so I can assess it."

## Step 1: Load Context (single bash read)

Read ALL in one tool call:
- memory/profile.md (identity, custody setup, succession, estate_documents)
- references/custody-formulas.md (all thresholds and scoring rules)
- references/custody-audit-workflow.md (scoring and output format)
- .claude/timecell-estate.local.md (user preferences, optional)

## Step 2: Write Session Log

Append to memory/session-log.md:
```
### /tc:custody-audit — [date]
Grade: [X]. Overall: [zone]. [One-line summary.]
```

## Step 3: Output (0 tool calls)

Apply references/custody-audit-workflow.md — six dimensions, overall zone, scorecard, actions.
