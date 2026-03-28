# User Local Config (.local.md)

Per-user preferences that override defaults but never override guardrails. Gitignored — never committed.

## What It Is

`.local.md` files store UX preferences: response length, hidden dashboard sections, display units, AMC preferences. They complement `profile.md` (financial data) and `credentials.enc` (secrets).

## How to Create

Create `.claude/timecell.local.md` in your project root:

```yaml
---
preferred_response_length: concise  # concise | standard | detailed
dashboard_sections_hidden: []  # sections to skip in /tc:start
custom_greeting: ""  # override CIO greeting text
advisor_names: []  # names the CIO should recognize as advisors
---
```

## Module-Specific Configs

Each add-on reads its own `.local.md` if present:

| Module | File | Example Fields |
|--------|------|----------------|
| Core | `.claude/timecell.local.md` | response_length, hidden sections, greeting |
| Bitcoin | `.claude/timecell-bitcoin.local.md` | btc_display_unit (btc/sats), preferred_exchange |
| Indian MF | `.claude/timecell-indian-mf.local.md` | preferred_amcs, sip_dates, direct_plan_preference |
| Estate | `.claude/timecell-estate.local.md` | jurisdiction, trust_type, review_frequency |

## Reading Pattern

Commands read `.local.md` in the mega-bash cat chain with `/dev/null` fallback:

```bash
cat .claude/timecell.local.md 2>/dev/null
```

If missing, all defaults apply. Preferences override defaults but never override guardrails or thresholds.

## Rules
- YAML frontmatter only — no markdown body needed
- Gitignored — never committed to repo
- Missing file = all defaults apply
- Preferences never override financial guardrails
