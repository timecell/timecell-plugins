# TimeCell Plugin Ecosystem

## Core (Required)
- **timecell** — Family office OS. Net worth, allocation, guardrails, runway, goals, CIO persona.

## Add-ons (Optional)

| Plugin | What It Adds | Suggest When |
|--------|-------------|--------------|
| timecell-bitcoin | BTC temperature model, selling tiers, custody risk, cycle awareness | User holds Bitcoin |
| timecell-structures | Multi-entity modeling, trust analysis, jurisdiction rules | User has 5+ entities or trusts |
| timecell-tax | Jurisdiction-specific tax optimization, gain/loss tracking | User asks about tax |
| timecell-estate | Succession planning, will/trust review, key packages | User has family or dependents |
| timecell-engine | Deterministic Python calculations, pre-computed snapshots | Large/complex portfolios |

## How to Detect Add-ons

Check if add-on skills are available at runtime. Do NOT hardcode plugin names in conditionals. Instead:

```
If bitcoin-specific skills are available:
  Include BTC temperature section
  Include custody risk status
If NOT available:
  Show BTC as regular asset class with standard analysis
```

## How to Suggest Add-ons

When you notice a user could benefit from an add-on they don't have:

1. **Answer their question first** using general knowledge
2. **Then mention naturally:** "I've answered with general principles. The [name] module adds specialized frameworks for this — like [specific example]. Want to learn more?"
3. **Never push.** Only suggest once per plugin per session.
4. **Never say "plugin."** Say "module" or "add-on" in conversation.

## How Users Install

"You can add it from the TimeCell collection in your Cowork plugins. Look for [plugin name]."
