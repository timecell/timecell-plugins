#!/usr/bin/env python3
"""
Documents Checker — Deterministic estate document registry engine.

Reads documents/index.md (YAML front matter), evaluates staleness,
computes completeness score, and outputs JSON.

Usage:
    python3 scripts/documents-checker.py load <path>
    python3 scripts/documents-checker.py check <path> [--date YYYY-MM-DD]
    python3 scripts/documents-checker.py score <path> [--date YYYY-MM-DD]

Functions:
    load_registry(path) → list[dict]
    check_staleness(doc, current_date) → 'current'|'stale'|'missing'|'planned'
    score_document(doc, current_date) → 0 or 1
    compute_completeness(docs, current_date) → {score, required_total, zone, details}
"""

import json
import os
import re
import sys
from datetime import date, timedelta

# ---- Constants ----

REQUIRED_TYPES = ['will', 'trust-deed', 'lpa', 'healthcare-directive', 'digital-asset-plan']

VALID_TYPES = {
    # Estate
    'will', 'trust-deed', 'lpa', 'healthcare-directive', 'key-package',
    'digital-asset-plan', 'cpf-nomination', 'insurance', 'tax', 'identity',
    # Insurance
    'insurance-life', 'insurance-health', 'insurance-property', 'insurance-liability',
    # Property
    'property-deed', 'property-title', 'property-valuation',
    # Loans
    'loan-mortgage', 'loan-personal', 'loan-business',
    # Legal
    'legal-partnership', 'legal-shareholder', 'legal-contract',
    # Tax
    'tax-return', 'tax-assessment', 'tax-ruling',
    # Other
    'other',
}

CATEGORY_MAP = {
    # Estate
    'will': 'estate', 'trust-deed': 'estate', 'lpa': 'estate',
    'healthcare-directive': 'estate', 'key-package': 'estate',
    'digital-asset-plan': 'estate', 'cpf-nomination': 'estate',
    'insurance': 'estate', 'tax': 'estate', 'identity': 'estate',
    # Insurance
    'insurance-life': 'insurance', 'insurance-health': 'insurance',
    'insurance-property': 'insurance', 'insurance-liability': 'insurance',
    # Property
    'property-deed': 'property', 'property-title': 'property',
    'property-valuation': 'property',
    # Loans
    'loan-mortgage': 'loans', 'loan-personal': 'loans', 'loan-business': 'loans',
    # Legal
    'legal-partnership': 'legal', 'legal-shareholder': 'legal',
    'legal-contract': 'legal',
    # Tax
    'tax-return': 'tax', 'tax-assessment': 'tax', 'tax-ruling': 'tax',
    # Other
    'other': 'other',
}

CATEGORY_ORDER = ['estate', 'insurance', 'property', 'loans', 'legal', 'tax', 'other']

# Days-based staleness thresholds (type-specific per PRD D3)
STALENESS_THRESHOLDS = {
    'key-package': 365,           # 1 year — operational
    'digital-asset-plan': 365,    # 1 year — operational
    'cpf-nomination': 1095,       # 3 years
    'identity': 365,              # 1 year
    # Insurance
    'insurance-life': 365, 'insurance-health': 365,
    'insurance-property': 365, 'insurance-liability': 365,
    'insurance': 1825,            # legacy estate type
    # Property
    'property-deed': 3650, 'property-title': 3650,
    'property-valuation': 1095,
    # Loans
    'loan-mortgage': 365, 'loan-personal': 365, 'loan-business': 365,
    # Legal
    'legal-partnership': 1095, 'legal-shareholder': 1095, 'legal-contract': 1095,
    # Tax
    'tax-return': 365, 'tax-assessment': 365, 'tax-ruling': 1825,
    'tax': 365,                   # legacy estate type
    # Other
    'other': 1095,                # 3 years default
    'default': 1825,              # 5 years — legal docs (will, trust-deed, lpa, healthcare-directive)
}


def load_registry(path):
    """Load documents from a YAML-in-markdown registry file.

    Returns list of document dicts. Returns [] if file missing or empty.
    """
    if not os.path.exists(path):
        return []

    with open(path, 'r') as f:
        content = f.read()

    if not content.strip():
        return []

    # Extract YAML front matter between --- delimiters
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return []

    yaml_text = match.group(1)

    # Parse YAML manually (avoid external dependency)
    documents = _parse_yaml_documents(yaml_text)
    return documents


