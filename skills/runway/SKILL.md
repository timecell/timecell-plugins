---
name: runway
description: |
  Calculate financial runway — months of expenses covered by liquid assets. Factors in
  burn rate, income, and liquid/illiquid classification. Used by /tc:start and /tc:check.
  Triggers on "runway", "how long can I last", "burn rate", "months of safety",
  "living expenses", "emergency fund".
---

# Runway Computation

## Workflow

### Step 1: Classify Assets
From entities/, classify each as liquid or illiquid:

| Liquid | Illiquid |
|--------|----------|
| Cash, savings accounts | Property, real estate |
| Listed equities (public markets) | Private equity, venture |
| Stablecoins | Locked/vesting positions |
| Money market funds | Art, collectibles |
| Short-term bonds (<1yr) | Business equity |

If classification is unclear, ask: "Is [entity] something you could liquidate within 30 days?"

### Step 2: Get Monthly Burn
From profile.md, read monthly_expenses field. If missing:
- Check if /tc:setup captured expenses
- If not: "What's your approximate monthly spending? This helps me calculate runway."

### Step 3: Compute

**No income:**
```
Runway = Total Liquid Assets / Monthly Expenses
```

**With income:**
```
Net Monthly Burn = Monthly Expenses - Monthly Income
Runway = Total Liquid Assets / Net Monthly Burn
```

**Positive cash flow (income > expenses):**
Runway = "Indefinite (positive cash flow of $X,XXX/month)"

### Step 4: Present

Lead with the number:
```
Runway: XX months
```

| Component | Value |
|-----------|-------|
| Liquid assets | $XXX,XXX |
| Monthly expenses | $X,XXX |
| Monthly income | $X,XXX |
| Net burn rate | $X,XXX |
| **Runway** | **XX months** |

### Step 5: Zone Assignment
Apply thresholds from `guardrails` skill (CRITICAL < 12, WARNING 12-18, WATCH 18-24, SAFE 24-36, STRONG > 36).
