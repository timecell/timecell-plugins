# TimeCell Formatting Standards

## Number Formats

| Type | Format | Example |
|------|--------|---------|
| Currency (>= $10K) | $X,XXX,XXX | $1,234,567 |
| Currency (< $10K) | $X,XXX.XX | $1,234.56 |
| Percentage | XX% | 52% |
| BTC amounts | X.XXXX BTC | 2.5000 BTC |
| Months | XX months | 38 months |
| Exchange rates | X.XXXX | 0.7543 |

- Always use comma separators for numbers > 999
- Round percentages to whole numbers in tables
- Show 2 decimal places for small currency values
- Show 4 decimal places for BTC and exchange rates

## Table Standards

- Header row with clear column names
- Right-align numbers
- Bold the totals row: `| **Total** | **$1,234,567** | **100%** |`
- Include status column where applicable (SAFE/WARNING/CRITICAL)
- Use `---` alignment in markdown tables

## Guardrail Status Display

Always use these exact labels — no emoji, no color codes:

| Zone | Label |
|------|-------|
| Immediate action needed | CRITICAL |
| Attention required | WARNING |
| Monitor closely | WATCH |
| Within bounds | SAFE |
| Well above minimum | STRONG |

## Section Structure

Use `---` horizontal rules between major sections. Use `##` and `###` headers for hierarchy.

## Dashboard Artifacts (React)

When generating React dashboard artifacts:
- Clean, professional design
- Consistent color palette: blues for safe, amber for warning, red for critical
- Net worth as the hero number (large, prominent)
- Allocation as horizontal bar chart (not pie — more readable)
- Guardrails as status cards with zone coloring
- Mobile-friendly layout (single column on small screens)
- Self-contained — no external dependencies or data fetches

## Response Length Guidelines

| Context | Target Length |
|---------|-------------|
| /tc:start | 200-400 words + dashboard artifact |
| /tc:weekly | 200-400 words, narrative only (no dashboard) |
| /tc:monthly | 500-800 words + dashboard artifact |
| /tc:check | 300-500 words + dashboard artifact |
| Freeform questions | Scale to question complexity |