def _parse_yaml_documents(yaml_text):
    """Parse the documents list from YAML text without PyYAML dependency."""
    documents = []
    current_doc = None
    current_storage = None
    in_documents = False

    for line in yaml_text.split('\n'):
        stripped = line.strip()

        if stripped == 'documents:':
            in_documents = True
            continue

        if not in_documents:
            continue

        # New document entry
        if stripped.startswith('- id:'):
            if current_doc is not None:
                if current_storage:
                    current_doc['storage'] = current_storage
                documents.append(current_doc)
            current_doc = {'id': _yaml_value(stripped[5:])}
            current_storage = {}
            continue

        if current_doc is None:
            continue

        # Storage block
        if stripped == 'storage:':
            current_storage = {}
            continue

        if stripped.startswith('medium:'):
            if current_storage is not None:
                current_storage['medium'] = _yaml_value(stripped[7:])
            continue

        if stripped.startswith('location:'):
            if current_storage is not None:
                current_storage['location'] = _yaml_value(stripped[9:])
            continue

        if stripped.startswith('url:'):
            if current_storage is not None:
                current_storage['url'] = _yaml_value(stripped[4:])
            continue

        if stripped.startswith('path:'):
            if current_storage is not None:
                current_storage['path'] = _yaml_value(stripped[5:])
            continue

        # Top-level document fields
        if stripped.startswith('type:'):
            current_doc['type'] = _yaml_value(stripped[5:])
        elif stripped.startswith('title:'):
            current_doc['title'] = _yaml_value(stripped[6:])
        elif stripped.startswith('last_updated:'):
            val = _yaml_value(stripped[13:])
            current_doc['last_updated'] = val if val and val != 'null' else None
        elif stripped.startswith('next_review:'):
            val = _yaml_value(stripped[12:])
            current_doc['next_review'] = val if val and val != 'null' else None
        elif stripped.startswith('notes:'):
            current_doc['notes'] = _yaml_value(stripped[6:])
        elif stripped.startswith('review_interval:'):
            current_doc['review_interval'] = _yaml_value(stripped[16:])
        elif stripped.startswith('stale_threshold_years:'):
            current_doc['stale_threshold_years'] = _yaml_value(stripped[22:])
        elif stripped.startswith('expiry_date:'):
            val = _yaml_value(stripped[12:])
            current_doc['expiry_date'] = val if val and val != 'null' else None
        elif stripped.startswith('renewal_date:'):
            val = _yaml_value(stripped[13:])
            current_doc['renewal_date'] = val if val and val != 'null' else None
        elif stripped.startswith('maturity_date:'):
            val = _yaml_value(stripped[14:])
            current_doc['maturity_date'] = val if val and val != 'null' else None
        elif stripped.startswith('policy_number:'):
            current_doc['policy_number'] = _yaml_value(stripped[14:])
        elif stripped.startswith('insurer:'):
            current_doc['insurer'] = _yaml_value(stripped[8:])
        elif stripped.startswith('coverage_amount:'):
            current_doc['coverage_amount'] = _yaml_value(stripped[16:])
        elif stripped.startswith('property_address:'):
            current_doc['property_address'] = _yaml_value(stripped[17:])
        elif stripped.startswith('lender:'):
            current_doc['lender'] = _yaml_value(stripped[7:])
        elif stripped.startswith('amount:'):
            current_doc['amount'] = _yaml_value(stripped[7:])
        elif stripped.startswith('counterparty:'):
            current_doc['counterparty'] = _yaml_value(stripped[13:])
        elif stripped.startswith('fiscal_year:'):
            current_doc['fiscal_year'] = _yaml_value(stripped[12:])
        elif stripped.startswith('filing_status:'):
            current_doc['filing_status'] = _yaml_value(stripped[14:])
        elif stripped.startswith('category:'):
            current_doc['category'] = _yaml_value(stripped[9:])

    # Don't forget last document
    if current_doc is not None:
        if current_storage:
            current_doc['storage'] = current_storage
        documents.append(current_doc)

    return documents


def _yaml_value(raw):
    """Extract a YAML value — strip quotes and whitespace."""
    val = raw.strip()
    if val == 'null' or val == '~' or val == '':
        return None
    # Remove surrounding quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    return val


