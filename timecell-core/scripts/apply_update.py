#!/usr/bin/env python3
"""
TimeCell Update Applier

Downloads the latest release from GitHub, extracts it, and copies
plugin files into the project while protecting user data paths.

Called conversationally by the CIO when the user confirms an update.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

# --- USER_DATA_PATHS: NEVER overwritten during update ---
# If the user or Cowork generated it, it survives.
# If the developer shipped it, it gets replaced.
USER_DATA_PATHS = [
    # Core user data
    "profile.md",
    "entities/",
    "memory/",
    # User settings
    ".claude/settings.json",
    ".claude/settings.local.json",
    "CLAUDE.md",
    # User-generated content
    "decisions/",
    "snapshots/",
    "source-documents/",
    # Runtime state
    ".timecell/",
    # Artifacts (Cowork-generated JSX files at project root)
    "*.jsx",
]

GITHUB_REPO = "timecell/timecell-plugins"
HTTP_TIMEOUT = 30  # longer timeout for download


def _project_root() -> Path:
    """Find project root by walking up from script location."""
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir.parent
    for _ in range(3):
        if (candidate / "profile.md").exists() or (candidate / ".timecell").exists():
            return candidate
        candidate = candidate.parent
    return script_dir.parent


def _is_protected(rel_path: str) -> bool:
    """Check if a relative path matches any USER_DATA_PATHS pattern."""
    # Normalize path separators
    rel_path = rel_path.replace("\\", "/")

    for pattern in USER_DATA_PATHS:
        # Directory pattern (ends with /)
        if pattern.endswith("/"):
            dir_name = pattern.rstrip("/")
            if rel_path == dir_name or rel_path.startswith(dir_name + "/"):
                return True
        # Glob pattern (contains *)
        elif "*" in pattern:
            # Match against the filename portion
            filename = os.path.basename(rel_path)
            if fnmatch(filename, pattern):
                return True
            # Also match against full path
            if fnmatch(rel_path, pattern):
                return True
        # Exact file match
        else:
            if rel_path == pattern:
                return True

    return False


def _get_release_info(project_root: Path) -> dict | None:
    """Read update-available.json marker."""
    marker = project_root / ".timecell" / "update-available.json"
    if not marker.exists():
        return None
    try:
        return json.loads(marker.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _download_release_zip(version: str) -> bytes | None:
    """Download release zip from GitHub. Try release asset first, then source zip."""
    # Try release zipball
    urls = [
        f"https://github.com/{GITHUB_REPO}/archive/refs/tags/v{version}.zip",
        f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{version}.zip",
        f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip",
    ]
    for url in urls:
        try:
            req = Request(url)
            with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return resp.read()
        except (URLError, OSError):
            continue
    return None


def _extract_plugin_files(zip_data: bytes, plugin_name: str = "timecell-core") -> dict[str, bytes]:
    """
    Extract plugin files from zip archive.
    Returns dict of {relative_path: file_contents}.
    The zip typically has a top-level directory we need to strip.
    """
    files = {}
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = info.filename.split("/")
            # Skip the top-level archive directory (e.g., "timecell-plugins-v2.1.0/")
            if len(parts) < 2:
                continue
            # Find the plugin_name directory in the path
            try:
                plugin_idx = parts.index(plugin_name)
            except ValueError:
                continue
            # Get the path relative to the plugin root
            rel_parts = parts[plugin_idx + 1:]
            if not rel_parts:
                continue
            rel_path = "/".join(rel_parts)
            files[rel_path] = zf.read(info.filename)
    return files


def _map_plugin_to_project(rel_path: str) -> str | None:
    """
    Map a plugin-relative path to a project-relative path.
    Plugin files go into .claude/ in the project.

    Examples:
      commands/start.md -> .claude/commands/start.md
      scripts/check-update.py -> .claude/scripts/check-update.py  AND  scripts/check-update.py
      references/version.txt -> .claude/references/version.txt
      hooks/hooks.json -> .claude/hooks/hooks.json

    Returns None for files that shouldn't be copied (tests, plugin.json, etc.)
    """
    # Skip non-deployable files
    skip_prefixes = ["tests/", ".claude-plugin/", ".github/"]
    for prefix in skip_prefixes:
        if rel_path.startswith(prefix):
            return None

    # Everything else goes into .claude/
    return f".claude/{rel_path}"


def apply_update(project_root: Path | None = None) -> dict:
    """
    Main entry point. Downloads and applies the update.
    Returns a summary dict with counts and status.
    """
    root = project_root or _project_root()
    result = {
        "success": False,
        "files_updated": 0,
        "files_protected": 0,
        "error": None,
        "old_version": None,
        "new_version": None,
    }

    # Read update info
    release_info = _get_release_info(root)
    if not release_info:
        result["error"] = "No update-available.json found. Run check-update.py first."
        return result

    old_version = release_info.get("current", "unknown")
    new_version = release_info.get("latest", "unknown")
    result["old_version"] = old_version
    result["new_version"] = new_version

    # Download
    print(f"Downloading TimeCell v{new_version}...")
    zip_data = _download_release_zip(new_version)
    if not zip_data:
        result["error"] = f"Failed to download release v{new_version} from GitHub."
        return result

    # Verify zip is valid
    try:
        zipfile.ZipFile(io.BytesIO(zip_data))
    except zipfile.BadZipFile:
        result["error"] = "Downloaded file is not a valid zip archive."
        return result

    # Extract plugin files
    plugin_files = _extract_plugin_files(zip_data)
    if not plugin_files:
        result["error"] = "No plugin files found in the downloaded archive."
        return result

    print(f"Applying update ({len(plugin_files)} files)...")

    # Apply files
    updated = 0
    protected = 0
    for rel_path, content in plugin_files.items():
        project_path = _map_plugin_to_project(rel_path)
        if project_path is None:
            continue  # Skip non-deployable files

        # Check if the project-level path is protected
        if _is_protected(project_path):
            protected += 1
            continue

        # Write file
        target = root / project_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        updated += 1

    # Also copy scripts to project root scripts/ (scripts need to be runnable)
    for rel_path, content in plugin_files.items():
        if rel_path.startswith("scripts/") and rel_path.endswith(".py"):
            target = root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not _is_protected(rel_path):
                target.write_bytes(content)

    result["files_updated"] = updated
    result["files_protected"] = protected

    # Update local version.txt
    for version_path in [
        root / "references" / "version.txt",
        root / ".claude" / "references" / "version.txt",
    ]:
        if version_path.parent.exists():
            version_path.write_text(new_version + "\n")

    # Delete update marker
    marker = root / ".timecell" / "update-available.json"
    if marker.exists():
        marker.unlink()

    # Log the update
    log_file = root / ".timecell" / "install-log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} — updated timecell v{old_version} -> v{new_version} "
                f"({updated} files updated, {protected} user files preserved)\n")

    result["success"] = True
    print(f"\nUpdated TimeCell v{old_version} -> v{new_version}.")
    print(f"  {updated} files updated")
    print(f"  {protected} user files preserved")
    return result


if __name__ == "__main__":
    result = apply_update()
    if not result["success"]:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)
