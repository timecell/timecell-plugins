# Custody Computation Formulas

Single source of truth for custody posture scoring. Commands reference this file for inline evaluation — no engine scripts needed.

## Six Custody Dimensions

### 1. Self-Custody Ratio
Percentage of BTC in self-custody (cold storage) vs exchange.

| Zone | Self-Custody % | Description |
|------|---------------|-------------|
| SAFE | > 50% | Sovereign floor met |
| WARNING | 30-50% | Below recommended threshold |
| CRITICAL | < 30% | Majority on exchange — counterparty risk |

Exchange risk classification (supplementary):
- < 10% on exchange = low risk
- 10-30% = moderate
- 30-60% = high
- >= 60% = critical

### 2. Multi-Sig / Key Security
| Zone | Setup | Description |
|------|-------|-------------|
| SAFE | 2-of-3+ multisig, distinct device manufacturers | Best practice |
| WARNING | Hardware single-sig | Single point of failure |
| CRITICAL | Exchange-only or no hardware device | No private key control |

### 3. Backup Completeness
| Zone | Requirements | Description |
|------|-------------|-------------|
| SAFE | Serials recorded + fireproof/metal seed + 2+ locations | Full backup |
| WARNING | Missing any one of the above | Partial backup |
| CRITICAL | No seed backup or no documented locations | No backup |

### 4. Recovery Cadence
Based on `last_recovery_test` date and `recovery_cadence_months` (default: 12).

| Zone | Status | Description |
|------|--------|-------------|
| SAFE | Tested within cadence window | On schedule |
| WARNING | Overdue 1-6 months | Needs attention |
| CRITICAL | Overdue >6 months or never tested | Untested backup may not work |

### 5. Geographic Distribution
| Zone | Setup | Description |
|------|-------|-------------|
| SAFE | 3+ locations across 2+ cities | Disaster-resilient |
| WARNING | 2 locations same city, or 1-2 locations | Limited resilience |
| CRITICAL | Single location or none documented | Single point of failure |

### 6. Succession Readiness
| Zone | Status | Description |
|------|--------|-------------|
| SAFE | Digital asset plan + successor knows process | Full readiness |
| WARNING | Partial plan or no formal successor instructions | Gaps in handoff |
| CRITICAL | No plan AND no documentation | Bitcoin unrecoverable on incapacitation |

## Overall Zone Calculation

1. If ANY dimension is CRITICAL -> Overall is CRITICAL
2. If 2+ dimensions are WARNING -> Overall is WARNING
3. If 1 dimension is WARNING and rest are SAFE -> Overall is WATCH
4. If all dimensions are SAFE -> Overall is SAFE

## Grade Mapping

| Overall Zone | Grade |
|-------------|-------|
| SAFE | A |
| WATCH | B |
| WARNING | C |
| CRITICAL | D/F |

## Output Format

```
**Custody Scorecard**
[One sentence summary of overall posture.]

| Dimension | Status | Detail | Zone |
|-----------|--------|--------|------|
```

Zone icons in Zone column only: SAFE, WARNING, CRITICAL.

## Key Constants

- SOVEREIGN_CUSTODY_FLOOR_PCT: 50
- EXCHANGE_LOW_RISK_PCT: 10
- EXCHANGE_MODERATE_PCT: 30
- EXCHANGE_HIGH_PCT: 60
- RECOVERY_CADENCE_DEFAULT_MONTHS: 12
- RECOVERY_WARNING_OVERDUE_MONTHS: 6
- MIN_BACKUP_LOCATIONS: 2
- MIN_GEO_CITIES: 2
- MIN_GEO_LOCATIONS: 3
