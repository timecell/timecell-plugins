# MF Category Classification — SEBI to TimeCell Mapping

> Reference for classifying mutual fund schemes by SEBI category. Used by mf-review command for allocation analysis and underperformer detection.

Last verified: March 2026 (SEBI circular SEBI/HO/IMD/IMD-II DOF3/P/CIR/2024/192)

## SEBI 4-Tier Classification

### Tier 1: Equity

| SEBI Category | Cap Size | TimeCell Tag |
|---------------|----------|-------------|
| Large Cap | large | equity-largecap |
| Large & Mid Cap | large-mid | equity-largemidcap |
| Mid Cap | mid | equity-midcap |
| Small Cap | small | equity-smallcap |
| Multi Cap | multi | equity-multicap |
| Flexi Cap | flexi | equity-flexicap |
| Focused Fund | varies | equity-focused |
| Value Fund | varies | equity-value |
| Contra Fund | varies | equity-contra |
| Dividend Yield | varies | equity-divyield |
| ELSS (Tax Saving) | varies | equity-elss |
| Sectoral / Thematic | sector | equity-sectoral |

**Cap size sub-tags** (for CIO narrative):
- Large cap: top 100 by market cap
- Mid cap: 101-250
- Small cap: 251+
- Multi cap: minimum 25% each in large/mid/small
- Flexi cap: no minimum allocation constraint

**Sectoral/Thematic notes:**
- Sector funds: single sector (banking, pharma, IT, infra)
- Thematic funds: broader theme (consumption, manufacturing, ESG)
- Higher concentration risk — flag if >15% of MF portfolio

### Tier 2: Debt

| SEBI Category | Duration/Credit | TimeCell Tag |
|---------------|----------------|-------------|
| Overnight | 1 day | debt-overnight |
| Liquid | up to 91 days | debt-liquid |
| Ultra Short Duration | 3-6 months | debt-ultrashort |
| Low Duration | 6-12 months | debt-lowduration |
| Money Market | up to 1 year | debt-moneymarket |
| Short Duration | 1-3 years | debt-shortduration |
| Medium Duration | 3-4 years | debt-mediumduration |
| Medium to Long Duration | 4-7 years | debt-medlongduration |
| Long Duration | 7+ years | debt-longduration |
| Dynamic Bond | varies | debt-dynamic |
| Corporate Bond | AA+ min | debt-corpbond |
| Credit Risk | AA and below | debt-creditrisk |
| Banking & PSU | bank/psu only | debt-bankpsu |
| Gilt | govt securities | debt-gilt |
| Gilt 10Y Constant | 10Y maturity | debt-gilt10y |
| Floater | floating rate | debt-floater |

### Tier 3: Hybrid

| SEBI Category | Equity Range | TimeCell Tag |
|---------------|-------------|-------------|
| Conservative Hybrid | 10-25% equity | hybrid-conservative |
| Balanced Hybrid | 40-60% equity | hybrid-balanced |
| Aggressive Hybrid | 65-80% equity | hybrid-aggressive |
| Dynamic Asset Allocation (BAF) | 0-100% equity | hybrid-dynamic |
| Multi Asset Allocation | min 3 asset classes | hybrid-multiasset |
| Arbitrage | arbitrage + equity | hybrid-arbitrage |
| Equity Savings | equity + debt + arb | hybrid-equitysavings |

### Tier 4: Other

| SEBI Category | Type | TimeCell Tag |
|---------------|------|-------------|
| Index Fund | passive equity | other-index |
| ETF | exchange traded | other-etf |
| Fund of Funds (Domestic) | domestic FoF | other-fof-domestic |
| Fund of Funds (Overseas) | international FoF | other-fof-overseas |

## Classification Rules

1. **Primary source:** AMFI scheme category from mfapi.in metadata
2. **Fallback:** Parse scheme name for keywords (Large Cap, ELSS, Liquid, etc.)
3. **Override:** If profile explicitly tags a scheme, use profile tag
4. **Unknown:** If classification fails, tag as `unclassified` and flag for manual review

## Research Mandate

When SEBI issues new categorization circulars (typically annual):
- Review all scheme-to-tier mappings
- Update category median TERs in mf-computation-formulas.md
- Check for new categories or merged categories
- Update "last verified" date at top of this file
