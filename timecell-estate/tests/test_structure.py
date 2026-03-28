#!/usr/bin/env python3
"""Structural validation tests for timecell-estate add-on plugin."""
import os
import json

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_plugin_json_valid():
    """plugin.json exists, is valid JSON, has correct name/version/dependency."""
    path = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
    assert os.path.exists(path), ".claude-plugin/plugin.json missing"
    with open(path) as f:
        data = json.load(f)
    assert data["name"] == "timecell-estate"
    assert data["version"] == "1.0.0"
    deps = data.get("dependencies", [])
    assert "timecell" in deps, "Missing dependency on timecell core"


def test_command_files_exist():
    """All 4 command files exist and are non-empty."""
    commands = ["estate-check.md", "custody-audit.md", "create-key-package.md", "documents.md"]
    for cmd in commands:
        path = os.path.join(PLUGIN_ROOT, "commands", cmd)
        assert os.path.exists(path), f"commands/{cmd} missing"
        with open(path) as f:
            content = f.read()
        assert len(content) > 100, f"{cmd} is too short"


def test_reference_files_exist():
    """All 6 reference files exist and are non-empty."""
    refs = [
        "estate-formulas.md",
        "custody-formulas.md",
        "estate-tax-classification.md",
        "trust-structure-template.md",
        "successor-template.md",
        "key-package-template.md",
    ]
    for ref in refs:
        path = os.path.join(PLUGIN_ROOT, "references", ref)
        assert os.path.exists(path), f"references/{ref} missing"
        with open(path) as f:
            content = f.read()
        assert len(content) > 50, f"{ref} is too short"


def test_estate_formulas_has_key_constants():
    """estate-formulas.md contains required constants and thresholds."""
    path = os.path.join(PLUGIN_ROOT, "references", "estate-formulas.md")
    with open(path) as f:
        content = f.read()
    for constant in [
        "ESTATE_CHECK_WARNING_DAYS",
        "ESTATE_CHECK_CRITICAL_DAYS",
        "KEY_PACKAGE_MAX_AGE_YEARS",
        "WILL_FRESHNESS_YEARS",
        "INSURANCE_MULTIPLIER",
    ]:
        assert constant in content, f"estate-formulas.md missing constant: {constant}"


def test_custody_formulas_has_key_constants():
    """custody-formulas.md contains required constants and thresholds."""
    path = os.path.join(PLUGIN_ROOT, "references", "custody-formulas.md")
    with open(path) as f:
        content = f.read()
    for constant in [
        "SOVEREIGN_CUSTODY_FLOOR_PCT",
        "RECOVERY_CADENCE_DEFAULT_MONTHS",
        "MIN_BACKUP_LOCATIONS",
    ]:
        assert constant in content, f"custody-formulas.md missing constant: {constant}"


def test_estate_tax_has_ticker_lists():
    """estate-tax-classification.md contains US-situs and UCITS-safe ticker lists."""
    path = os.path.join(PLUGIN_ROOT, "references", "estate-tax-classification.md")
    with open(path) as f:
        content = f.read()
    # Check key US-situs tickers
    for ticker in ["VOO", "SPY", "QQQ", "IBIT", "VTI"]:
        assert ticker in content, f"estate-tax-classification.md missing US-situs ticker: {ticker}"
    # Check key UCITS-safe tickers
    for ticker in ["VUSA", "CSPX", "IWDA"]:
        assert ticker in content, f"estate-tax-classification.md missing UCITS-safe ticker: {ticker}"
    # Check key constants
    assert "NRNC_EXEMPTION_USD" in content
    assert "60000" in content


def test_documents_checker_script_exists_and_executable():
    """scripts/documents-checker.py exists and is executable."""
    path = os.path.join(PLUGIN_ROOT, "scripts", "documents-checker.py")
    assert os.path.exists(path), "scripts/documents-checker.py missing"
    assert os.access(path, os.X_OK), "documents-checker.py is not executable"


def test_no_skills_directory():
    """Zero-skill architecture: no skills/ directory should exist."""
    path = os.path.join(PLUGIN_ROOT, "skills")
    assert not os.path.exists(path), "skills/ directory must not exist (zero-skill architecture)"


def test_no_agents_directory():
    """No agents/ directory should exist."""
    path = os.path.join(PLUGIN_ROOT, "agents")
    assert not os.path.exists(path), "agents/ directory must not exist"


def test_reference_files_under_300_lines():
    """All reference files must be under 300 lines each."""
    ref_dir = os.path.join(PLUGIN_ROOT, "references")
    for fname in os.listdir(ref_dir):
        if fname.endswith(".md"):
            path = os.path.join(ref_dir, fname)
            with open(path) as f:
                lines = len(f.readlines())
            assert lines < 300, f"{fname} has {lines} lines, expected < 300"


def test_estate_check_references_formulas():
    """estate-check.md must reference estate-formulas.md and estate-tax-classification.md."""
    path = os.path.join(PLUGIN_ROOT, "commands", "estate-check.md")
    with open(path) as f:
        content = f.read()
    assert "estate-formulas.md" in content, "estate-check.md doesn't reference estate-formulas.md"
    assert "estate-tax-classification.md" in content, "estate-check.md doesn't reference estate-tax-classification.md"


def test_custody_audit_references_formulas():
    """custody-audit.md must reference custody-formulas.md."""
    path = os.path.join(PLUGIN_ROOT, "commands", "custody-audit.md")
    with open(path) as f:
        content = f.read()
    assert "custody-formulas.md" in content, "custody-audit.md doesn't reference custody-formulas.md"


def test_create_key_package_references_template():
    """create-key-package.md must reference key-package-template.md."""
    path = os.path.join(PLUGIN_ROOT, "commands", "create-key-package.md")
    with open(path) as f:
        content = f.read()
    assert "key-package-template.md" in content, "create-key-package.md doesn't reference key-package-template.md"


def test_documents_references_checker_script():
    """documents.md must reference documents-checker.py."""
    path = os.path.join(PLUGIN_ROOT, "commands", "documents.md")
    with open(path) as f:
        content = f.read()
    assert "documents-checker.py" in content, "documents.md doesn't reference documents-checker.py"


def test_content_file_count():
    """Plugin should have exactly 12 content files (4 commands + 6 references + 1 script + 1 plugin.json)."""
    count = 0
    for root, dirs, files in os.walk(PLUGIN_ROOT):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__", ".git", ".pytest_cache")]
        for f in files:
            if not f.startswith("."):
                count += 1
    assert count == 12, f"Plugin has {count} content files, expected 12 (excl. tests)"
