# MF Computation Formulas — Single Source of Truth

> Read this file when computing XIRR, SIP returns, CAGR, underperformer detection, or expense ratio flags. All math is performed inline by the LLM — no external engine.

## XIRR — Extended Internal Rate of Return

Newton-Raphson iteration to find the annualized rate `r` where NPV of cash flows = 0.

### Cash Flow Convention
- Negative = money out (SIP installment, lump sum purchase)
- Positive = money in (redemption, dividend, current valuation)
- Last entry: current market value as positive (valuation date)

### Algorithm

    day_fracs[i] = (date[i] - date[0]).days / 365.0
    NPV(r) = SUM( amount[i] / (1 + r)^day_fracs[i] )
    NPV'(r) = SUM( -day_fracs[i] * amount[i] / (1 + r)^(day_fracs[i] + 1) )

    Initial guess: r = 0.10
    Iterate: r_new = r - NPV(r) / NPV'(r)
    Convergence: |r_new - r| < 1e-7
    Max iterations: 100
    Guard: clamp r to [-0.999, 100]

### Bisection Fallback
If Newton-Raphson diverges (derivative too small), use bisection on [-0.99, 10.0]:

    mid = (lo + hi) / 2
    If NPV(mid) * NPV(lo) < 0: hi = mid, else: lo = mid
    Stop when |NPV(mid)| < 1e-7 or interval < 1e-7

### SIP Cash Flow Construction
For a monthly SIP of amount `A` starting on `start_date`:
- Each installment: {date: start_date + N months, amount: -A}
- Final entry: {date: today, amount: +current_value}
- Monthly dates: same day each month (adjust for month-end)

## Absolute Return

    absolute_return_pct = (current_value - invested_amount) / invested_amount * 100

## CAGR (Compound Annual Growth Rate)

    cagr_pct = ((current_value / invested_amount) ^ (365 / holding_days) - 1) * 100

Use CAGR for lump sum investments. Use XIRR for SIP investments (accounts for irregular cash flows).

## Underperformer Detection

A scheme is flagged as underperformer when:

    scheme_1Y_return - sebi_category_avg_1Y_return < UNDERPERFORMER_THRESHOLD

Where `UNDERPERFORMER_THRESHOLD = -2.0` (percentage points).

Assessment:
- **Mild underperformer:** delta between -2% and -5%
- **Significant underperformer:** delta between -5% and -10%
- **Severe underperformer:** delta worse than -10%

Category averages sourced from AMFI data or Value Research benchmarks.

## Expense Ratio Flags

Flag schemes where TER exceeds category median by more than the threshold:

    flag_if: scheme_ter > category_median_ter + EXPENSE_RATIO_BUFFER

Where `EXPENSE_RATIO_BUFFER = 0.50` (50 basis points).

### Category Median TERs (Direct Plans, as of March 2026)

| Category | Median TER |
|----------|-----------|
| Equity (active) | 0.80% |
| Equity (index/ETF) | 0.20% |
| Debt | 0.40% |
| Hybrid | 0.60% |
| Other (FoF, international) | 0.50% |

## ELSS Lock-in

Each SIP installment has its own 3-year lock-in:

    unlock_date = purchase_date + 3 years (1095 days)

For ELSS lock-in matrix:
- List each installment with purchase_date, amount, unlock_date
- Group by: locked (unlock_date > today) vs unlocked
- Total locked amount and next unlock date

## Direct vs Regular Savings Estimate

    annual_savings = invested_amount * (regular_ter - direct_ter)

Typical regular-to-direct TER difference: 0.50% to 1.00% for equity funds.

## Key Constants

    UNDERPERFORMER_THRESHOLD = -2.0      # percentage points below category avg
    EXPENSE_RATIO_BUFFER = 0.50          # percentage points above category median
    XIRR_INITIAL_GUESS = 0.10            # 10% starting point
    XIRR_TOLERANCE = 1e-7                # convergence threshold
    XIRR_MAX_ITERATIONS = 100            # Newton-Raphson cap
    XIRR_BISECTION_LO = -0.99           # bisection lower bound
    XIRR_BISECTION_HI = 10.0            # bisection upper bound
    NAV_STALE_THRESHOLD_HOURS = 72       # 3 days (weekends/holidays)
    ELSS_LOCK_IN_DAYS = 1095             # 3 years
    CATEGORY_MEDIAN_TER_EQUITY = 0.80
    CATEGORY_MEDIAN_TER_INDEX = 0.20
    CATEGORY_MEDIAN_TER_DEBT = 0.40
    CATEGORY_MEDIAN_TER_HYBRID = 0.60
    CATEGORY_MEDIAN_TER_OTHER = 0.50
