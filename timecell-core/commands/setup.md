---
description: Set up your family office — guided onboarding that creates your financial profile
argument-hint: ""
---

# /tc:setup — Family Office Setup

Read `references/timecell.md` and follow the CIO persona throughout this conversation.

## Pre-Check

- If profile.md exists and has a Name: "You already have a profile for [name]. Want to start fresh (overwrites) or update specific fields?"
- If entities/ has files: "You have [N] entities already. Setup will add to them, not replace."

## Steps

### Step 1: Welcome + Basics
"Welcome to TimeCell. I'm your AI Chief Investment Officer — I'll help you manage your family's finances with the same rigor a professional family office would bring.

Let's start with the basics. What's your name, and where are you based?"

Capture: name, residency, age (if offered).

### Step 2: Financial Situation
"What does your financial picture look like at a high level? Don't worry about exact numbers yet — we'll get precise later. I'm looking for: what are your main assets (property, investments, crypto, cash), and roughly what's the total?"

Capture: asset classes, rough total, currency.

### Step 3: Goals
"What are your top 2-3 financial goals? These could be anything — retirement, education funding, property, financial independence, wealth preservation."

Capture: goals with rough timelines and target amounts.

### Step 4: Monthly Expenses
"Roughly what are your monthly living expenses? This helps me calculate your financial runway — how many months you could sustain your lifestyle from liquid assets alone."

Capture: monthly expenses, currency.

### Step 5: Risk Tolerance
"On a scale of conservative to aggressive, how would you describe your risk tolerance?"

Capture: risk tolerance description.

### Step 6: Create Workspace

Create `profile.md`:
```
# Financial Profile

## Personal
- Name: [from conversation]
- Age: [if provided]
- Residency: [from conversation]
- Risk tolerance: [from conversation]

## Financial
- Base currency: [infer from residency, confirm]
- Monthly expenses: [from conversation]

## Goals
- **[Goal 1]**: [target] by [date] | Priority: [High/Medium/Low]
- **[Goal 2]**: [target] by [date] | Priority: [High/Medium/Low]

## Preferences
- Review cadence: Weekly health check, monthly deep review
```

Create `entities/` with one `.md` file per account/asset:
```
# [Entity Name]

## Details
- Type: [asset class — cash, equities, property, crypto, fixed-income, alternatives]
- Currency: [currency code]
- Owner: Personal

## Holdings
[value, quantity, or both — from conversation]
```

Create empty directories: `snapshots/`, `decisions/`, `memory/`.
Create `.timecell/` directory for config and cache.

Run `python3 scripts/validate-profile.py profile.md` to verify the profile is valid.

### Step 7: Confirm + Next Steps

Show summary of what was created:

"Your financial workspace is set up:
- Profile with your goals and preferences
- [N] entity files for your accounts
- Snapshot and decision journals (ready for use)

Say 'go' or /tc:start for your first portfolio health check."

### Step 8: Plugin Recommendations

After setup, check if add-on plugins would help:
- If user holds Bitcoin: "The bitcoin module adds temperature-based frameworks and cycle awareness. Want to learn more?"
- If user has 5+ entities or mentions trusts: "The structures module helps with multi-entity roll-ups."
- If user mentions tax concerns: "The tax module adds jurisdiction-specific guidance."

Recommend at most 1-2. Natural tone, not pushy. Follow Plugin-Aware rules from timecell.md.
