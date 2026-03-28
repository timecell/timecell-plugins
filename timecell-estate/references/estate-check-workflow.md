# Estate Check Workflow

Detailed evaluation and output for /tc:estate-check.

## Five Dimensions

Score each applicable dimension as GREEN, AMBER, or RED using thresholds from references/estate-formulas.md.

**Dimension 1 — Legal Documents:** Check will, trust deed, LPA, beneficiary designations against existence and freshness. Will missing + dependents = RED CRITICAL. Will missing + BTC >$1M = RED.

**Dimension 2 — BTC Succession:** Only if crypto holdings exist. Check key package age (<2 years), digital asset plan, heir briefed status, recovery tested. Key package missing + BTC >$500K = RED.

**Dimension 3 — US Estate Tax:** Only for NRNC (non-US citizen, no green card) with US-situs assets. Classify each holding using the ticker lists and ISIN heuristic from references/estate-tax-classification.md. Calculate total exposure. Zones: SAFE <=60K, WARNING 60K-500K, CRITICAL >500K. All classification is deterministic string matching — exact ticker lookup against the 27 US-situs and 14 UCITS-safe lists, then ISIN prefix, then UNCLASSIFIED default.

**Dimension 4 — Trust Branch:** Only if trust deed exists. Check BTC in trust name, trustee succession, protector.

**Dimension 5 — Insurance Adequacy:** Life cover >= 5x annual burn. No data = AMBER. No cover + dependents = RED.

**Calculate Grade:** A (all green) through F (will missing + dependents + significant assets) per references/estate-formulas.md.

## Output Format

Address user by name. Respect response_style and communication_density from profile.

1. **Estate Readiness: Grade [X]** — one-sentence summary
2. **Estate Dimensions table:**

```
| Dimension | Status | Detail | Zone |
|-----------|--------|--------|------|
```

Zone icons in Zone column only. Skip non-applicable dimensions with "Not applicable" and reason.

3. **Priority Actions** (if any AMBER/RED): numbered list, RED first, then AMBER, ordered by financial impact within severity. Each action: what to do, why it matters, who can help.

4. **Context notes** (if applicable): active legal engagements, jurisdiction considerations, cross-reference with /tc:check.

If Grade A: be concise, confirm completeness, do not invent gaps.

## Output Rules
- Always address user by name
- Lead with grade and verdict
- Zone icons in Zone column only
- Estate dimensions table for every run
- Never expose internal file paths or reference file names
- Say "my assessment" or "framework guidance" not "engine-bridge" or "beliefs.md"
- Jurisdiction awareness: note jurisdiction-specific considerations where relevant but don't overreach into legal advice
- Tone: structured, professional, empathetic. Estate planning involves mortality — be respectful.
