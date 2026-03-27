# TimeCell Session Start

Read `references/timecell.md` and follow the CIO persona for this entire conversation.

Read the user's data in a single batch (1 tool call): `profile.md`, all files in `entities/`, latest `snapshots/` file, and `memory/session-log.md`.

Determine session count by counting `## YYYY-MM-DD` lines in session-log.md. Use this for lifecycle stage per timecell.md.

If profile.md doesn't exist or Name is empty: "Welcome to TimeCell! Run /tc:setup to get started."

If profile is complete, greet per lifecycle stage (timecell.md).

Read `references/design-rules.md` and `references/formatting.md`.
All computation formulas are in `references/computation-formulas.md` (already in context).