def get_staleness_threshold_days(doc):
    """Get the staleness threshold in days for a document.

    Priority: per-doc review_interval > per-doc stale_threshold_years > type default > global default.
    """
    # Per-doc override via review_interval (in days)
    if doc.get('review_interval'):
        try:
            return int(doc['review_interval'])
        except (ValueError, TypeError):
            pass

    # Per-doc override via stale_threshold_years
    if doc.get('stale_threshold_years'):
        try:
            return int(float(doc['stale_threshold_years']) * 365)
        except (ValueError, TypeError):
            pass

    doc_type = doc.get('type', 'other')
    return STALENESS_THRESHOLDS.get(doc_type, STALENESS_THRESHOLDS['default'])


def check_staleness(doc, current_date=None):
    """Determine document status: 'current', 'stale', 'missing', or 'planned'.

    Per PRD:
    - planned (medium=planned) → 'planned'
    - last_updated is None → 'missing'
    - age > threshold → 'stale'
    - else → 'current'
    """
    if current_date is None:
        current_date = date.today()

    storage = doc.get('storage', {})
    medium = storage.get('medium', '')

    if medium == 'planned':
        return 'planned'

    last_updated = doc.get('last_updated')
    if last_updated is None:
        return 'missing'

    try:
        updated_date = date.fromisoformat(str(last_updated))
    except (ValueError, TypeError):
        return 'missing'

    threshold_days = get_staleness_threshold_days(doc)
    days_old = (current_date - updated_date).days

    if days_old > threshold_days:
        return 'stale'

    return 'current'


def years_since(last_updated_str, current_date=None):
    """Calculate years since a date string. Returns float or None."""
    if current_date is None:
        current_date = date.today()
    if not last_updated_str:
        return None
    try:
        updated_date = date.fromisoformat(str(last_updated_str))
        return round((current_date - updated_date).days / 365.25, 1)
    except (ValueError, TypeError):
        return None


def get_category(doc):
    """Get the category for a document.

    Priority: explicit category field > CATEGORY_MAP lookup > 'other'.
    """
    if doc.get('category'):
        return doc['category']
    doc_type = doc.get('type', 'other')
    return CATEGORY_MAP.get(doc_type, 'other')


def check_expiry(doc, current_date=None):
    """Check if a document has an expiry date and its status.

    Returns dict with: has_expiry, expiry_date, days_until, alert_level.
    alert_level: 'expired' | 'critical' | 'warning' | 'ok' | None
    """
    if current_date is None:
        current_date = date.today()

    expiry_str = doc.get('expiry_date') or doc.get('renewal_date') or doc.get('maturity_date')
    if not expiry_str:
        return {'has_expiry': False, 'expiry_date': None, 'days_until': None, 'alert_level': None}

    try:
        expiry_date = date.fromisoformat(str(expiry_str))
    except (ValueError, TypeError):
        return {'has_expiry': False, 'expiry_date': None, 'days_until': None, 'alert_level': None}

    days_until = (expiry_date - current_date).days

    if days_until < 0:
        alert_level = 'expired'
    elif days_until <= 30:
        alert_level = 'critical'
    elif days_until <= 90:
        alert_level = 'warning'
    else:
        alert_level = 'ok'

    return {
        'has_expiry': True,
        'expiry_date': str(expiry_date),
        'days_until': days_until,
        'alert_level': alert_level,
    }


def get_expiry_alert(doc, current_date=None):
    """Get a human-readable expiry alert string for a document.

    Returns None if no alert needed.
    """
    expiry = check_expiry(doc, current_date)
    if not expiry['has_expiry']:
        return None

    days = expiry['days_until']
    if expiry['alert_level'] == 'expired':
        return f"EXPIRED ({abs(days)} days ago)"
    elif expiry['alert_level'] == 'critical':
        return f"Expiring in {days} days"
    elif expiry['alert_level'] == 'warning':
        return f"Expiring in {days} days"
    return None


def score_document(doc, current_date=None):
    """Score a document: 0 (planned/missing) or 1 (current/stale).

    Per PRD D2: planned = 0 (counts as missing).
    Per PRD D4: stale = 1 (present, shown as warning).
    """
    status = check_staleness(doc, current_date)
    if status in ('current', 'stale'):
        return 1
    return 0


