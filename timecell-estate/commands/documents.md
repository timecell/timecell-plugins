# /documents — Estate Document Registry

Structured registry of estate documents with deterministic status tracking. CRUD operations + completeness scoring.

## Tool Call Budget: 2-3

## Subcommands
- `/documents` or `/documents list` — full registry with status
- `/documents add` — interactive flow to register a new document
- `/documents add <type> <path>` — register a local file directly
- `/documents add <type> --gdrive <fileId-or-URL>` — register GDrive reference
- `/documents update [doc-id]` — update metadata for existing entry
- `/documents list --missing` — gap/planned items only
- `/documents list --stale` — stale items only
- `/documents list --expiring` — documents expiring within 30 days
- `/documents list --category <category>` — filter by category
- `/documents find <query>` — search registry by keyword
- `/documents --open [doc-id]` — open document or show location
- `/documents --summary` — compact completeness score

## Valid Document Types
`will`, `trust-deed`, `lpa`, `healthcare-directive`, `insurance`, `key-package`, `digital-asset-plan`, `cpf-nomination`, `tax`, `identity`, `insurance-life`, `insurance-health`, `insurance-property`, `insurance-liability`, `property-deed`, `property-title`, `property-valuation`, `loan-mortgage`, `loan-personal`, `loan-business`, `legal-partnership`, `legal-shareholder`, `legal-contract`, `tax-return`, `tax-assessment`, `tax-ruling`, `other`

If invalid type provided: reject with valid type list. Suggest closest match if obvious.

## Required Types for Estate Completeness
`will`, `trust-deed`, `lpa`, `healthcare-directive`, `digital-asset-plan`

## Data Model
Registry at `documents/index.md` — YAML front matter (schema: estate-documents-v1).

## Status Logic (Deterministic)

ALL status calculations use the script:
```
python3 scripts/documents-checker.py <command> documents/index.md
```

Available script commands: `load`, `check`, `score`, `expiring`, `categories`, `validate-type`.

Status values: Current, Stale (N yrs), Missing, Planned, Date unknown.

**Scoring rules (locked):**
- Planned = 0 (counts as missing for guardrail)
- Stale = 1 (counts as present, shown with warning)

## Flow: list

### Step 1: Read + Score (single bash)
```bash
cat documents/index.md 2>/dev/null; echo '---SEPARATOR---';
python3 scripts/documents-checker.py score documents/index.md;
echo '---SEPARATOR---';
python3 scripts/documents-checker.py expiring documents/index.md;
echo '---SEPARATOR---';
python3 scripts/documents-checker.py categories documents/index.md
```

If file doesn't exist: "No documents registered yet. Run `/documents add` to register your first document."

### Step 2: Display

Group by category if multi-category. Flat table if estate-only.

```
## Document Registry
Updated: <date>

| # | Document | Type | Location | Last Updated | Status |
```

Footer: estate completeness score + zone, legal disclaimer, available commands.

Expiry alerting in Status column: Expiring in N days, EXPIRED.

## Flow: add

### Direct Flow (type + path provided)
1. **Validate type** — HARD GATE. Must match valid types list exactly. Reject invalid.
2. Determine mode: local (copy file), gdrive (store reference), physical, planned.
3. Identity warning if type=identity and mode=local.
4. Create/update `documents/index.md` YAML entry.
5. Confirm immediately (do NOT ask permission): type, category, location, dates, doc-id.

### Interactive Flow (no args)
Ask: type, name, location, date, notes. Write entry. Confirm.

## Flow: find
Search all fields case-insensitive. If no match: "No documents matching '<query>'. Run `/documents list` to see all registered documents." — STOP. No suggestions after.

## Flow: update
Find by doc-id, ask what to update, show old->new, confirm, recalculate next_review.

## Flow: --open
By doc-id or row number. Local: `open <path>`. GDrive: `open <url>`. Physical: print location. Planned: suggest add.

## Migration from profile.md
On first run, check if profile has `estate_documents:` block. If found, offer import (wait for confirmation). Map: yes->physical, no->planned, partial->physical with note.

## Output Rules
- Status icons in Status column only
- Shortened locations: GDrive -> "Google Drive", physical -> description
- Always show completeness score after table
- Always show legal disclaimer: "This registry tracks document references only. Verify with your legal advisor that all documents are valid and current for your jurisdiction."
- Suggest `/documents add` when missing items displayed
