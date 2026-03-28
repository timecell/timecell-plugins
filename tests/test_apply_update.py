"""
Tests for apply-update.py — download, extract, and apply updates
with USER_DATA_PATHS protection.

Tests cover: path protection, file mapping, zip extraction,
update application, marker cleanup, and logging.
"""

import io
import json
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path
PLUGIN_ROOT = Path(__file__).parent.parent / "timecell-core"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import apply_update


# --- Fixtures ---

@pytest.fixture
def project_dir(tmp_path):
    """Create a mock project with user data and plugin files."""
    root = tmp_path / "project"
    root.mkdir()

    # User data that must survive
    (root / "profile.md").write_text("Name: Raj Mehta\nBase Currency: INR\n")
    (root / "entities").mkdir()
    (root / "entities" / "savings.md").write_text("Bank: HDFC\n")
    (root / "memory").mkdir()
    (root / "memory" / "session-log.md").write_text("## 2026-03-27\n")
    (root / "decisions").mkdir()
    (root / "decisions" / "btc-allocation.md").write_text("Decided: 5%\n")
    (root / "snapshots").mkdir()
    (root / "snapshots" / "2026-03.md").write_text("Net worth: 100M\n")
    (root / "source-documents").mkdir()
    (root / "source-documents" / "tax.pdf").write_bytes(b"fake pdf")
    (root / ".timecell").mkdir()
    (root / ".timecell" / "session-count.txt").write_text("5")
    (root / "CLAUDE.md").write_text("# Custom instructions\n")
    (root / "dashboard.jsx").write_text("// user artifact\n")

    # .claude settings
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text('{"permissions": {}}')
    (claude_dir / "settings.local.json").write_text('{"local": true}')

    # Existing plugin files (will be overwritten)
    (claude_dir / "commands").mkdir()
    (claude_dir / "commands" / "start.md").write_text("old start command")
    (claude_dir / "references").mkdir()
    (claude_dir / "references" / "version.txt").write_text("2.0.1\n")
    (claude_dir / "scripts").mkdir()
    (claude_dir / "scripts" / "fetch-exchange-rates.py").write_text("# old script")
    (root / "references").mkdir()
    (root / "references" / "version.txt").write_text("2.0.1\n")

    # Update marker
    (root / ".timecell" / "update-available.json").write_text(json.dumps({
        "current": "2.0.1",
        "latest": "2.1.0",
        "checked_at": "2026-03-27T10:00:00Z",
        "release_url": "https://github.com/timecell/timecell-plugins/releases/v2.1.0",
    }))

    return root


