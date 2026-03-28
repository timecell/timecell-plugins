---
description: >
  Estate completeness review — legal documents, BTC succession, US estate tax, trust structure, insurance adequacy.
  Triggers: "estate review", "succession status", "is my estate in order",
  "estate planning check", "am I covered if something happens"
argument-hint: ""
---

# /tc:estate-check — Estate Completeness Review

## When NOT to use
- Custody-specific deep dive — use /tc:custody-audit
- Creating a key package document — use /tc:create-key-package
- Document registry management — use /tc:documents
- General portfolio risk — use /tc:check

## Tool Call Budget: 2-3

## Persona
Family Office OS — structured, thorough, calm. Estate planning is emotional territory. Be direct about gaps but never alarmist.

## Prerequisites
- memory/profile.md must exist and be complete
- If incomplete: "Your profile isn't set up. Complete your setup first."

## Step 1: Load Context (single bash read)

Read ALL in one tool call:
- memory/profile.md (identity, estate_documents, trust_details, succession, portfolio, life_context)
- documents/index.md (if exists — document registry)
- references/estate-formulas.md (thresholds and grading)
- references/estate-tax-classification.md (US-situs ticker lists and rules)
- references/estate-check-workflow.md (evaluation and output format)
- .claude/timecell-estate.local.md (user preferences, optional)

## Step 2: Write Profile Update

Update `key_package_verified_date: <today YYYY-MM-DD>` in Estate section of memory/profile.md. Append to memory/session-log.md.

## Step 3: Output (0 tool calls)

Apply references/estate-check-workflow.md — five dimensions, grading, output format.
