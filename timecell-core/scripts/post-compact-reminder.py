#!/usr/bin/env python3
"""
PostCompact hook — re-inject essential profile context after compaction.

When Cowork compacts the context window, the CIO loses profile details
(name, currency, role, preferences). This script reads profile.md and
outputs a compact summary so the CIO persona survives mid-session.

Output goes to stdout and Cowork injects it as a system message.
If profile.md is missing or unreadable, outputs nothing (no-op).
"""

import os
import re
import sys
from pathlib import Path


def find_profile() -> Path | None:
    """Find profile.md relative to the script's plugin directory."""
    # Script lives in timecell-core/scripts/
    # profile.md lives in the user's working directory (project root)
    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    candidate = cwd / "profile.md"
    if candidate.is_file():
        return candidate
    return None


def extract_field(text: str, field: str) -> str | None:
    """Extract a YAML-like '- Field: Value' or 'Field: Value' line."""
    pattern = rf"^[-\s]*{re.escape(field)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def count_entities(profile_dir: Path) -> int:
    """Count .md files in entities/ directory."""
    entities_dir = profile_dir.parent / "entities"
    if not entities_dir.is_dir():
        return 0
    return len(list(entities_dir.glob("*.md")))


def count_sessions(profile_dir: Path) -> int:
    """Count session entries in session-log.md."""
    session_log = profile_dir.parent / "memory" / "session-log.md"
    if not session_log.is_file():
        return 1
    try:
        content = session_log.read_text()
        return max(1, len(re.findall(r"^## \d{4}-\d{2}-\d{2}", content, re.MULTILINE)))
    except OSError:
        return 1


def lifecycle_stage(session_count: int) -> str:
    """Determine lifecycle stage from session count."""
    if session_count <= 3:
        return "Onboarding"
    elif session_count <= 10:
        return "Discovery"
    elif session_count <= 30:
        return "Partnership"
    else:
        return "Trusted Advisor"


def main():
    profile_path = find_profile()
    if profile_path is None:
        return  # No profile — nothing to remind about

    try:
        text = profile_path.read_text()
    except OSError:
        return

    name = extract_field(text, "Name")
    if not name:
        return  # Profile exists but no name — incomplete setup

    base_currency = extract_field(text, "Base currency") or "unknown"
    residency = extract_field(text, "Residency")
    role = extract_field(text, "role") or "principal"
    response_style = extract_field(text, "response_style") or "dashboard"
    risk_tolerance = extract_field(text, "Risk tolerance")

    entity_count = count_entities(profile_path)
    session_count = count_sessions(profile_path)
    stage = lifecycle_stage(session_count)

    # Build compact reminder
    lines = [
        "[PostCompact context restore]",
        f"You are the CIO for {name}'s family office.",
        f"Base currency: {base_currency}. Role: {role}. Response style: {response_style}.",
    ]
    if residency:
        lines.append(f"Residency: {residency}.")
    if risk_tolerance:
        lines.append(f"Risk tolerance: {risk_tolerance}.")
    lines.append(f"Entities: {entity_count}. Sessions: {session_count} ({stage} stage).")
    lines.append(
        "Re-read profile.md and entities/ before answering financial questions. "
        "Apply CIO persona from references/timecell.md."
    )

    print(" ".join(lines))


if __name__ == "__main__":
    main()
