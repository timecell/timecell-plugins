"""
Tests for check-update.py — version check against GitHub API.

Tests cover: throttling, version comparison, marker file creation,
fail-open behavior, and semver parsing.
"""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
PLUGIN_ROOT = Path(__file__).parent.parent / "timecell-core"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import check_update


# --- Fixtures ---

@pytest.fixture
def project_dir(tmp_path):
    """Create a mock project directory with version.txt."""
    refs = tmp_path / "references"
    refs.mkdir()
    (refs / "version.txt").write_text("2.0.1\n")
    (tmp_path / ".timecell").mkdir()
    (tmp_path / "profile.md").write_text("Name: Test\n")
    return tmp_path


@pytest.fixture
def project_dir_claude(tmp_path):
    """Create a mock project directory with .claude/references/version.txt layout."""
    claude_refs = tmp_path / ".claude" / "references"
    claude_refs.mkdir(parents=True)
    (claude_refs / "version.txt").write_text("2.0.1\n")
    (tmp_path / ".timecell").mkdir()
    (tmp_path / "profile.md").write_text("Name: Test\n")
    return tmp_path


# --- Semver parsing ---

class TestSemver:
    def test_parse_simple(self):
        assert check_update._parse_semver("2.0.1") == (2, 0, 1)

    def test_parse_major_only(self):
        assert check_update._parse_semver("3") == (3,)

    def test_parse_with_invalid(self):
        assert check_update._parse_semver("2.0.beta") == (2, 0, 0)

    def test_is_newer_true(self):
        assert check_update._is_newer("2.1.0", "2.0.1") is True

    def test_is_newer_false_same(self):
        assert check_update._is_newer("2.0.1", "2.0.1") is False

    def test_is_newer_false_older(self):
        assert check_update._is_newer("1.9.0", "2.0.1") is False

    def test_is_newer_major_bump(self):
        assert check_update._is_newer("3.0.0", "2.9.9") is True

    def test_is_newer_patch_bump(self):
        assert check_update._is_newer("2.0.2", "2.0.1") is True


# --- Throttling ---

class TestThrottling:
    def test_should_check_no_marker(self, project_dir):
        tc_dir = project_dir / ".timecell"
        assert check_update._should_check(tc_dir) is True

    def test_should_check_old_marker(self, project_dir):
        tc_dir = project_dir / ".timecell"
        # Write a timestamp from 25 hours ago
        old_time = time.time() - (25 * 3600)
        (tc_dir / "last-version-check.txt").write_text(str(old_time))
        assert check_update._should_check(tc_dir) is True

    def test_should_not_check_recent(self, project_dir):
        tc_dir = project_dir / ".timecell"
        # Write a timestamp from 1 hour ago
        recent_time = time.time() - (1 * 3600)
        (tc_dir / "last-version-check.txt").write_text(str(recent_time))
        assert check_update._should_check(tc_dir) is False

    def test_should_check_corrupt_marker(self, project_dir):
        tc_dir = project_dir / ".timecell"
        (tc_dir / "last-version-check.txt").write_text("not-a-number")
        assert check_update._should_check(tc_dir) is True

    def test_record_check_writes_marker(self, project_dir):
        tc_dir = project_dir / ".timecell"
        check_update._record_check(tc_dir)
        marker = tc_dir / "last-version-check.txt"
        assert marker.exists()
        ts = float(marker.read_text().strip())
        assert abs(ts - time.time()) < 5  # within 5 seconds


# --- Local version reading ---

class TestLocalVersion:
    def test_reads_from_references(self, project_dir):
        version = check_update._read_local_version(project_dir)
        assert version == "2.0.1"

    def test_reads_from_claude_references(self, project_dir_claude):
        version = check_update._read_local_version(project_dir_claude)
        assert version == "2.0.1"

    def test_returns_none_if_missing(self, tmp_path):
        assert check_update._read_local_version(tmp_path) is None


# --- Full check_update flow (mocked network) ---

class TestCheckUpdate:
    @patch("check_update._fetch_latest_version")
    def test_update_available(self, mock_fetch, project_dir):
        mock_fetch.return_value = ("2.1.0", "https://github.com/test/releases/v2.1.0")
        result = check_update.check_update(project_dir)
        assert result is not None
        assert result["current"] == "2.0.1"
        assert result["latest"] == "2.1.0"
        # Marker file should exist
        marker = project_dir / ".timecell" / "update-available.json"
        assert marker.exists()
        data = json.loads(marker.read_text())
        assert data["latest"] == "2.1.0"

    @patch("check_update._fetch_latest_version")
    def test_no_update_same_version(self, mock_fetch, project_dir):
        mock_fetch.return_value = ("2.0.1", "https://github.com/test/releases/v2.0.1")
        result = check_update.check_update(project_dir)
        assert result is None
        # No marker file
        marker = project_dir / ".timecell" / "update-available.json"
        assert not marker.exists()

    @patch("check_update._fetch_latest_version")
    def test_cleans_stale_marker(self, mock_fetch, project_dir):
        # Create a stale marker
        marker = project_dir / ".timecell" / "update-available.json"
        marker.write_text(json.dumps({"current": "1.0.0", "latest": "2.0.1"}))
        # Now check returns same version
        mock_fetch.return_value = ("2.0.1", "")
        check_update.check_update(project_dir)
        assert not marker.exists()

    @patch("check_update._fetch_latest_version")
    def test_api_unreachable(self, mock_fetch, project_dir):
        mock_fetch.return_value = (None, None)
        result = check_update.check_update(project_dir)
        assert result is None

    @patch("check_update._fetch_latest_version")
    def test_throttled_skip(self, mock_fetch, project_dir):
        # Set recent check time
        tc_dir = project_dir / ".timecell"
        recent = time.time() - 3600  # 1 hour ago
        (tc_dir / "last-version-check.txt").write_text(str(recent))
        result = check_update.check_update(project_dir)
        assert result is None
        # fetch should NOT have been called
        mock_fetch.assert_not_called()

    def test_no_version_file(self, tmp_path):
        """No version.txt -> skip silently."""
        (tmp_path / ".timecell").mkdir()
        (tmp_path / "profile.md").write_text("Name: Test\n")
        result = check_update.check_update(tmp_path)
        assert result is None

    @patch("check_update._fetch_latest_version")
    def test_fail_open_on_exception(self, mock_fetch, project_dir):
        """Any unexpected exception should not bubble up."""
        mock_fetch.side_effect = RuntimeError("unexpected")
        result = check_update.check_update(project_dir)
        assert result is None  # fail-open, no crash


# --- CLAUDE_PLUGIN_DATA env var ---

class TestPluginDataEnvVar:
    @patch("check_update._fetch_latest_version")
    def test_uses_plugin_data_dir(self, mock_fetch, tmp_path):
        """When CLAUDE_PLUGIN_DATA is set, markers go there."""
        plugin_data_dir = tmp_path / "plugin-data"
        plugin_data_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "profile.md").write_text("Name: Test\n")
        refs = project_dir / "references"
        refs.mkdir()
        (refs / "version.txt").write_text("2.0.1\n")

        mock_fetch.return_value = ("2.1.0", "https://github.com/test/releases/v2.1.0")

        with patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(plugin_data_dir)}):
            result = check_update.check_update(project_dir)
            assert result is not None
            # Marker should be in plugin_data_dir, not project/.timecell/
            assert (plugin_data_dir / "update-available.json").exists()
            assert not (project_dir / ".timecell" / "update-available.json").exists()
