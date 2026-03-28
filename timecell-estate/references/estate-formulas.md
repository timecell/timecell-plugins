# Estate Computation Formulas

Single source of truth for all estate-related thresholds and computations. Commands reference this file for inline evaluation — no engine scripts needed.

## Estate Staleness (Verification Age)

Date arithmetic: `days_since = (today - key_package_verified_date).days`

| Zone | Days Since Last Check | Display |
|------|----------------------|---------|
| SAFE | < 90 days | "Verified N days ago" |
| WARNING | 90-179 days | "Estate check overdue (N days)" |
| CRITICAL | >= 180 days | "Estate check critically overdue (N days)" |
| UNKNOWN | No date or malformed | "Estate verification date unknown" |

## Estate Completeness

5 required document types for estate completeness guardrail:

1. `will`
2. `trust-deed` (if trust structure exists)
3. `lpa` (Lasting Power of Attorney)
4. `healthcare-directive`
5. `digital-asset-plan`

Scoring: present (current or stale) = 1, planned or missing = 0.

| Zone | Score | Description |
|------|-------|-------------|
| CRITICAL | 0-2 of 5 | Major estate gaps — immediate action needed |
| WARNING | 3-4 of 5 | Partial coverage — gaps require attention |
| SAFE | 5 of 5, none stale | Full coverage, all current |
| WARNING | 5 of 5, some stale | Full coverage but documents need refresh |

## Estate Readiness Grade

| Grade | Criteria |
|-------|----------|
| A | All evaluated dimensions GREEN. No gaps. |
| B | All dimensions GREEN or AMBER. No RED. Minor gaps only. |
| C | One RED dimension. Meaningful gap requiring action. |
| D | Two+ RED dimensions. Significant estate planning gaps. |
| F | Will missing + dependents + significant assets. Immediate action needed. |

Only grade dimensions that are applicable. Skipped dimensions (e.g., US estate tax for US citizens, trust branch with no trust) do not count against the grade.

## Five Estate Dimensions

### 1. Legal Documents
| Document | GREEN | AMBER | RED |
|----------|-------|-------|-----|
| Will | exists | exists but >5 years old | missing |
| Trust Deed | exists | exists but BTC not transferred | missing AND holdings >$500K |
| LPA | exists | -- | missing |
| Beneficiary Designations | aligned with trust/will | partial | missing |

Rules:
- Will missing + dependents = RED with CRITICAL flag
- Will missing + BTC >$1M = RED (intestacy risk)
- Trust deed missing + BTC >$1M = AMBER (probate risk)

### 2. BTC Succession (only if crypto holdings exist)
| Item | GREEN | AMBER | RED |
|------|-------|-------|-----|
| Key Package | exists, created within 2 years | exists but >2 years old | missing |
| Digital Asset Plan | documented | partial | missing |
| Heir Briefed | yes (knows location + attorney) | partial | no |
| Recovery Tested | yes | -- | no or unknown |

Rules:
- Key package missing + BTC >$500K = RED
- Heir not briefed = AMBER (plan exists but fails on execution)

### 3. US Estate Tax (NRNC only — see estate-tax-classification.md)
Only evaluate if nationality is NOT US citizen AND no green card AND holds US-situs assets.

### 4. Trust Branch (only if trust deed exists)
| Item | GREEN | AMBER | RED |
|------|-------|-------|-----|
| BTC in Trust Name | yes | -- | no (defeats trust purpose) |
| Trustee Succession | documented | -- | not documented |
| Protector Named | yes (if required) | not applicable | missing where required |

### 5. Insurance Adequacy
| Item | GREEN | AMBER | RED |
|------|-------|-------|-----|
| Life Insurance | cover >= 5x annual burn AND covers dependents | exists but < 5x burn | no cover AND has dependents |

Rules:
- No insurance data = AMBER ("Insurance status unknown")
- No dependents = lower priority, still note for estate liquidity

## Document Freshness Thresholds

| Type | Threshold |
|------|-----------|
| will, trust-deed, lpa, healthcare-directive | 5 years (1825 days) |
| key-package, digital-asset-plan | 1 year (365 days) |
| cpf-nomination | 3 years (1095 days) |
| identity | 1 year (365 days) |
| insurance-* | 1 year (365 days) |
| property-deed, property-title | 10 years (3650 days) |
| property-valuation | 3 years (1095 days) |
| loan-* | 1 year (365 days) |
| legal-* | 3 years (1095 days) |
| tax-return, tax-assessment | 1 year (365 days) |
| tax-ruling | 5 years (1825 days) |

## Key Constants

- ESTATE_CHECK_WARNING_DAYS: 90
- ESTATE_CHECK_CRITICAL_DAYS: 180
- KEY_PACKAGE_MAX_AGE_YEARS: 2
- WILL_FRESHNESS_YEARS: 5
- INSURANCE_MULTIPLIER: 5 (life cover >= 5x annual burn)
- SIGNIFICANT_ASSETS_THRESHOLD: 500000 (USD)
- HIGH_VALUE_THRESHOLD: 1000000 (USD)
