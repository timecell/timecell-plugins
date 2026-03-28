# Custody Audit Workflow

Detailed scoring and output for /tc:custody-audit.

## Six Dimensions

Score each dimension using thresholds from references/custody-formulas.md:

1. **Self-Custody Ratio**: CRITICAL <30%, WARNING 30-50%, SAFE >50%
2. **Key Security (Multi-Sig)**: SAFE 2-of-3+ distinct manufacturers, WARNING single-sig, CRITICAL exchange-only
3. **Backup Completeness**: SAFE serials+fireproof+2 locations, WARNING missing one, CRITICAL none
4. **Recovery Cadence**: SAFE within window, WARNING 1-6mo overdue, CRITICAL >6mo/never
5. **Geographic Distribution**: SAFE 3+ locs 2+ cities, WARNING 2 same city, CRITICAL single
6. **Succession Readiness**: SAFE plan+successor knows, WARNING partial, CRITICAL no plan

**Overall Zone**: any CRITICAL = CRITICAL, 2+ WARNING = WARNING, 1 WARNING = WATCH, all SAFE = SAFE.
**Grade**: SAFE=A, WATCH=B, WARNING=C, CRITICAL=D/F.

## Output Format

Address user by name.

Lead with overall verdict:
- CRITICAL: "Your custody setup has critical gaps."
- WARNING: "Your custody is partially configured — gaps need attention."
- WATCH: "Good foundation, one area to tighten up."
- SAFE: "Your custody posture is strong."

**Custody Scorecard table:**
```
| Dimension | Status | Detail | Zone |
|-----------|--------|--------|------|
```

After table:
- If WARNING/CRITICAL dimensions: Priority Actions (numbered, severity-ordered, specific with numbers)
- For SAFE dimensions: brief acknowledgment of what's working
- Concrete actions: "Move 1.85 BTC from Binance to your Ledger" not "Move more BTC off exchange"

## Output Rules
- Always address user by name
- Lead with verdict — overall custody zone
- 6-dimension scorecard table mandatory
- Zone icons in Zone column only
- CRITICAL: lead with critical dimension, explain risk, give action
- Positive reinforcement for strong dimensions
- Framework attribution: "The sovereign custody framework requires..." not "You should..."
- Concrete actions with specific numbers
- If recovery test overdue: recommend scheduling THIS month
- Tone: security-conscious but not alarmist
- End with clear next step
