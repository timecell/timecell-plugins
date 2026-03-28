#!/usr/bin/env python3
"""Structural validation tests for timecell-bitcoin add-on plugin."""
import os
import json

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_plugin_json_valid():
    """plugin.json exists, is valid JSON, has correct name/version/dependency."""
    path = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
    assert os.path.exists(path), ".claude-plugin/plugin.json missing"
    with open(path) as f:
        data = json.load(f)
    assert data["name"] == "timecell-bitcoin"
    assert data["version"] == "1.1.0"
    deps = data.get("dependencies", [])
    assert "timecell" in deps, "Missing dependency on timecell core"


def test_btc_check_command_exists():
    """commands/btc-check.md exists and is non-empty."""
    path = os.path.join(PLUGIN_ROOT, "commands", "btc-check.md")
    assert os.path.exists(path), "commands/btc-check.md missing"
    with open(path) as f:
        content = f.read()
    assert len(content) > 100, "btc-check.md is too short"


def test_bitcoin_formulas_exists_with_constants():
    """references/bitcoin-formulas.md exists and contains key constants."""
    path = os.path.join(PLUGIN_ROOT, "references", "bitcoin-formulas.md")
    assert os.path.exists(path), "references/bitcoin-formulas.md missing"
    with open(path) as f:
        content = f.read()
    for constant in ["MVRV_MEAN", "MVRV_STD", "RHODL_MIN", "RHODL_MAX",
                      "SURVIVAL_RUNWAY_MONTHS", "NON_BTC_CORRELATION"]:
        assert constant in content, f"bitcoin-formulas.md missing constant: {constant}"


def test_bitcoin_conviction_exists_with_beliefs():
    """references/bitcoin-conviction.md exists and contains 9 beliefs."""
    path = os.path.join(PLUGIN_ROOT, "references", "bitcoin-conviction.md")
    assert os.path.exists(path), "references/bitcoin-conviction.md missing"
    with open(path) as f:
        content = f.read()
    belief_count = sum(1 for line in content.splitlines()
                       if line.strip()[:2] in [f"{i}." for i in range(1, 10)])
    assert belief_count >= 9, f"Expected 9 beliefs, found {belief_count}"


def test_fetch_script_exists_and_executable():
    """scripts/fetch-btc-data.py exists and is executable."""
    path = os.path.join(PLUGIN_ROOT, "scripts", "fetch-btc-data.py")
    assert os.path.exists(path), "scripts/fetch-btc-data.py missing"
    assert os.access(path, os.X_OK), "fetch-btc-data.py is not executable"


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


def test_btc_check_references_both_files():
    """btc-check.md must reference bitcoin-formulas.md, bitcoin-conviction.md, and hedge-formulas.md."""
    path = os.path.join(PLUGIN_ROOT, "commands", "btc-check.md")
    with open(path) as f:
        content = f.read()
    assert "bitcoin-formulas.md" in content, "btc-check.md doesn't reference bitcoin-formulas.md"
    assert "bitcoin-conviction.md" in content, "btc-check.md doesn't reference bitcoin-conviction.md"
    assert "hedge-formulas.md" in content, "btc-check.md doesn't reference hedge-formulas.md"


def test_hedge_formulas_exists_with_key_content():
    """references/hedge-formulas.md exists and contains key hedge concepts."""
    path = os.path.join(PLUGIN_ROOT, "references", "hedge-formulas.md")
    assert os.path.exists(path), "references/hedge-formulas.md missing"
    with open(path) as f:
        content = f.read()
    for term in ["Budget Tiers", "Layer Classification", "Exit Recommendations",
                  "CAGR Formula", "Coverage Health Score", "Collar Triggers",
                  "Hedge Ratio", "Breakeven Algorithm", "0.75%"]:
        assert term in content, f"hedge-formulas.md missing key content: {term}"


def test_hedge_engine_exists_and_executable():
    """scripts/hedge-engine.py exists and is executable."""
    path = os.path.join(PLUGIN_ROOT, "scripts", "hedge-engine.py")
    assert os.path.exists(path), "scripts/hedge-engine.py missing"
    assert os.access(path, os.X_OK), "hedge-engine.py is not executable"


def test_content_file_count():
    """Plugin should have exactly 7 content files (excluding tests, __pycache__, dotfiles)."""
    count = 0
    for root, dirs, files in os.walk(PLUGIN_ROOT):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__", ".git", ".pytest_cache")]
        for f in files:
            if not f.startswith("."):
                count += 1
    assert count == 7, f"Plugin has {count} content files, expected 7 (excl. tests)"