def _make_release_zip(files: dict[str, str], top_dir: str = "timecell-plugins-v2.1.0") -> bytes:
    """Create a mock release zip with given files under timecell-core/."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for rel_path, content in files.items():
            full_path = f"{top_dir}/timecell-core/{rel_path}"
            zf.writestr(full_path, content)
    return buf.getvalue()


# --- USER_DATA_PATHS protection ---

class TestIsProtected:
    def test_profile_md(self):
        assert apply_update._is_protected("profile.md") is True

    def test_entities_dir(self):
        assert apply_update._is_protected("entities/savings.md") is True

    def test_entities_itself(self):
        assert apply_update._is_protected("entities") is True

    def test_memory_dir(self):
        assert apply_update._is_protected("memory/session-log.md") is True

    def test_decisions_dir(self):
        assert apply_update._is_protected("decisions/btc.md") is True

    def test_snapshots_dir(self):
        assert apply_update._is_protected("snapshots/2026-03.md") is True

    def test_source_documents_dir(self):
        assert apply_update._is_protected("source-documents/tax.pdf") is True

    def test_timecell_dir(self):
        assert apply_update._is_protected(".timecell/cache/rates.json") is True

    def test_claude_settings(self):
        assert apply_update._is_protected(".claude/settings.json") is True

    def test_claude_settings_local(self):
        assert apply_update._is_protected(".claude/settings.local.json") is True

    def test_claude_md(self):
        assert apply_update._is_protected("CLAUDE.md") is True

    def test_jsx_files(self):
        assert apply_update._is_protected("dashboard.jsx") is True
        assert apply_update._is_protected("some-artifact.jsx") is True

    def test_plugin_command_not_protected(self):
        assert apply_update._is_protected(".claude/commands/start.md") is False

    def test_plugin_reference_not_protected(self):
        assert apply_update._is_protected(".claude/references/timecell.md") is False

    def test_plugin_script_not_protected(self):
        assert apply_update._is_protected(".claude/scripts/check-update.py") is False

    def test_hooks_not_protected(self):
        assert apply_update._is_protected(".claude/hooks/hooks.json") is False


# --- File mapping ---

class TestMapPluginToProject:
    def test_command(self):
        assert apply_update._map_plugin_to_project("commands/start.md") == ".claude/commands/start.md"

    def test_reference(self):
        assert apply_update._map_plugin_to_project("references/timecell.md") == ".claude/references/timecell.md"

    def test_script(self):
        assert apply_update._map_plugin_to_project("scripts/check-update.py") == ".claude/scripts/check-update.py"

    def test_hooks(self):
        assert apply_update._map_plugin_to_project("hooks/hooks.json") == ".claude/hooks/hooks.json"

    def test_skip_tests(self):
        assert apply_update._map_plugin_to_project("tests/test_foo.py") is None

    def test_skip_plugin_json(self):
        assert apply_update._map_plugin_to_project(".claude-plugin/plugin.json") is None

    def test_skip_github(self):
        assert apply_update._map_plugin_to_project(".github/workflows/release.yml") is None


# --- Zip extraction ---

class TestExtractPluginFiles:
    def test_extracts_files(self):
        zip_data = _make_release_zip({
            "commands/start.md": "new start",
            "references/version.txt": "2.1.0\n",
            "scripts/check-update.py": "# new script",
        })
        files = apply_update._extract_plugin_files(zip_data)
        assert "commands/start.md" in files
        assert "references/version.txt" in files
        assert "scripts/check-update.py" in files
        assert files["commands/start.md"] == b"new start"

    def test_ignores_non_plugin_dirs(self):
        """Files not under timecell-core/ are ignored."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("timecell-plugins-v2.1.0/README.md", "repo readme")
            zf.writestr("timecell-plugins-v2.1.0/timecell-core/commands/start.md", "new start")
        files = apply_update._extract_plugin_files(buf.getvalue())
        assert "commands/start.md" in files
        assert "README.md" not in files


# --- Full apply_update flow ---

