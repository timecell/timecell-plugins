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

## INR Formatting

When `primary_currency: INR` or `base_currency: INR`:
- Use `₹` symbol, Lakh/Crore notation: `₹1.6Cr` not `INR 16M`, `₹2.8L/mo` not `INR 280K/mo`
- 1 Lakh = 1,00,000. 1 Crore = 1,00,00,000.
- In tables with mixed currencies, show INR primary with USD equivalent: `₹1.6Cr ($192K)`
- Apply Indian comma grouping: `₹1,23,45,678` not `₹12,345,678`

## Response Style

Read `response_style` from profile.md → CIO Preferences. Default: `dashboard`.
- `dashboard`: Tables for comparisons, structured sections, metrics-first.
- `conversational`: Weave numbers into prose. Example: "Selling 10 BTC would drop your concentration from 58% to 42%."
- `auto`: Conversational by default; switch to dashboard on "show me the numbers", "details", "table".

## Correction Persistence

When the user corrects factual data about holdings, expenses, or goals:
1. Identify source file, run snapshot-before-write, show diff, confirm, write
2. Log to decisions/ with type: `correction`, old_value, new_value
3. An unwritten correction is a bug — never just acknowledge without persisting

## Response Length Guidelines

| Context | Target Length |
|---------|-------------|
| /tc:start | 200-400 words + dashboard artifact |
| /tc:weekly | 200-400 words, narrative only (no dashboard) |
| /tc:monthly | 500-800 words + dashboard artifact |
| /tc:check | 300-500 words + dashboard artifact |
| Freeform questions | Scale to question complexity |

## Mobile / Dispatch Output

When the user is on Cowork Dispatch (phone), output must be scannable on a small screen:

- **Lead with numbers.** Net worth, runway, zone status — first 3 lines.
- **Tables: max 3 columns.** Collapse wider tables into multiple narrow tables or a ranked list.
- **No React artifacts.** Dispatch does not render React. Use markdown text only.
- **Target length: 50-150 words.** Half the desktop target. Cut narrative, keep data + verdict.
- **No horizontal rules or deep heading nesting.** Use bold labels instead of ### headers.
- **Single follow-up.** Offer one next action, not a menu.

Detection: If the conversation context is short (single sentence, no prior turns, no artifact history), assume Dispatch. When uncertain, produce concise output — it reads fine on desktop too.
