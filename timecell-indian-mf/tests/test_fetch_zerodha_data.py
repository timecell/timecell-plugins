#!/usr/bin/env python3
"""Unit tests for fetch-zerodha-data.py — Kite Connect fetcher."""
import importlib
import importlib.util
import json
import os
import sys
import time
from unittest import mock

# Add scripts dir to path for import (hyphenated filename needs importlib)
PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
_spec = importlib.util.spec_from_file_location(
    "fetch_zerodha_data",
    os.path.join(PLUGIN_ROOT, "scripts", "fetch-zerodha-data.py"),
)
fetch_zerodha = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch_zerodha)


class TestCredentialReading:
    """Credential reading from env vars."""

    def test_credentials_from_env(self):
        """Read all three credentials from env vars."""
        with mock.patch.dict(os.environ, {
            "ZERODHA_API_KEY": "test_key",
            "ZERODHA_API_SECRET": "test_secret",
            "ZERODHA_ACCESS_TOKEN": "test_token",
        }):
            api_key, api_secret, access_token = fetch_zerodha.get_credentials()
            assert api_key == "test_key"
            assert api_secret == "test_secret"
            assert access_token == "test_token"

    def test_missing_credentials(self):
        """Missing env vars return None."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove any existing zerodha env vars
            for key in ["ZERODHA_API_KEY", "ZERODHA_API_SECRET", "ZERODHA_ACCESS_TOKEN"]:
                os.environ.pop(key, None)
            api_key, api_secret, access_token = fetch_zerodha.get_credentials()
            assert api_key is None
            assert api_secret is None
            assert access_token is None


class TestMissingCredentialsGraceful:
    """Graceful error when credentials missing."""

    def test_no_api_key_returns_auth_error(self):
        """Missing API key returns auth error response."""
        with mock.patch.dict(os.environ, {}, clear=True):
            for key in ["ZERODHA_API_KEY", "ZERODHA_API_SECRET", "ZERODHA_ACCESS_TOKEN"]:
                os.environ.pop(key, None)
            result = fetch_zerodha.fetch_zerodha_data(use_cache=False)
            assert result["manual_input_needed"] is True
            assert "auth_error" in result
            assert "not configured" in result["auth_error"]

    def test_no_access_token_returns_auth_error(self):
        """Missing access token returns specific auth error."""
        with mock.patch.dict(os.environ, {
            "ZERODHA_API_KEY": "test_key",
            "ZERODHA_API_SECRET": "test_secret",
        }):
            os.environ.pop("ZERODHA_ACCESS_TOKEN", None)
            result = fetch_zerodha.fetch_zerodha_data(use_cache=False)
            assert result["manual_input_needed"] is True
            assert "auth_error" in result
            assert "daily login" in result["auth_error"]


class TestMFHoldingsNormalization:
    """MF holdings normalization to indian-mf schema."""

    def test_normalize_mf_holding_basic(self):
        """Normalize a standard Kite MF holding."""
        kite_mf = {
            "fund": "HDFC Flexi Cap Fund - Direct Plan - Growth",
            "tradingsymbol": "INF179KA1EU4",
            "folio": "1234567890",
            "quantity": 100.5,
            "average_price": 40.0,
            "last_price": 45.12,
            "pnl": 514.56,
            "last_price_date": "2026-03-27",
        }
        result = fetch_zerodha.normalize_mf_holding(kite_mf)
        assert result["scheme_name_normalized"] == "HDFC Flexi Cap Fund"
        assert result["plan_detected"] == "direct"
        assert result["current_value"] == round(45.12 * 100.5, 2)
        assert result["invested_amount"] == round(40.0 * 100.5, 2)

    def test_detect_regular_plan(self):
        """Regular plan detection from fund name."""
        assert fetch_zerodha.detect_plan("HDFC Flexi Cap - Regular Plan - Growth") == "regular"
        assert fetch_zerodha.detect_plan("HDFC Flexi Cap - Direct Plan - Growth") == "direct"
        assert fetch_zerodha.detect_plan("HDFC Flexi Cap Fund") == "regular"  # default

    def test_normalize_scheme_name(self):
        """Scheme name normalization strips suffixes."""
        assert fetch_zerodha.normalize_scheme_name(
            "HDFC Flexi Cap Fund - Direct Plan - Growth"
        ) == "HDFC Flexi Cap Fund"
        assert fetch_zerodha.normalize_scheme_name(
            "SBI Blue Chip Fund - Regular - Growth"
        ) == "SBI Blue Chip Fund"


class TestSIPExtraction:
    """SIP data extraction."""

    def test_normalize_sip(self):
        """Normalize a Kite Connect SIP entry."""
        kite_sip = {
            "sip_id": 12345,
            "fund": "HDFC Flexi Cap Fund - Direct Plan - Growth",
            "tradingsymbol": "INF179KA1EU4",
            "frequency": "monthly",
            "instalment_amount": 5000,
            "status": "active",
            "next_instalment_date": "2026-04-05",
            "completed_instalments": 24,
        }
        result = fetch_zerodha.normalize_sip(kite_sip)
        assert result["sip_id"] == "12345"
        assert result["instalment_amount"] == 5000.0
        assert result["status"] == "active"
        assert result["next_instalment"] == "2026-04-05"
        assert result["completed_instalments"] == 24


class TestTokenExchangeFlow:
    """Token exchange flow tests."""

    def test_exchange_token_success(self):
        """Successful token exchange returns access_token."""
        mock_response = json.dumps({
            "data": {
                "access_token": "new_token_123",
                "user_id": "AB1234",
                "email": "user@example.com",
            }
        }).encode()

        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = mock_response
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = fetch_zerodha.exchange_token("api_key", "api_secret", "request_token")
            assert result["access_token"] == "new_token_123"


class TestCacheBehavior:
    """Cache behavior tests."""

    def test_cache_write_and_read(self, tmp_path):
        """Write cache, read it back fresh."""
        cache_file = tmp_path / "zerodha-data.json"
        original_cache_file = fetch_zerodha.CACHE_FILE
        original_cache_dir = fetch_zerodha.CACHE_DIR

        try:
            fetch_zerodha.CACHE_FILE = str(cache_file)
            fetch_zerodha.CACHE_DIR = str(tmp_path)

            test_data = {"plugin": "indian-mf", "data": {"mf_holdings": []}}
            fetch_zerodha.write_cache(test_data)

            cached, is_fresh = fetch_zerodha.read_cache()
            assert is_fresh is True
            assert cached["plugin"] == "indian-mf"
        finally:
            fetch_zerodha.CACHE_FILE = original_cache_file
            fetch_zerodha.CACHE_DIR = original_cache_dir


class TestNoCredentialsInOutput:
    """Security: credentials must never appear in output."""

    def test_auth_error_has_no_credentials(self):
        """Auth error response must not contain credential values."""
        with mock.patch.dict(os.environ, {
            "ZERODHA_API_KEY": "secret_key_abc",
            "ZERODHA_API_SECRET": "secret_secret_xyz",
        }):
            os.environ.pop("ZERODHA_ACCESS_TOKEN", None)
            result = fetch_zerodha.fetch_zerodha_data(use_cache=False)
            output = json.dumps(result)
            assert "secret_key_abc" not in output, "API key leaked in output"
            assert "secret_secret_xyz" not in output, "API secret leaked in output"

    def test_cache_has_no_credentials(self, tmp_path):
        """Cached data must not contain credential values."""
        cache_file = tmp_path / "zerodha-data.json"
        original_cache_file = fetch_zerodha.CACHE_FILE
        original_cache_dir = fetch_zerodha.CACHE_DIR

        try:
            fetch_zerodha.CACHE_FILE = str(cache_file)
            fetch_zerodha.CACHE_DIR = str(tmp_path)

            test_data = {
                "plugin": "indian-mf",
                "data": {"mf_holdings": [], "summary": None},
            }
            fetch_zerodha.write_cache(test_data)

            with open(cache_file) as f:
                cached_content = f.read()
            assert "ZERODHA_API_KEY" not in cached_content
            assert "ZERODHA_API_SECRET" not in cached_content
            assert "ZERODHA_ACCESS_TOKEN" not in cached_content
        finally:
            fetch_zerodha.CACHE_FILE = original_cache_file
            fetch_zerodha.CACHE_DIR = original_cache_dir
