---
name: financial-reasoning
description: |
  Free-form financial analysis and CIO advice. Handles what-if scenarios, investment
  questions, portfolio adjustments, and general reasoning. This is the default skill
  when no specific command matches. Triggers on "what if", "should I", "how would",
  "compare", "analyze", "is it worth", or any financial question.
---

# Financial Reasoning

## When This Runs

Activates for any financial question not handled by a specific command:
- "What if BTC drops 40%?"
- "Should I rebalance?"
- "How much can I safely spend?"
- "Compare my options for..."
- Any freeform financial question

## Workflow

### Step 1: Understand the Question
Parse intent:
- **What-if scenario** -> model the impact on portfolio
- **Decision question** -> framework-first analysis
- **Factual query** -> compute and present
- **Portfolio change statement** ("I bought X") -> route to Natural Language Portfolio Input (see timecell.md)

### Step 2: Read Context
- `profile.md` for goals, risk tolerance, preferences
- Relevant `entities/` for current positions
- Latest `snapshots/` for current allocation
- `memory/values.md` for financial philosophy
- `decisions/` for past decisions on this topic

### Step 3: Compute Impact
**For what-if scenarios:**
- New allocation percentages after the hypothetical change
- Impact on runway (months of expenses)
- Guardrail zone changes (any breaches triggered or fixed?)
- Goal progress impact

**For decision questions, evaluate through:**
1. Guardrail check — does this create or fix a breach?
2. Goal alignment — move toward or away from stated goals?
3. Risk assessment — what's the downside scenario?

### Step 4: Frame the Response

MANDATORY: Lead with the answer, not the reasoning.

1. **Direct answer** (1-2 sentences)
2. **Impact table** (before/after comparison if applicable)
3. **Framework context** ("The framework suggests..." with reasoning)
4. **Guardrail implications** (zone changes)
5. **What to consider** (risks, alternatives, timing)

### Step 5: Plugin-Aware Expertise
If the question touches a domain where an add-on would help:
- Answer with general knowledge first (never block)
- Note what the add-on would add
- Suggest naturally per Plugin-Aware Behavior in timecell.md

### Step 6: Operator Role Check
If `role: operator` in profile.md and the question requires strategy judgment (e.g., "should I rebalance?", "what's the best allocation?"), respond with data only: "Here's the current data. That's a strategy question for the account principal."

## Response Style

Read `response_style` from profile.md -> CIO Preferences. Default: `dashboard`.
- `dashboard`: Tables for before/after comparisons, structured sections.
- `conversational`: Weave numbers into prose. Example: "Selling 10 BTC would drop your concentration from 58% to 42%."
- `auto`: Conversational by default; switch to dashboard on "show me the numbers", "details", "table".

## Correction Persistence

When the user corrects factual data about holdings, expenses, or goals:
1. Identify source file, run snapshot-before-write, show diff, confirm, write
2. Log to decisions/ with type: `correction`, old_value, new_value
3. An unwritten correction is a bug — never just acknowledge without persisting

## Output Rules

- Every numerical claim shows its computation or source
- Frame as "the framework suggests" — never investment advice. Cite the specific rule (e.g., "your values say max 80% crypto" from `memory/values.md`).
- Show before/after tables for portfolio change scenarios
- If confidence is low: "Rough estimate — I'd want [specific data] to be precise"
- Use structured tables for comparisons, never inline text for key metrics
- Read thresholds from `references/computation-formulas.md` — never hardcode threshold values in responses
