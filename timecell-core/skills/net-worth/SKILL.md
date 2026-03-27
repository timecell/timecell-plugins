---
name: net-worth
description: |
  Compute total net worth across all entities and currencies. Sum by asset class,
  convert to base currency, handle multi-currency portfolios. Used by /tc:start and
  /tc:monthly. Triggers on "net worth", "total value", "how much am I worth",
  "portfolio value", "what do I have".
---

# Net Worth Computation

## Workflow

### Step 1: Read All Entities
Read every file in `entities/`. Each entity has:
- Type (asset class): cash, equities, property, crypto, fixed-income, alternatives
- Currency
- Value (or quantity x price for assets like BTC)
- Owner (personal, trust, company — if specified)

### Step 2: Get Exchange Rates
For multi-currency portfolios:
- Run `python3 scripts/fetch-exchange-rates.py` for current rates
- If unavailable, use web search for rates
- Convert all values to base currency (from profile.md)
- Record exchange rates used (for snapshot audit trail)

### Step 3: Compute Totals

| Level | Computation |
|-------|-------------|
| Per entity | local value x exchange rate = base currency value |
| Per asset class | sum all entities in that class |
| Total net worth | sum all asset classes |
| Per owner | sum entities grouped by owner (if multiple owners) |

### Step 4: Self-Verify
- Verify individual values sum to total (rounding OK within 0.1%)
- Flag entities with missing or zero values
- Flag entities with stale data (file not updated > 30 days)

### Step 5: Present

Lead with the headline number:
```
Net Worth: $X,XXX,XXX (as of YYYY-MM-DD)
```

Then breakdown table:

| Asset Class | Value | % of Total |
|-------------|-------|------------|
| Cash | $XXX,XXX | XX% |
| Equities | $XXX,XXX | XX% |
| ... | ... | ... |
| **Total** | **$X,XXX,XXX** | **100%** |

## Multi-Owner Portfolios
If entities belong to different owners (personal, trust, company):
- Show consolidated view first (total net worth)
- Then per-owner breakdown if 2+ owners exist
- Property values: note "estimated" unless recently appraised
- Crypto: use current market price, not cost basis