def compute_completeness(docs, current_date=None):
    """Compute estate completeness score.

    Returns dict with:
        score: number of required types that are current or stale
        required_total: total required types (5)
        missing: list of missing required type names
        stale: list of stale required type names
        planned: list of planned required type names
        zone: 'CRITICAL' | 'WARNING' | 'SAFE'
        details: per-type status breakdown
    """
    if current_date is None:
        current_date = date.today()

    # Build type → best status mapping (a type can have multiple docs)
    type_status = {}
    type_docs = {}
    for doc in docs:
        doc_type = doc.get('type', 'other')
        status = check_staleness(doc, current_date)

        # Keep best status per type: current > stale > planned > missing
        priority = {'current': 3, 'stale': 2, 'planned': 1, 'missing': 0}
        existing = type_status.get(doc_type)
        if existing is None or priority.get(status, 0) > priority.get(existing, 0):
            type_status[doc_type] = status
            type_docs[doc_type] = doc

    # Evaluate each required type
    score = 0
    missing_types = []
    stale_types = []
    planned_types = []
    details = {}

    for req_type in REQUIRED_TYPES:
        status = type_status.get(req_type)
        doc = type_docs.get(req_type)

        if status is None:
            # Type not in registry at all
            details[req_type] = {'status': 'missing', 'title': None, 'years_old': None}
            missing_types.append(req_type)
        elif status == 'current':
            score += 1
            title = doc.get('title', req_type) if doc else req_type
            details[req_type] = {'status': 'current', 'title': title, 'years_old': None}
        elif status == 'stale':
            score += 1  # PRD D4: stale counts as present
            title = doc.get('title', req_type) if doc else req_type
            yrs = years_since(doc.get('last_updated'), current_date) if doc else None
            details[req_type] = {'status': 'stale', 'title': title, 'years_old': yrs}
            stale_types.append(req_type)
        elif status == 'planned':
            # PRD D2: planned = 0
            details[req_type] = {'status': 'planned', 'title': doc.get('title', req_type) if doc else req_type, 'years_old': None}
            planned_types.append(req_type)
        else:
            details[req_type] = {'status': 'missing', 'title': None, 'years_old': None}
            missing_types.append(req_type)

    required_total = len(REQUIRED_TYPES)

    # Zone calculation
    if score == required_total and len(stale_types) == 0:
        zone = 'SAFE'
    elif score >= required_total:
        zone = 'WARNING'  # All present but some stale
    elif score >= required_total - 1:
        zone = 'WARNING'
    else:
        zone = 'CRITICAL'

    return {
        'score': score,
        'required_total': required_total,
        'missing': missing_types,
        'stale': stale_types,
        'planned': planned_types,
        'zone': zone,
        'details': details,
    }


def format_check_output(docs, current_date=None):
    """Format the /check Step 5b estate completeness output.

    Returns a dict with 'table' (list of {type, display_name, status_text}) and 'summary'.
    """
    if current_date is None:
        current_date = date.today()

    completeness = compute_completeness(docs, current_date)

    display_names = {
        'will': 'Will',
        'trust-deed': 'Trust Deed',
        'lpa': 'LPA',
        'healthcare-directive': 'Healthcare Directive',
        'digital-asset-plan': 'Digital Asset Plan',
        'key-package': 'Key Package',
        'cpf-nomination': 'CPF Nomination',
    }

    # Build table rows for all types found in docs + required types
    all_types = list(REQUIRED_TYPES)
    # Add non-required types that exist in the registry
    for doc in docs:
        dt = doc.get('type', 'other')
        if dt not in all_types:
            all_types.append(dt)

    table = []
    for dtype in all_types:
        detail = completeness['details'].get(dtype)
        display = display_names.get(dtype, dtype.replace('-', ' ').title())

        if detail is None:
            # Non-required type that exists in registry
            # Find the doc and check its status
            for doc in docs:
                if doc.get('type') == dtype:
                    status = check_staleness(doc, current_date)
                    title = doc.get('title', dtype)
                    if status == 'current':
                        status_text = f'✅ Done ({title})'
                    elif status == 'stale':
                        yrs = years_since(doc.get('last_updated'), current_date)
                        status_text = f'⚠️ Review for currency ({yrs} yrs old)'
                    elif status == 'planned':
                        status_text = '📋 Planned — not yet created'
                    else:
                        status_text = '❓ Unknown'
                    table.append({'type': dtype, 'display_name': display, 'status_text': status_text})
                    break
        elif detail['status'] == 'current':
            table.append({'type': dtype, 'display_name': display, 'status_text': f"✅ Done ({detail['title']})"})
        elif detail['status'] == 'stale':
            yrs = detail['years_old']
            table.append({'type': dtype, 'display_name': display, 'status_text': f"⚠️ Review for currency ({yrs} yrs old)"})
        elif detail['status'] == 'planned':
            table.append({'type': dtype, 'display_name': display, 'status_text': '📋 Planned — not yet created'})
        elif detail['status'] == 'missing':
            table.append({'type': dtype, 'display_name': display, 'status_text': '❓ Unknown'})

    summary = f"{completeness['score']} of {completeness['required_total']} required types fully current"

    return {
        'table': table,
        'summary': summary,
        'zone': completeness['zone'],
        'score': completeness['score'],
        'required_total': completeness['required_total'],
        'missing': completeness['missing'],
        'stale': completeness['stale'],
        'planned': completeness['planned'],
    }


