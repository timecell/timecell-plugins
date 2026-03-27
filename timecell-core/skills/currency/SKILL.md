---
name: currency
description: |
  Handle multi-currency portfolios. Convert between currencies, track exchange rate
  impact, manage base currency preferences. Used by net-worth and other skills.
  Triggers on "currency", "exchange rate", "convert", "FX impact", "foreign exchange".
---

# Multi-Currency Handling

## Base Currency
- Every user has a base currency in profile.md
- All summary views show values in base currency
- Original currency values are preserved in entity files

## Conversion
- Use `python3 scripts/fetch-exchange-rates.py` for rates
- If unavailable, fall back to web search
- Always record which rates and timestamps were used
- Record rate source in snapshots for audit trail

## Display Format

When showing multi-currency data:

| Entity | Currency | Local Value | Rate | Base Value |
|--------|----------|-------------|------|------------|
| SGX Brokerage | SGD | S$90,000 | 0.7543 | $67,887 |
| BTC Cold | BTC | 2.5 | 87,360 | $218,400 |
| Melbourne House | AUD | A$850,000 | 0.6526 | $554,710 |

## FX Impact Analysis

When comparing snapshots across dates, separate genuine value changes from FX movement:
- "Your SGD holdings are worth $2,000 less in USD terms, but unchanged in SGD — purely FX movement."
- Show both local-currency and base-currency changes

## Currency Patterns

| Pattern | Handling |
|---------|---------|
| Single currency | No conversion needed |
| Dual currency (e.g., USD + BTC) | Show both, convert to base |
| Multi-currency (3+) | Group by currency, then show consolidated |
| Crypto (BTC, ETH) | Treat as currency, prices from web search or API |

## Edge Cases

- **Rate fetch fails:** Use last cached rate, note "using rate from [date]"
- **Base currency not set:** Infer from residency in profile.md, confirm with user
- **Entity currency unknown:** Ask during setup or entity creation
- **Stale rates (>24hr):** Show warning, proceed with available data
