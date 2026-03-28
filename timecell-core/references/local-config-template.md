# User Local Config (.local.md)

Per-user preferences that don't belong in profile.md or credentials.

## What Goes Where

| File | Content | Example |
|------|---------|---------|
| `profile.md` | Financial data | Holdings, goals, burn rate, base currency |
| `credentials.enc` | Secrets | API keys, account tokens |
| `.claude/<module>.local.md` | UX preferences | Response length, display units, hidden sections |

## Creating Your Local Config

Create `.claude/timecell.local.md` in your project root with YAML frontmatter:

```yaml
---
preferred_response_length: concise  # concise | standard | detailed
dashboard_sections_hidden: []  # sections to skip in /tc:start (e.g. ["guardrails", "delta"])
custom_greeting: ""  # override CIO greeting text
advisor_names: []  # names the CIO should recognize as advisors
---
```

## Add-On Local Configs

Each add-on module can have its own `.local.md`:

**timecell-bitcoin** — `.claude/timecell-bitcoin.local.md`:
```yaml
---
preferred_exchange: coinbase  # price source preference
deribit_account: ""  # Deribit subaccount name
btc_display_unit: btc  # btc | sats
selling_ladder_notify: true  # alert on ladder trigger
---
```

**timecell-indian-mf** — `.claude/timecell-indian-mf.local.md`:
```yaml
---
preferred_amcs: []  # AMC preferences for recommendations
sip_dates: []  # SIP debit dates to track
folio_numbers: {}  # scheme -> folio mapping
direct_plan_preference: true  # prefer direct over regular
---
```

**timecell-estate** — `.claude/timecell-estate.local.md`:
```yaml
---
jurisdiction: ""  # primary jurisdiction for estate planning
trust_type: ""  # revocable | irrevocable | living
key_package_recipients: []  # guardian names for key packages
review_frequency: quarterly  # how often estate review runs
---
```

## Rules

- `.local.md` files are **gitignored** — never committed
- Preferences override defaults but **never override guardrails**
- If a `.local.md` file is missing, all defaults apply
- YAML frontmatter only — no markdown body needed
- The CIO reads these as part of the session start batch read
