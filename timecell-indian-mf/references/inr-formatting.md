# INR Formatting Reference

> Rules for displaying Indian Rupee amounts. Used by mf-review and any skill handling INR values.

## Lakh / Crore Notation

| Range | Format | Example |
|-------|--------|---------|
| < Rs 1,00,000 | Whole rupees with commas | Rs 45,000 |
| Rs 1,00,000 to Rs 99,99,999 | X.XX L | Rs 12.50 L |
| Rs 1,00,00,000+ | X.XX Cr | Rs 3.25 Cr |

## Indian Number Grouping

Pattern: XX,XX,XXX (NOT XXX,XXX,XXX)

| Amount | Indian Format | Western Format |
|--------|--------------|----------------|
| 100000 | 1,00,000 | 100,000 |
| 1234567 | 12,34,567 | 1,234,567 |
| 10000000 | 1,00,00,000 | 10,000,000 |
| 123456789 | 12,34,56,789 | 123,456,789 |

Only use Indian grouping when showing full rupee amounts. When using L/Cr notation, show 2 decimal places.

## Decimal Rules

- Amounts >= 1L: show 2 decimals in L/Cr notation (e.g., 1.25 Cr, 12.50 L)
- Amounts < 1L: show whole rupees with Indian comma grouping (e.g., Rs 45,000)
- Percentages in tables: whole numbers (e.g., 12%)
- Percentages in narrative: 2 decimals (e.g., 12.50%)
- NAV values: 4 decimals (e.g., Rs 45.1234)

## Symbol

- Preferred: Rs (e.g., Rs 12.50 L)
- Alternative: INR (for formal/cross-currency contexts)
- Never use the rupee unicode symbol in CLI/terminal output (rendering issues)

## Conversion Reference

    1 Lakh (L) = 1,00,000 = 100 thousand
    1 Crore (Cr) = 1,00,00,000 = 10 million
    100 L = 1 Cr
