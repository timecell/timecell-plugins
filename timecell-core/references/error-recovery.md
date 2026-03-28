# Error Recovery

At session start, check the data directory (`${CLAUDE_PLUGIN_DATA}` or `.timecell/`) for `session-errors.json` with retryable errors (max 3):
- If errors found: "Last session, [operation] failed — [error]. Let me try again."
- Re-run. Report success or continued failure.
- Never apologize. Matter-of-fact. 1-2 lines per error.
- Never block session start — handle errors then proceed to greeting.
