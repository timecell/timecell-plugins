#!/usr/bin/env python3
"""Create a backup of a file before mutation. Safety net for data writes."""
import sys
import os
import shutil
from datetime import datetime

PROTECTED_PATTERNS = ["profile.md", "entities/", "memory/", "snapshots/", "decisions/"]


def should_backup(file_path):
    """Only backup files in protected user data locations."""
    normalized = os.path.abspath(file_path).replace("\\", "/")
    return any(pattern in normalized for pattern in PROTECTED_PATTERNS)


def find_project_root(file_path):
    """Walk up from file to find project root (has .timecell/ or profile.md)."""
    current = os.path.dirname(os.path.abspath(file_path))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, ".timecell")):
            return current
        if os.path.exists(os.path.join(current, "profile.md")):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.abspath(file_path))


def snapshot_before_write(file_path):
    """Backup file before write. Returns backup path or None."""
    if not os.path.exists(file_path):
        return None

    if not should_backup(file_path):
        return None

    project_dir = find_project_root(file_path)
    backup_dir = os.path.join(project_dir, ".timecell", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    basename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{timestamp}-{basename}")

    shutil.copy2(file_path, backup_path)
    print(f"Backup: {backup_path}")
    return backup_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: snapshot-before-write.py <file-path>", file=sys.stderr)
        sys.exit(1)
    snapshot_before_write(sys.argv[1])
    sys.exit(0)