# ---- CLI interface ----

def main():
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Usage: documents-checker.py <command> <path> [--date YYYY-MM-DD]'}))
        sys.exit(1)

    command = sys.argv[1]
    path = sys.argv[2]

    # Parse optional --date flag
    current_date = date.today()
    if '--date' in sys.argv:
        idx = sys.argv.index('--date')
        if idx + 1 < len(sys.argv):
            current_date = date.fromisoformat(sys.argv[idx + 1])

    docs = load_registry(path)

    if command == 'load':
        print(json.dumps({'documents': docs, 'count': len(docs)}, indent=2, default=str))

    elif command == 'check':
        results = []
        for doc in docs:
            status = check_staleness(doc, current_date)
            yrs = years_since(doc.get('last_updated'), current_date)
            threshold_days = get_staleness_threshold_days(doc)
            results.append({
                'id': doc.get('id'),
                'type': doc.get('type'),
                'title': doc.get('title'),
                'status': status,
                'years_old': yrs,
                'threshold_days': threshold_days,
                'score': score_document(doc, current_date),
            })
        print(json.dumps({'documents': results, 'date': str(current_date)}, indent=2))

    elif command == 'score':
        result = format_check_output(docs, current_date)
        print(json.dumps(result, indent=2, default=str))

    elif command == 'expiring':
        results = []
        for doc in docs:
            expiry = check_expiry(doc, current_date)
            if expiry['has_expiry'] and expiry['alert_level'] in ('expired', 'critical', 'warning'):
                alert_text = get_expiry_alert(doc, current_date)
                results.append({
                    'id': doc.get('id'),
                    'type': doc.get('type'),
                    'title': doc.get('title'),
                    'category': get_category(doc),
                    'expiry_date': expiry['expiry_date'],
                    'days_until': expiry['days_until'],
                    'alert_level': expiry['alert_level'],
                    'alert_text': alert_text,
                })
        print(json.dumps({'expiring': results, 'count': len(results), 'date': str(current_date)}, indent=2))

    elif command == 'categories':
        grouped = {}
        for doc in docs:
            cat = get_category(doc)
            if cat not in grouped:
                grouped[cat] = []
            status = check_staleness(doc, current_date)
            expiry = check_expiry(doc, current_date)
            grouped[cat].append({
                'id': doc.get('id'),
                'type': doc.get('type'),
                'title': doc.get('title'),
                'status': status,
                'expiry': expiry if expiry['has_expiry'] else None,
            })
        # Order categories
        ordered = {}
        for cat in CATEGORY_ORDER:
            if cat in grouped:
                ordered[cat] = grouped[cat]
        # Add any unexpected categories
        for cat in grouped:
            if cat not in ordered:
                ordered[cat] = grouped[cat]
        categories_present = list(ordered.keys())
        multi_category = len(categories_present) > 1 or (len(categories_present) == 1 and categories_present[0] != 'estate')
        print(json.dumps({
            'categories': ordered,
            'category_order': categories_present,
            'multi_category': multi_category,
            'date': str(current_date),
        }, indent=2, default=str))

    elif command == 'validate-type':
        if len(sys.argv) >= 4:
            doc_type = sys.argv[3]
            valid = doc_type in VALID_TYPES
            print(json.dumps({'type': doc_type, 'valid': valid, 'valid_types': sorted(VALID_TYPES)}))
        else:
            print(json.dumps({'error': 'Usage: documents-checker.py validate-type <type>'}))

    else:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()
