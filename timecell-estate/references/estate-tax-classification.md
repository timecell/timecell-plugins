# US Estate Tax Classification (NRNC)

Deterministic classification rules for US estate tax situs. Used by estate-check to evaluate US estate tax exposure for Non-Resident Non-Citizens (NRNC).

## Core Rule

- NRNC exemption: $60,000 (NOT the ~$13.6M US-citizen exemption)
- Tax rate: 40% on exposure above exemption
- Estimated tax: (total_exposed - 60000) * 0.40

## Applicability

Only evaluate if ALL conditions met:
1. Nationality is NOT US citizen
2. User does NOT hold a US green card
3. User holds US-situs assets

If any condition fails, skip US estate tax section entirely.

## Classification Priority

Evaluate each holding in this order (first match wins):

### 1. Asset Class Overrides
- **Treasuries**: SAFE — portfolio-interest exemption IRC 2105(b)(3). US Treasury bonds are NOT US-situs for NRNC.
- **Bitcoin** (non-US custody): SAFE — not US-sited per current IRS guidance. Regardless of where wallet is custodied.
- **Bitcoin** (US exchange custody): Flag for review — custodial location may create situs exposure.

### 2. Ticker Lookup

**US-SITUS tickers** (27 — US-listed ETFs/stocks, IRC 2104(a)):
```
VOO, VTI, VEA, VWO, VXUS, SPY, IVV, QQQ, GLD, SLV,
IBIT, FBTC, ARKK, XLF, XLE, EEM, EFA, AGG, BND, DIA,
IWM, IWF, IWD, SCHB, SCHX, VUG, VYM
```

**UCITS-SAFE tickers** (14 — Irish/Luxembourg-domiciled, not US-situs):
```
VUSA, VUSD, V500, VWRL, VWCE, CSPX, SWDA, IWDA,
IUSA, IEEM, EIMI, XSPX, XDWD, AGGG
```

### 3. Direct UCITS Equivalents

| US-Situs | UCITS Alternative |
|----------|-------------------|
| VOO | VUSA, VUSD |
| SPY | CSPX, IUSA |
| QQQ | EQQQ |
| IBIT | None (use cold storage for BTC) |

### 4. ISIN Prefix Heuristic
If no ticker match:
- Prefix `IE` or `LU` = UCITS-safe (Irish/Luxembourg domicile)
- Prefix `US` = US-situs (US-domiciled security)
- Other prefix = UNCLASSIFIED

### 5. Default
UNCLASSIFIED — manual review needed. Default is NOT us_situs (false negatives safer than false positives).

## Exposure Zones

| Zone | Total US-Situs Exposure | Action |
|------|------------------------|--------|
| SAFE | <= $60,000 | Within NRNC exemption |
| WARNING | $60,001 - $500,000 | Above exemption — consult cross-border estate attorney |
| CRITICAL | > $500,000 | Significant tax liability — restructuring recommended |

## Treaty Countries (pro-rata unified credit)

```
UK, Japan, Germany, France, Netherlands, Denmark, Finland,
Austria, Ireland, Italy, Australia
```

Treaty countries may have higher effective exemptions via pro-rata unified credit.

## Non-Treaty Countries

```
Singapore, India, UAE, Hong Kong
```

These countries have NO US estate tax treaty — the $60K exemption is the hard ceiling.

## BVI/Cayman Advisory

Holdings through BVI or Cayman structures: consult specialist — look-through rules may apply depending on structure type. Do not auto-classify.

## Acknowledgment Decay

Estate tax acknowledgment expires after:
- 24 months since last review, OR
- Portfolio change > 25% (new US-situs holdings added)

When expired, re-evaluate and present findings fresh.

## Key Constants

- NRNC_EXEMPTION_USD: 60000
- TAX_RATE: 0.40
- SAFE_THRESHOLD_USD: 60000
- WARNING_THRESHOLD_USD: 500000
- ACKNOWLEDGMENT_DECAY_MONTHS: 24
- PORTFOLIO_CHANGE_THRESHOLD_PCT: 25
