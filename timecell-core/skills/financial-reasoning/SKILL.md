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

## Output Rules

- Every numerical claim shows its computation or source
- Frame as "the framework suggests" — never investment advice
- Show before/after tables for portfolio change scenarios
- If confidence is low: "Rough estimate — I'd want [specific data] to be precise"
- Use structured tables for comparisons, never inline text for key metrics
