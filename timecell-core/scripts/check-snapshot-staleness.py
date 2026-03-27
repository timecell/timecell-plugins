#!/usr/bin/env python3
"""Check if the latest snapshot is stale (>7 days old)."""
import sys
import os
import json
import re
from datetime import datetime


def check_staleness(project_dir="."):
    """Check snapshot staleness. Returns dict with stale status."""
    snapshots_dir = os.path.join(project_dir, "snapshots")

    if not os.path.exists(snapshots_dir):
        return {"stale": True, "last_snapshot": None, "days_since": None, "reason": "no snapshots directory"}

    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
    dates = []
    for f in os.listdir(snapshots_dir):
        m = date_pattern.match(f)
        if m:
            try:
                dates.append(datetime.strptime(m.group(1), "%Y-%m-%d"))
            except ValueError:
                pass

    if not dates:
        return {"stale": True, "last_snapshot": None, "days_since": None, "reason": "no snapshot files"}

    latest = max(dates)
    days_since = (datetime.now() - latest).days

    return {
        "stale": days_since > 7,
        "last_snapshot": latest.strftime("%Y-%m-%d"),
        "days_since": days_since,
    }


if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "TIMECELL_PROJECT_DIR", "."
    )
    result = check_staleness(project_dir)
    print(json.dumps(result))