class TestApplyUpdate:
    @patch("apply_update._download_release_zip")
    def test_full_update_preserves_user_data(self, mock_download, project_dir):
        """The core test: user data must survive an update."""
        zip_data = _make_release_zip({
            "commands/start.md": "NEW start command v2.1.0",
            "references/version.txt": "2.1.0\n",
            "references/timecell.md": "NEW CIO persona v2.1.0",
            "scripts/check-update.py": "# NEW check script",
            "hooks/hooks.json": '{"hooks": {"SessionStart": []}}',
        })
        mock_download.return_value = zip_data

        result = apply_update.apply_update(project_dir)

        assert result["success"] is True
        assert result["old_version"] == "2.0.1"
        assert result["new_version"] == "2.1.0"
        assert result["files_updated"] > 0

        # USER DATA PRESERVED (byte-level check)
        assert (project_dir / "profile.md").read_text() == "Name: Raj Mehta\nBase Currency: INR\n"
        assert (project_dir / "entities" / "savings.md").read_text() == "Bank: HDFC\n"
        assert (project_dir / "memory" / "session-log.md").read_text() == "## 2026-03-27\n"
        assert (project_dir / "decisions" / "btc-allocation.md").read_text() == "Decided: 5%\n"
        assert (project_dir / "snapshots" / "2026-03.md").read_text() == "Net worth: 100M\n"
        assert (project_dir / "source-documents" / "tax.pdf").read_bytes() == b"fake pdf"
        assert (project_dir / ".timecell" / "session-count.txt").read_text() == "5"
        assert (project_dir / "CLAUDE.md").read_text() == "# Custom instructions\n"
        assert (project_dir / "dashboard.jsx").read_text() == "// user artifact\n"
        assert (project_dir / ".claude" / "settings.json").read_text() == '{"permissions": {}}'
        assert (project_dir / ".claude" / "settings.local.json").read_text() == '{"local": true}'

        # PLUGIN FILES UPDATED
        assert (project_dir / ".claude" / "commands" / "start.md").read_text() == "NEW start command v2.1.0"
        assert (project_dir / ".claude" / "references" / "timecell.md").read_text() == "NEW CIO persona v2.1.0"

        # Version updated
        assert (project_dir / ".claude" / "references" / "version.txt").read_text().strip() == "2.1.0"
        assert (project_dir / "references" / "version.txt").read_text().strip() == "2.1.0"

    @patch("apply_update._download_release_zip")
    def test_marker_deleted_after_apply(self, mock_download, project_dir):
        zip_data = _make_release_zip({"commands/start.md": "new"})
        mock_download.return_value = zip_data

        apply_update.apply_update(project_dir)

        marker = project_dir / ".timecell" / "update-available.json"
        assert not marker.exists()

    @patch("apply_update._download_release_zip")
    def test_install_log_written(self, mock_download, project_dir):
        zip_data = _make_release_zip({"commands/start.md": "new"})
        mock_download.return_value = zip_data

        apply_update.apply_update(project_dir)

        log = project_dir / ".timecell" / "install-log.txt"
        assert log.exists()
        content = log.read_text()
        assert "v2.0.1 -> v2.1.0" in content
        assert "updated" in content

    @patch("apply_update._download_release_zip")
    def test_download_failure(self, mock_download, project_dir):
        mock_download.return_value = None

        result = apply_update.apply_update(project_dir)
        assert result["success"] is False
        assert "Failed to download" in result["error"]

    def test_no_marker_file(self, tmp_path):
        """apply_update with no marker should fail gracefully."""
        (tmp_path / ".timecell").mkdir()
        (tmp_path / "profile.md").write_text("Name: Test\n")
        result = apply_update.apply_update(tmp_path)
        assert result["success"] is False
        assert "No update-available.json" in result["error"]

    @patch("apply_update._download_release_zip")
    def test_bad_zip(self, mock_download, project_dir):
        mock_download.return_value = b"this is not a zip file"
        result = apply_update.apply_update(project_dir)
        assert result["success"] is False
        assert "not a valid zip" in result["error"]

    @patch("apply_update._download_release_zip")
    def test_empty_zip(self, mock_download, project_dir):
        """Zip with no plugin files."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("random/file.txt", "nothing useful")
        mock_download.return_value = buf.getvalue()

        result = apply_update.apply_update(project_dir)
        assert result["success"] is False
        assert "No plugin files" in result["error"]


# --- Regression: USER_DATA_PATHS completeness ---

class TestUserDataPathsCompleteness:
    """Ensure all known user-generated paths are in the allowlist."""

    KNOWN_USER_PATHS = [
        "profile.md",
        "entities/",
        "memory/",
        ".claude/settings.json",
        ".claude/settings.local.json",
        "CLAUDE.md",
        "decisions/",
        "snapshots/",
        "source-documents/",
        ".timecell/",
        "*.jsx",
    ]

    def test_all_known_paths_protected(self):
        """If this test fails, someone removed a path from USER_DATA_PATHS."""
        for path in self.KNOWN_USER_PATHS:
            assert path in apply_update.USER_DATA_PATHS, (
                f"REGRESSION: '{path}' was removed from USER_DATA_PATHS! "
                f"This would cause user data loss during updates."
            )


# --- CLAUDE_PLUGIN_DATA env var ---

class TestPluginDataEnvVar:
    @patch("apply_update._download_release_zip")
    def test_uses_plugin_data_dir(self, mock_download, tmp_path):
        """When CLAUDE_PLUGIN_DATA is set, markers and logs go there."""
        plugin_data_dir = tmp_path / "plugin-data"
        plugin_data_dir.mkdir()

        root = tmp_path / "project"
        root.mkdir()
        (root / "profile.md").write_text("Name: Test\n")
        claude_dir = root / ".claude"
        claude_dir.mkdir()
        (claude_dir / "commands").mkdir()
        (claude_dir / "references").mkdir()
        (claude_dir / "references" / "version.txt").write_text("2.0.1\n")
        (root / "references").mkdir()
        (root / "references" / "version.txt").write_text("2.0.1\n")

        # Put marker in plugin_data_dir
        (plugin_data_dir / "update-available.json").write_text(json.dumps({
            "current": "2.0.1",
            "latest": "2.1.0",
            "checked_at": "2026-03-27T10:00:00Z",
            "release_url": "",
        }))

        zip_data = _make_release_zip({"commands/start.md": "new start"})
        mock_download.return_value = zip_data

        with patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(plugin_data_dir)}):
            result = apply_update.apply_update(root)
            assert result["success"] is True
            # Marker should be deleted from plugin_data_dir
            assert not (plugin_data_dir / "update-available.json").exists()
            # Install log should be in plugin_data_dir
            assert (plugin_data_dir / "install-log.txt").exists()
