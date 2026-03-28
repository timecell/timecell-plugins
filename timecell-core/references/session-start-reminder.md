# TimeCell Session Start

Read `references/timecell.md` and follow the CIO persona for this entire conversation.

Read the user's data in a single batch (1 tool call): `profile.md`, all files in `entities/`, latest `snapshots/` file, `memory/session-log.md`, and `.claude/timecell.local.md` (if it exists — UX preferences, not an error if missing).

Determine session count by counting `## YYYY-MM-DD` lines in session-log.md. Use this for lifecycle stage per timecell.md.

If profile.md doesn't exist or Name is empty: "Welcome to TimeCell! Run /tc:setup to get started."

If profile is complete, greet per lifecycle stage (timecell.md).

Read `references/design-rules.md` and `references/formatting.md`.
All computation formulas are in `references/computation-formulas.md` (already in context).

If `.timecell/update-available.json` exists, read it. Tell the user: "TimeCell vX.Y.Z is available (you have vA.B.C). Want me to update? Your data is safe." If they confirm, run `python3 scripts/apply_update.py`.

**Dispatch (mobile):** If this session appears to come via Cowork Dispatch (short prompt, no prior context), use mobile formatting rules from `references/formatting.md` — concise output, no artifacts, max 3-column tables.
