---
description: >
  Bitcoin key package generator — standalone succession document for a specific guardian.
  Triggers: "key package", "create key package", "succession document", "guardian letter", "dead man's switch"
argument-hint: "[--for <guardian_name>]"
---

# /tc:create-key-package — Bitcoin Key Package Generator

## When NOT to use
- Estate completeness overview → use /tc:estate-check
- Custody posture check → use /tc:custody-audit
- General estate documents → use /tc:documents

## Tool Call Budget: 2-4

## Syntax
```
/tc:create-key-package --for <guardian_name>
/tc:create-key-package
```

## Step 1: Load Context (single bash read)

Read ALL in one tool call:
- memory/profile.md (identity, succession, portfolio, custody setup, estate_documents, trust_details)
- references/key-package-template.md (structure reference)
- references/create-key-package-workflow.md (generation rules and output format)
- .claude/timecell-estate.local.md (user preferences, optional)

**Check 1 — Successor exists:** If `succession.successor_named` is `no` or null: STOP. Explain that a key package requires a recipient.
**Check 2 — Guardian name:** If `--for <name>` provided, use it. Otherwise, use primary successor from profile.

## Step 2: Generate + Save (1-2 tool calls)

Apply references/create-key-package-workflow.md — custody-adaptive generation, all mandatory sections.

Save to `documents/estate/key-package-<guardian_name_lowercase>.md`. Create directory if needed.

## Step 3: Update Profile

In memory/profile.md: set `key_package: yes`, `key_package_created: <today>`, `last_verified: <today>`, `key_package_verified_date: <today>` under Estate/succession.

Append to memory/session-log.md.
