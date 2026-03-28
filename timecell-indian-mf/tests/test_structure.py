#!/usr/bin/env python3
"""Structural validation tests for timecell-indian-mf add-on plugin."""
import os
import json

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_plugin_json_valid():
    """plugin.json exists, is valid JSON, has correct name/version/dependency."""
    path = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
    assert os.path.exists(path), ".claude-plugin/plugin.json missing"
    with open(path) as f:
        data = json.load(f)
    assert data["name"] == "timecell-indian-mf"
    assert data["version"] == "1.0.0"
    assert "timecell" in data.get("dependencies", []), "Missing dependency on timecell core"


def test_mf_review_command_exists():
    """commands/mf-review.md exists and is non-empty."""
    path = os.path.join(PLUGIN_ROOT, "commands", "mf-review.md")
    assert os.path.exists(path), "commands/mf-review.md missing"
    with open(path) as f:
        content = f.read()
    assert len(content) > 100, "mf-review.md is too short"


def test_mf_computation_formulas_exists_with_constants():
    """references/mf-computation-formulas.md exists and contains key constants."""
    path = os.path.join(PLUGIN_ROOT, "references", "mf-computation-formulas.md")
    assert os.path.exists(path), "references/mf-computation-formulas.md missing"
    with open(path) as f:
        content = f.read()
    for constant in ["UNDERPERFORMER_THRESHOLD", "EXPENSE_RATIO_BUFFER",
                      "XIRR_INITIAL_GUESS", "XIRR_TOLERANCE", "XIRR_MAX_ITERATIONS",
                      "ELSS_LOCK_IN_DAYS", "CATEGORY_MEDIAN_TER_EQUITY",
                      "CATEGORY_MEDIAN_TER_DEBT"]:
        assert constant in content, f"mf-computation-formulas.md missing constant: {constant}"


def test_mf_category_classification_exists():
    """references/mf-category-classification.md exists with SEBI categories."""
    path = os.path.join(PLUGIN_ROOT, "references", "mf-category-classification.md")
    assert os.path.exists(path), "references/mf-category-classification.md missing"
    with open(path) as f:
        content = f.read()
    # Check key SEBI categories are present
    for category in ["Large Cap", "Mid Cap", "Small Cap", "ELSS", "Liquid",
                      "Aggressive Hybrid", "Sectoral"]:
        assert category in content, f"Missing SEBI category: {category}"


def test_indian_entity_types_exists():
    """references/indian-entity-types.md exists with key entity types."""
    path = os.path.join(PLUGIN_ROOT, "references", "indian-entity-types.md")
    assert os.path.exists(path), "references/indian-entity-types.md missing"
    with open(path) as f:
        content = f.read()
    for entity in ["HUF", "Private Limited", "LLP", "Trust", "Partnership"]:
        assert entity in content, f"Missing entity type: {entity}"


def test_inr_formatting_exists():
    """references/inr-formatting.md exists with Lakh/Crore rules."""
    path = os.path.join(PLUGIN_ROOT, "references", "inr-formatting.md")
    assert os.path.exists(path), "references/inr-formatting.md missing"
    with open(path) as f:
        content = f.read()
    for term in ["Lakh", "Crore", "XX,XX,XXX"]:
        assert term in content, f"Missing INR formatting term: {term}"


def test_fetch_mf_data_script_exists_and_executable():
    """scripts/fetch-mf-data.py exists and is executable."""
    path = os.path.join(PLUGIN_ROOT, "scripts", "fetch-mf-data.py")
    assert os.path.exists(path), "scripts/fetch-mf-data.py missing"
    assert os.access(path, os.X_OK), "fetch-mf-data.py is not executable"


def test_fetch_zerodha_data_script_exists_and_executable():
    """scripts/fetch-zerodha-data.py exists and is executable."""
    path = os.path.join(PLUGIN_ROOT, "scripts", "fetch-zerodha-data.py")
    assert os.path.exists(path), "scripts/fetch-zerodha-data.py missing"
    assert os.access(path, os.X_OK), "fetch-zerodha-data.py is not executable"


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


def test_mf_review_references_all_files():
    """mf-review.md must reference all 4 reference files."""
    path = os.path.join(PLUGIN_ROOT, "commands", "mf-review.md")
    with open(path) as f:
        content = f.read()
    for ref in ["mf-computation-formulas.md", "mf-category-classification.md",
                 "indian-entity-types.md", "inr-formatting.md"]:
        assert ref in content, f"mf-review.md doesn't reference {ref}"


def test_content_file_count():
    """Plugin should have exactly 9 content files (1 command + 5 references + 2 scripts + 1 plugin.json)."""
    count = 0
    for root, dirs, files in os.walk(PLUGIN_ROOT):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__", ".git", ".pytest_cache")]
        for f in files:
            if not f.startswith("."):
                count += 1
    assert count == 9, f"Plugin has {count} content files, expected 9 (excl. tests)"
