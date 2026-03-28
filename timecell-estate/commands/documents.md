---
description: >
  Estate document registry — structured tracking with completeness scoring and CRUD operations.
  Triggers: "documents", "document registry", "estate documents", "add document", "document status", "missing documents"
argument-hint: "[list|add|update|find|--open|--summary]"
---

# /tc:documents — Estate Document Registry

## When NOT to use
- Estate completeness review → use /tc:estate-check
- Key package generation → use /tc:create-key-package
- General file management → not a TimeCell function

## Tool Call Budget: 2-3

## Step 1: Load Context (single bash read)

Read ALL in one tool call:
- documents/index.md (document registry)
- references/documents-workflow.md (subcommands, types, flows, output format)
- .claude/timecell-estate.local.md (user preferences, optional)

## Step 2: Execute Subcommand

Apply references/documents-workflow.md — route to correct flow (list/add/update/find/open/summary).

For **list** flow, run scoring script:
```bash
cat documents/index.md 2>/dev/null; echo '---SEPARATOR---';
python3 scripts/documents-checker.py score documents/index.md;
echo '---SEPARATOR---';
python3 scripts/documents-checker.py expiring documents/index.md;
echo '---SEPARATOR---';
python3 scripts/documents-checker.py categories documents/index.md
```

For **add** flow: validate type (HARD GATE), write entry, confirm.

## Step 3: Output

Apply references/documents-workflow.md output rules. Always include completeness score and legal disclaimer.
