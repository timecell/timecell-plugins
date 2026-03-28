#!/usr/bin/env python3
"""
TimeCell Update Checker

Runs on SessionStart hook. Compares local version.txt against
the latest GitHub release. If a newer version exists, writes
a marker file for the CIO to pick up conversationally.

Design: 5-second timeout, 24-hour throttle, fail-open.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

# --- Configuration ---
GITHUB_REPO = "timecell/timecell-plugins"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RAW_PLUGIN_JSON = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/timecell-core/.claude-plugin/plugin.json"
HTTP_TIMEOUT = 5  # seconds
THROTTLE_HOURS = 24


def _project_root() -> Path:
    """Find project root by walking up from script location."""
    # Script is at <project>/.claude/scripts/check-update.py
    # or <project>/scripts/check-update.py
    script_dir = Path(__file__).resolve().parent
    # Try finding .timecell/ or profile.md as project root markers
    candidate = script_dir.parent
    for _ in range(3):
        if (candidate / "profile.md").exists() or (candidate / ".timecell").exists():
            return candidate
        candidate = candidate.parent
    # Fallback: assume script is at <root>/scripts/ or <root>/.claude/scripts/
    return script_dir.parent


def _timecell_dir(project_root: Path) -> Path:
    """Return .timecell/ directory, creating if needed."""
    d = project_root / ".timecell"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_local_version(project_root: Path) -> str | None:
    """Read local version from references/version.txt or .claude/references/version.txt."""
    for rel in [
        "references/version.txt",
        ".claude/references/version.txt",
    ]:
        p = project_root / rel
        if p.exists():
            return p.read_text().strip()
    return None


def _should_check(timecell_dir: Path, throttle_hours: int = THROTTLE_HOURS) -> bool:
    """Return True if enough time has passed since last check."""
    marker = timecell_dir / "last-version-check.txt"
    if not marker.exists():
        return True
    try:
        last_ts = float(marker.read_text().strip())
        elapsed_hours = (time.time() - last_ts) / 3600
        return elapsed_hours >= throttle_hours
    except (ValueError, OSError):
        return True


def _record_check(timecell_dir: Path) -> None:
    """Write current timestamp as last check time."""
    marker = timecell_dir / "last-version-check.txt"
    marker.write_text(str(time.time()))


def _fetch_latest_version() -> tuple[str | None, str | None]:
    """
    Query GitHub for latest release version.
    Returns (version_string, release_url) or (None, None) on failure.

    Strategy: Try releases API first, fall back to raw plugin.json.
    """
    # Try GitHub Releases API
    try:
        req = Request(GITHUB_API_URL, headers={"Accept": "application/vnd.github.v3+json"})
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            # Strip leading 'v' if present
            version = tag.lstrip("v")
            url = data.get("html_url", "")
            if version:
                return version, url
    except (URLError, OSError, json.JSONDecodeError, KeyError):
        pass

    # Fallback: read plugin.json from main branch
    try:
        req = Request(GITHUB_RAW_PLUGIN_JSON)
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            version = data.get("version", "")
            if version:
                url = f"https://github.com/{GITHUB_REPO}/releases/latest"
                return version, url
    except (URLError, OSError, json.JSONDecodeError, KeyError):
        pass

    return None, None


def _parse_semver(version: str) -> tuple[int, ...]:
    """Parse a semver string into a tuple of ints for comparison."""
    parts = version.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)


def _is_newer(latest: str, current: str) -> bool:
    """Return True if latest version is strictly newer than current."""
    return _parse_semver(latest) > _parse_semver(current)


def check_update(project_root: Path | None = None) -> dict | None:
    """
    Main entry point. Returns update info dict if update available,
    None otherwise. Never raises exceptions (fail-open).
    """
    try:
        root = project_root or _project_root()
        tc_dir = _timecell_dir(root)

        # Throttle check
        if not _should_check(tc_dir):
            return None

        # Read local version
        current = _read_local_version(root)
        if not current:
            # No version file — can't compare, skip silently
            _record_check(tc_dir)
            return None

        # Fetch remote version
        latest, release_url = _fetch_latest_version()
        if not latest:
            # API unreachable — fail open
            _record_check(tc_dir)
            return None

        # Record that we checked (regardless of result)
        _record_check(tc_dir)

        # Compare
        if _is_newer(latest, current):
            update_info = {
                "current": current,
                "latest": latest,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "release_url": release_url or "",
            }
            # Write marker file
            marker = tc_dir / "update-available.json"
            marker.write_text(json.dumps(update_info, indent=2))
            return update_info

        # Same or older — clean up any stale marker
        stale_marker = tc_dir / "update-available.json"
        if stale_marker.exists():
            stale_marker.unlink()

        return None

    except Exception:
        # Fail open — never crash session start
        return None


if __name__ == "__main__":
    result = check_update()
    if result:
        print(f"Update available: v{result['current']} -> v{result['latest']}")
    # Silent exit if no update (hook should produce no output on success)
