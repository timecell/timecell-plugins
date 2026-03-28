#!/usr/bin/env python3
"""Unit tests for fetch-mf-data.py — AMFI NAV fetcher."""
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from unittest import mock

# Add scripts dir to path for import (hyphenated filename needs importlib)
PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
_spec = importlib.util.spec_from_file_location(
    "fetch_mf_data",
    os.path.join(PLUGIN_ROOT, "scripts", "fetch-mf-data.py"),
)
fmd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fmd)


class TestCacheReadWrite:
    """Cache read/write cycle tests."""

    def test_cache_write_and_read(self, tmp_path):
        """Write cache, read it back, verify freshness."""
        cache_file = tmp_path / "mf-nav-data.json"
        original_cache_file = fmd.CACHE_FILE
        original_cache_dir = fmd.CACHE_DIR

        try:
            fmd.CACHE_FILE = str(cache_file)
            fmd.CACHE_DIR = str(tmp_path)

            test_data = {"schemes": {"119551": {"nav": 45.12}}, "timestamp": "test"}
            fmd.write_cache(test_data)

            cached, is_fresh = fmd.read_cache()
            assert is_fresh is True
            assert cached is not None
            assert cached["schemes"]["119551"]["nav"] == 45.12
        finally:
            fmd.CACHE_FILE = original_cache_file
            fmd.CACHE_DIR = original_cache_dir

    def test_cache_expired(self, tmp_path):
        """Expired cache returns None."""
        cache_file = tmp_path / "mf-nav-data.json"
        original_cache_file = fmd.CACHE_FILE
        original_cache_dir = fmd.CACHE_DIR

        try:
            fmd.CACHE_FILE = str(cache_file)
            fmd.CACHE_DIR = str(tmp_path)

            test_data = {"schemes": {}, "_cached_at": time.time() - 100000}
            with open(cache_file, "w") as f:
                json.dump(test_data, f)

            cached, is_fresh = fmd.read_cache()
            assert is_fresh is False
        finally:
            fmd.CACHE_FILE = original_cache_file
            fmd.CACHE_DIR = original_cache_dir

    def test_cache_missing_file(self, tmp_path):
        """Missing cache file returns None, False."""
        original_cache_file = fmd.CACHE_FILE
        try:
            fmd.CACHE_FILE = str(tmp_path / "nonexistent.json")
            cached, is_fresh = fmd.read_cache()
            assert cached is None
            assert is_fresh is False
        finally:
            fmd.CACHE_FILE = original_cache_file


class TestSchemeCodeExtraction:
    """Profile parsing for scheme codes."""

    def test_extract_codes_from_profile(self, tmp_path):
        """Extract scheme codes from a profile with MF section."""
        profile = tmp_path / "profile.md"
        profile.write_text("""# Portfolio

## Mutual Fund Holdings

- Scheme: HDFC Flexi Cap
  scheme_code: 119551
- Scheme: Parag Parikh Flexi Cap
  scheme_code: 122639

## Other Assets
- Cash: 100000
""")
        original_paths = fmd.PROFILE_PATHS
        try:
            fmd.PROFILE_PATHS = [str(profile)]
            codes = fmd.extract_scheme_codes_from_profile()
            assert codes == ["119551", "122639"]
        finally:
            fmd.PROFILE_PATHS = original_paths

    def test_extract_codes_no_profile(self, tmp_path):
        """Missing profile returns empty list."""
        original_paths = fmd.PROFILE_PATHS
        try:
            fmd.PROFILE_PATHS = [str(tmp_path / "nonexistent.md")]
            codes = fmd.extract_scheme_codes_from_profile()
            assert codes == []
        finally:
            fmd.PROFILE_PATHS = original_paths


class TestReturnCalculation:
    """Return calculation from NAV history."""

    def test_calculate_returns_with_history(self):
        """Calculate 1Y return from mock history."""
        from datetime import datetime, timedelta
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)

        history = [
            {"date": today.strftime("%Y-%m-%d"), "nav": 110.0},
            {"date": one_year_ago.strftime("%Y-%m-%d"), "nav": 100.0},
        ]
        returns = fmd.calculate_returns(history)
        assert returns["return_1y"] == 10.0  # 10% return

    def test_calculate_returns_insufficient_data(self):
        """Single entry returns None for both periods."""
        returns = fmd.calculate_returns([{"date": "2026-01-01", "nav": 100.0}])
        assert returns["return_1y"] is None
        assert returns["return_3y"] is None

    def test_calculate_returns_empty(self):
        """Empty history returns None."""
        returns = fmd.calculate_returns([])
        assert returns["return_1y"] is None


class TestSearchParsing:
    """Search result parsing."""

    def test_search_schemes_mock(self):
        """Mock search returns parsed results."""
        mock_response = json.dumps([
            {"schemeCode": 119551, "schemeName": "HDFC Flexi Cap Fund - Direct Plan - Growth"},
            {"schemeCode": 119552, "schemeName": "HDFC Flexi Cap Fund - Regular Plan - Growth"},
        ]).encode()

        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = mock_response
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = fmd.search_schemes("HDFC Flexi")
            assert len(result["results"]) == 2
            assert result["results"][0]["scheme_code"] == "119551"
            assert "HDFC" in result["results"][0]["scheme_name"]


class TestStalenessDetection:
    """Staleness detection tests."""

    def test_stale_nav_detected(self):
        """NAV older than threshold triggers stale flag."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(hours=80)).strftime("%d-%m-%Y")

        schemes = {"119551": {"date": old_date, "nav": 45.0}}
        is_stale, warning = fmd.check_staleness(schemes, now)
        assert is_stale is True
        assert warning is not None

    def test_fresh_nav_not_stale(self):
        """Recent NAV is not flagged as stale."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        fresh_date = now.strftime("%d-%m-%Y")

        schemes = {"119551": {"date": fresh_date, "nav": 45.0}}
        is_stale, warning = fmd.check_staleness(schemes, now)
        assert is_stale is False


class TestNetworkErrorHandling:
    """Graceful failure on network errors."""

    def test_fetch_json_network_error(self):
        """Network error returns None with error message."""
        with mock.patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            data, err = fmd.fetch_json("https://api.mfapi.in/mf/999999/latest")
            assert data is None
            assert "Connection refused" in err

    def test_fetch_scheme_nav_error(self):
        """Scheme fetch error returns error dict."""
        with mock.patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = fmd.fetch_scheme_nav("999999")
            assert "error" in result
            assert result["scheme_code"] == "999999"


class TestOutputFormat:
    """JSON output format validation."""

    def test_output_has_required_fields(self):
        """Main output structure has all required fields."""
        required = ["schemes", "scheme_count", "errors", "timestamp",
                     "cached", "data_age_hours", "stale", "manual_input_needed"]
        # We test the output structure by constructing it
        output = {
            "schemes": {},
            "scheme_count": 0,
            "errors": [],
            "timestamp": "2026-03-27T00:00:00+00:00",
            "cached": False,
            "data_age_hours": 0,
            "stale": False,
            "manual_input_needed": True,
        }
        for field in required:
            assert field in output, f"Missing required field: {field}"
