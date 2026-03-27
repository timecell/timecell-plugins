#!/usr/bin/env python3
"""Increment the session counter. Creates file if missing."""
import sys
import os


def increment_session_count(project_dir="."):
    """Increment session count and return new value."""
    tc_dir = os.path.join(project_dir, ".timecell")
    os.makedirs(tc_dir, exist_ok=True)
    count_file = os.path.join(tc_dir, "session-count.txt")

    try:
        with open(count_file) as f:
            count = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        count = 0

    count += 1
    with open(count_file, "w") as f:
        f.write(str(count))

    print(f"session_count: {count}")
    return count


if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "TIMECELL_PROJECT_DIR", "."
    )
    increment_session_count(project_dir)
