#!/usr/bin/env python3
"""Unit tests for documents-checker.py."""
import os
import sys
import json
import tempfile
from datetime import date, timedelta

# Add scripts dir to path
PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(PLUGIN_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

# Import the module directly by loading it
import importlib.util
spec = importlib.util.spec_from_file_location(
    "documents_checker",
    os.path.join(SCRIPTS_DIR, "documents-checker.py")
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def _write_registry(tmpdir, yaml_content):
    """Helper: write a documents/index.md with given YAML front matter."""
    path = os.path.join(tmpdir, "index.md")
    with open(path, "w") as f:
        f.write(f"---\n{yaml_content}\n---\n")
    return path


def test_load_empty_file():
    """Empty file returns empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "index.md")
        with open(path, "w") as f:
            f.write("")
        docs = checker.load_registry(path)
        assert docs == []


def test_load_missing_file():
    """Missing file returns empty list."""
    docs = checker.load_registry("/nonexistent/path/index.md")
    assert docs == []


def test_load_single_document():
    """Parse a single document entry from YAML."""
    yaml = """schema: estate-documents-v1
last_updated: 2026-03-11

documents:
  - id: will-001
    type: will
    title: "Singapore Will"
    storage:
      medium: physical
      location: "Rajah & Tann"
    last_updated: "2023-04-15"
    next_review: "2028-04-15"
    notes: "Covers SG assets only." """
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_registry(tmpdir, yaml)
        docs = checker.load_registry(path)
        assert len(docs) == 1
        assert docs[0]["id"] == "will-001"
        assert docs[0]["type"] == "will"
        assert docs[0]["title"] == "Singapore Will"
        assert docs[0]["storage"]["medium"] == "physical"
        assert docs[0]["last_updated"] == "2023-04-15"


def test_load_multiple_documents():
    """Parse multiple document entries."""
    yaml = """schema: estate-documents-v1
documents:
  - id: will-001
    type: will
    title: "Will"
    last_updated: "2023-01-01"
  - id: lpa-001
    type: lpa
    title: "LPA"
    last_updated: "2024-06-01"
  - id: trust-001
    type: trust-deed
    title: "Trust Deed"
    last_updated: "2022-01-01" """
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_registry(tmpdir, yaml)
        docs = checker.load_registry(path)
        assert len(docs) == 3


def test_staleness_current():
    """Document within threshold is 'current'."""
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    doc = {"type": "will", "last_updated": recent, "storage": {"medium": "physical"}}
    assert checker.check_staleness(doc, today) == "current"


def test_staleness_stale():
    """Document beyond threshold is 'stale'."""
    today = date.today()
    old = (today - timedelta(days=2000)).isoformat()  # > 1825 days (5 years)
    doc = {"type": "will", "last_updated": old, "storage": {"medium": "physical"}}
    assert checker.check_staleness(doc, today) == "stale"


def test_staleness_planned():
    """Planned document returns 'planned'."""
    doc = {"type": "will", "last_updated": None, "storage": {"medium": "planned"}}
    assert checker.check_staleness(doc) == "planned"


def test_staleness_missing():
    """Document with no last_updated returns 'missing'."""
    doc = {"type": "will", "last_updated": None, "storage": {"medium": "physical"}}
    assert checker.check_staleness(doc) == "missing"


def test_score_planned_is_zero():
    """Planned documents score 0 (not present for guardrail)."""
    doc = {"type": "will", "last_updated": None, "storage": {"medium": "planned"}}
    assert checker.score_document(doc) == 0


def test_score_stale_is_one():
    """Stale documents score 1 (present, shown as warning)."""
    today = date.today()
    old = (today - timedelta(days=2000)).isoformat()
    doc = {"type": "will", "last_updated": old, "storage": {"medium": "physical"}}
    assert checker.score_document(doc, today) == 1


def test_score_current_is_one():
    """Current documents score 1."""
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    doc = {"type": "will", "last_updated": recent, "storage": {"medium": "physical"}}
    assert checker.score_document(doc, today) == 1


def test_completeness_full():
    """5 of 5 required types present = SAFE."""
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    docs = [
        {"type": "will", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "trust-deed", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "lpa", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "healthcare-directive", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "digital-asset-plan", "last_updated": recent, "storage": {"medium": "physical"}},
    ]
    result = checker.compute_completeness(docs, today)
    assert result["score"] == 5
    assert result["required_total"] == 5
    assert result["zone"] == "SAFE"
    assert result["missing"] == []


def test_completeness_partial():
    """3 of 5 required types present = WARNING."""
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    docs = [
        {"type": "will", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "lpa", "last_updated": recent, "storage": {"medium": "physical"}},
        {"type": "healthcare-directive", "last_updated": recent, "storage": {"medium": "physical"}},
    ]
    result = checker.compute_completeness(docs, today)
    assert result["score"] == 3
    assert result["zone"] == "CRITICAL"
    assert "trust-deed" in result["missing"]
    assert "digital-asset-plan" in result["missing"]


def test_completeness_empty():
    """0 documents = CRITICAL."""
    result = checker.compute_completeness([])
    assert result["score"] == 0
    assert result["zone"] == "CRITICAL"
    assert len(result["missing"]) == 5


def test_zone_classification():
    """Verify zone thresholds: 0-2 CRITICAL, 3-4 WARNING, 5 SAFE."""
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    required = ["will", "trust-deed", "lpa", "healthcare-directive", "digital-asset-plan"]

    # 4 of 5 = WARNING
    docs = [{"type": t, "last_updated": recent, "storage": {"medium": "physical"}}
            for t in required[:4]]
    result = checker.compute_completeness(docs, today)
    assert result["zone"] == "WARNING"


def test_expiry_expired():
    """Document with past expiry_date returns 'expired'."""
    today = date.today()
    past = (today - timedelta(days=10)).isoformat()
    doc = {"type": "insurance-life", "expiry_date": past}
    expiry = checker.check_expiry(doc, today)
    assert expiry["has_expiry"] is True
    assert expiry["alert_level"] == "expired"
    assert expiry["days_until"] == -10


def test_expiry_critical():
    """Document expiring within 30 days returns 'critical'."""
    today = date.today()
    soon = (today + timedelta(days=15)).isoformat()
    doc = {"type": "insurance-life", "expiry_date": soon}
    expiry = checker.check_expiry(doc, today)
    assert expiry["alert_level"] == "critical"


def test_expiry_warning():
    """Document expiring within 90 days returns 'warning'."""
    today = date.today()
    later = (today + timedelta(days=60)).isoformat()
    doc = {"type": "insurance-life", "expiry_date": later}
    expiry = checker.check_expiry(doc, today)
    assert expiry["alert_level"] == "warning"


def test_expiry_ok():
    """Document expiring in >90 days returns 'ok'."""
    today = date.today()
    far = (today + timedelta(days=200)).isoformat()
    doc = {"type": "insurance-life", "expiry_date": far}
    expiry = checker.check_expiry(doc, today)
    assert expiry["alert_level"] == "ok"


def test_category_mapping():
    """Documents get correct categories."""
    assert checker.get_category({"type": "will"}) == "estate"
    assert checker.get_category({"type": "insurance-life"}) == "insurance"
    assert checker.get_category({"type": "property-deed"}) == "property"
    assert checker.get_category({"type": "loan-mortgage"}) == "loans"
    assert checker.get_category({"type": "legal-partnership"}) == "legal"
    assert checker.get_category({"type": "tax-return"}) == "tax"
    assert checker.get_category({"type": "other"}) == "other"


def test_valid_type_validation():
    """All 28 document types are in VALID_TYPES."""
    expected_types = {
        "will", "trust-deed", "lpa", "healthcare-directive", "key-package",
        "digital-asset-plan", "cpf-nomination", "insurance", "tax", "identity",
        "insurance-life", "insurance-health", "insurance-property", "insurance-liability",
        "property-deed", "property-title", "property-valuation",
        "loan-mortgage", "loan-personal", "loan-business",
        "legal-partnership", "legal-shareholder", "legal-contract",
        "tax-return", "tax-assessment", "tax-ruling",
        "other",
    }
    assert expected_types.issubset(checker.VALID_TYPES)


def test_staleness_type_specific_thresholds():
    """Key-package has 1-year threshold (365 days), will has 5-year (1825 days)."""
    today = date.today()
    # 400 days old — stale for key-package (365), current for will (1825)
    d = (today - timedelta(days=400)).isoformat()
    kp = {"type": "key-package", "last_updated": d, "storage": {"medium": "physical"}}
    will = {"type": "will", "last_updated": d, "storage": {"medium": "physical"}}
    assert checker.check_staleness(kp, today) == "stale"
    assert checker.check_staleness(will, today) == "current"
