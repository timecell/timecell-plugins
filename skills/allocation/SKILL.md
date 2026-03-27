---
name: allocation
description: |
  Analyze asset allocation across the portfolio. Calculate concentration by asset class
  and entity. Flag over-concentration. Used by /tc:start and /tc:check. Triggers on
  "allocation", "concentration", "diversification", "portfolio breakdown", "how am I allocated".
---

# Allocation Analysis

## Workflow

### Step 1: Compute Allocation
Using net worth data (load `net-worth` skill if needed):
- Percentage per asset class
- Percentage per individual entity
- Percentage per currency

### Step 2: Check Concentration
Reference the `guardrails` skill for thresholds. Key checks:

| Check | Threshold | Zone |
|-------|-----------|------|
| Single asset class > 50% | 50% | WARNING |
| Single asset class > 70% | 70% | CRITICAL |
| Single entity > 30% | 30% | WARNING |
| Single entity > 50% | 50% | CRITICAL |
| Cash < 10% | 10% | WATCH |

### Step 3: Compare to Last Snapshot
If previous snapshot exists:
- Show allocation drift (current vs previous)
- Flag threshold crossings since last check
- Note large swings (> 5% change in any class)

### Step 4: Present

| Asset Class | Value | Allocation | Status |
|-------------|-------|------------|--------|
| Equities | $XXX,XXX | XX% | SAFE |
| Bitcoin | $XXX,XXX | XX% | WARNING |
| Cash | $XX,XXX | X% | WATCH |
| ... | ... | ... | ... |

## Rules
- Always compute from current entity data, never from cached percentages
- Round percentages to whole numbers in tables
- Percentages must sum to 100% (adjust rounding on largest position)
- "Unmapped" assets are a signal — surface as config opportunity (Design Rule #4)
