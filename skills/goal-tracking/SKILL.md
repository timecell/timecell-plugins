---
name: goal-tracking
description: |
  Track financial goals, measure progress, and assess trajectory. Goals have target
  amounts, deadlines, and current progress. Used by /tc:monthly. Triggers on "goals",
  "am I on track", "goal progress", "financial goals", "targets".
---

# Goal Tracking

## Goal Format

Goals are in profile.md under `## Goals`:

```
## Goals
- **Financial Independence**: $2M by 2030 | Priority: High
  - Current progress: $1.2M (60%)
  - Monthly contribution: $5,000
- **Education Fund**: $200K by 2035 | Priority: Medium
  - Current progress: $45,000 (22.5%)
```

## Workflow

### Step 1: Parse Goals
Each goal has: name, target amount, target date, priority, current progress, monthly contribution (optional).

### Step 2: Compute Trajectory
For each goal:
- Months remaining until target date
- Monthly contribution rate (if specified)
- Projected value: current + (months_remaining x monthly_contribution)
- Growth assumption: 0% (conservative — no market gains assumed)

### Step 3: Assess Status

| Status | Criteria |
|--------|----------|
| Achieved | Current >= target |
| On Track | Projected >= target |
| At Risk | Projected is 80-100% of target |
| Off Track | Projected < 80% of target |

### Step 4: Present

| Goal | Target | Current | Progress | Status | ETA |
|------|--------|---------|----------|--------|-----|
| Financial Independence | $2M by 2030 | $1.2M | 60% | On Track | 2029 |
| Education Fund | $200K by 2035 | $45K | 22% | At Risk | 2037 |

### Step 5: Recommendations
For off-track goals:
- Calculate the gap: "You need $X more per month to stay on track"
- Suggest options: increase contributions, extend timeline, reduce target
- Frame as options, not directives
