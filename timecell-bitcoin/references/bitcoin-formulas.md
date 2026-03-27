# Bitcoin Formulas — Computation Reference

> Read this file when computing BTC temperature, selling rules, DCA multipliers, crash survival, or deployment ladders. All math is performed inline by the LLM — no external engine.

## Temperature Calculation

### MVRV Normalization

    z = (mvrv - MVRV_MEAN) / MVRV_STD

Convert z to CDF using Abramowitz & Stegun polynomial approximation:

    t = 1 / (1 + 0.2316419 * |z|)
    d = 0.3989423 * exp(-z² / 2)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    CDF = if z > 0: 1 - p, else: p
    mvrvScore = CDF * 100

Max approximation error: 1.5e-7.

### RHODL Normalization

    rhodlScore = (log10(rhodl) - log10(RHODL_MIN)) / (log10(RHODL_MAX) - log10(RHODL_MIN)) * 100

Clamp result to 0-100.

### Composite Temperature

    temperature = mvrvScore * 0.6 + rhodlScore * 0.4

### Zone Thresholds

| Zone | Range |
|------|-------|
| COLD | 0-30 |
| COOL | 30-50 |
| NEUTRAL | 50-60 |
| CAUTION | 60-80 |
| GREED | 80-95 |
| EXTREME GREED | 95-100 |

**Fallback:** If `fetch-btc-data.py` returns a pre-computed score (source: "timecell-api"), use it directly. The formula above is for when raw MVRV/RHODL values are provided instead.

## Selling Tier Ladder

Applied to accessible BTC only (entities with `access_tag: liquid`):

| Trigger | % to Sell |
|---------|-----------|
| T >= 70 | 5% |
| T >= 75 | 10% |
| T >= 80 | 15% |
| T >= 85 | 20% |
| T >= 90 | 25% |
| T >= 95 | 25% |

**Floor rule:** Never sell below 50% of original liquid BTC position.

**Oscillation buffer:** Temperature must sustain tier level for 48 hours before triggering. 3-point buffer prevents whipsawing (e.g., T=79 does not trigger T>=80 tier).

## DCA Temperature Multipliers

| Temperature Range | DCA Multiplier |
|-------------------|----------------|
| 0-20 | 2.0x |
| 20-40 | 1.5x |
| 40-60 | 1.0x (baseline) |
| 60-75 | 0.5x |
| 75-100 | 0.0x (pause DCA) |

## Historical Crash Database

| Event | Year | Drawdown | Recovery |
|-------|------|----------|----------|
| Mt. Gox | 2014 | 85.2% | 36 months |
| ICO Bust | 2018 | 84.2% | 36 months |
| LUNA/FTX | 2022 | 77.5% | 25 months |
| COVID | 2020 | 63.3% | 7 months |

**Non-BTC correlation factor:** 0.5 (other assets drop at 50% of BTC drawdown magnitude).

**Survival threshold:** Liquid runway must be >= 18 months at all times.

## Multi-Asset Crash Scenarios

| Scenario | BTC | Stocks | Treasuries | Cash |
|----------|-----|--------|------------|------|
| btc_crash_25 | 0.75 | 1.0 | 0.99 | 1.0 |
| btc_crash_50 | 0.50 | 0.90 | 0.98 | 1.0 |
| btc_crash_75 | 0.25 | 0.80 | 0.97 | 1.0 |
| market_crash_20 | 0.85 | 0.80 | 1.0 | 1.0 |
| market_crash_40 | 0.60 | 0.60 | 0.99 | 1.0 |

**Runway zone classification:**
- CRITICAL: < 6 months
- WARNING: < 12 months
- SAFE: >= 12 months

## Crash Deployment Ladder (Buying Opportunities)

| Drawdown Range | Deploy % of Opportunity Fund |
|----------------|------------------------------|
| 30-40% | 10% |
| 40-50% | 20% |
| 50-60% | 30% |
| 60%+ | 40% |

**Source constraint:** Deploy from opportunity fund ONLY. Never from safety floor or lifestyle fund.

## Key Constants

MVRV_MEAN = 1.73
MVRV_STD = 1.36
RHODL_MIN = 120
RHODL_MAX = 30541
DEFAULT_ANNUAL_GROWTH_RATE = 0.30
DEFAULT_VOLATILITY = 0.60
SURVIVAL_RUNWAY_MONTHS = 18
NON_BTC_CORRELATION = 0.5
CACHE_MAX_AGE_SECONDS = 3600
STALE_THRESHOLD_HOURS = 48
