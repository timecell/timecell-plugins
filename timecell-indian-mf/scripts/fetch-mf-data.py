#!/usr/bin/env python3
"""
Fetch Indian Mutual Fund NAV data from AMFI via mfapi.in.

Primary: mfapi.in (free, zero-config, no API key)
Fallback: manual_input_needed flag

Plugin version for timecell-indian-mf. Cache path: .timecell/indian-mf/mf-nav-data.json
Project dir from TIMECELL_PROJECT_DIR env var or current working directory.

Usage:
    python3 scripts/fetch-mf-data.py                          # fetch all schemes in profile
    python3 scripts/fetch-mf-data.py --scheme-codes 119551,120503  # fetch specific schemes
    python3 scripts/fetch-mf-data.py --no-cache                # skip cache
    python3 scripts/fetch-mf-data.py --list-search "HDFC"      # search schemes by name

Prints JSON to stdout. All network errors handled gracefully.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MFAPI_BASE = "https://api.mfapi.in/mf"
MFAPI_SEARCH = "https://api.mfapi.in/mf/search?q="

CACHE_MAX_AGE_SECONDS = 86400  # 24 hours (NAV updates once daily after market close)
STALE_THRESHOLD_HOURS = 72     # NAV older than 3 days triggers warning
REQUEST_TIMEOUT = 15           # seconds per request
MAX_SCHEMES_PER_FETCH = 50     # safety limit

# Project-dir-aware paths (plugin pattern)
PROJECT_DIR = os.environ.get("TIMECELL_PROJECT_DIR", os.getcwd())
CACHE_DIR = os.path.join(PROJECT_DIR, ".timecell", "indian-mf")
CACHE_FILE = os.path.join(CACHE_DIR, "mf-nav-data.json")

# Profile search paths (Cowork plugin context)
PROFILE_PATHS = [
    os.path.join(PROJECT_DIR, "user", "profile.md"),
    os.path.join(PROJECT_DIR, "memory", "profile.md"),
    os.path.join(PROJECT_DIR, "profile.md"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fetch_json(url, timeout=REQUEST_TIMEOUT):
    """Fetch URL and parse JSON. Returns (data, None) or (None, error_str)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TimeCell/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"Network error: {e.reason}"
    except json.JSONDecodeError:
        return None, "Invalid JSON response"
    except Exception as e:
        return None, str(e)


def read_cache():
    """Read cache file. Returns (data, is_fresh) or (None, False)."""
    try:
        with open(CACHE_FILE, "r") as f:
            cached = json.load(f)
        cached_at = cached.get("_cached_at", 0)
        age = time.time() - cached_at
        if age < CACHE_MAX_AGE_SECONDS:
            cached["cached"] = True
            cached["data_age_hours"] = round(age / 3600, 1)
            return cached, True
        return None, False
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None, False


def write_cache(data):
    """Write data to cache file."""
    try:
        data["_cached_at"] = time.time()
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # Cache write failure is non-fatal


def find_profile():
    """Find profile.md in known locations."""
    for path in PROFILE_PATHS:
        if os.path.exists(path):
            return path
    return None


def extract_scheme_codes_from_profile():
    """Extract MF scheme codes from profile.md.

    Looks for scheme_code fields in the mutual fund holdings section.
    Returns list of scheme code strings.
    """
    profile_path = find_profile()
    if not profile_path:
        return []

    try:
        with open(profile_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return []

    codes = []
    in_mf_section = False
    for line in content.split("\n"):
        line_lower = line.strip().lower()
        # Detect MF holdings section
        if "mutual fund" in line_lower and line.strip().startswith("#"):
            in_mf_section = True
            continue
        if in_mf_section and line.strip().startswith("#") and "mutual fund" not in line_lower:
            in_mf_section = False
            continue
        # Extract scheme codes
        if "scheme_code" in line_lower:
            parts = line.split(":")
            if len(parts) >= 2:
                code = parts[-1].strip().strip('"').strip("'")
                if code and code.isdigit():
                    codes.append(code)
    return codes


def fetch_scheme_nav(scheme_code):
    """Fetch latest NAV for a single scheme.

    Returns dict with scheme_code, scheme_name, nav, date, or error.
    """
    url = f"{MFAPI_BASE}/{scheme_code}/latest"
    data, err = fetch_json(url)

    if err:
        return {"scheme_code": scheme_code, "error": err}

    if not data or "data" not in data:
        return {"scheme_code": scheme_code, "error": "Unexpected response format"}

    meta = data.get("meta", {})
    nav_data = data.get("data", [])

    if not nav_data:
        return {"scheme_code": scheme_code, "error": "No NAV data returned"}

    latest = nav_data[0]

    return {
        "scheme_code": scheme_code,
        "scheme_name": meta.get("scheme_name", "Unknown"),
        "scheme_category": meta.get("scheme_category", ""),
        "scheme_type": meta.get("scheme_type", ""),
        "fund_house": meta.get("fund_house", ""),
        "nav": float(latest.get("nav", 0)),
        "date": latest.get("date", ""),
    }


def fetch_scheme_history(scheme_code, days=365):
    """Fetch historical NAV for return calculation.

    Returns list of {date, nav} entries, most recent first.
    """
    url = f"{MFAPI_BASE}/{scheme_code}"
    data, err = fetch_json(url)

    if err:
        return None, err

    if not data or "data" not in data:
        return None, "Unexpected response format"

    nav_entries = data.get("data", [])

    # mfapi.in returns data sorted most recent first
    # Parse dates and filter to requested window
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    filtered = []
    for entry in nav_entries:
        try:
            nav_date = datetime.strptime(entry["date"], "%d-%m-%Y")
            if nav_date.timestamp() >= cutoff:
                filtered.append({
                    "date": nav_date.strftime("%Y-%m-%d"),
                    "nav": float(entry["nav"]),
                })
        except (ValueError, KeyError):
            continue

    return filtered, None


def search_schemes(query):
    """Search for mutual fund schemes by name.

    Returns list of matching schemes with code and name.
    """
    url = f"{MFAPI_SEARCH}{urllib.request.quote(query)}"
    data, err = fetch_json(url)

    if err:
        return {"results": [], "error": err}

    if not isinstance(data, list):
        return {"results": [], "error": "Unexpected response format"}

    results = []
    for item in data[:20]:  # Limit to 20 results
        results.append({
            "scheme_code": str(item.get("schemeCode", "")),
            "scheme_name": item.get("schemeName", ""),
        })

    return {"results": results, "query": query}


def calculate_returns(history):
    """Calculate 1Y and 3Y returns from NAV history.

    Args:
        history: List of {date, nav} entries, sorted by date descending.

    Returns:
        Dict with return_1y, return_3y (percentages), or None if insufficient data.
    """
    if not history or len(history) < 2:
        return {"return_1y": None, "return_3y": None}

    latest_nav = history[0]["nav"]
    latest_date = datetime.strptime(history[0]["date"], "%Y-%m-%d")

    return_1y = None
    return_3y = None

    # Find NAV closest to 1 year ago
    target_1y = latest_date.timestamp() - (365 * 86400)
    target_3y = latest_date.timestamp() - (3 * 365 * 86400)

    for entry in history:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        entry_ts = entry_date.timestamp()

        if return_1y is None and abs(entry_ts - target_1y) < (7 * 86400):
            return_1y = round(((latest_nav - entry["nav"]) / entry["nav"]) * 100, 2)

        if return_3y is None and abs(entry_ts - target_3y) < (14 * 86400):
            return_3y = round(((latest_nav - entry["nav"]) / entry["nav"]) * 100, 2)

    return {"return_1y": return_1y, "return_3y": return_3y}


def check_staleness(schemes, now):
    """Check if NAV data is stale. Returns (is_stale, warning_message)."""
    for code, scheme in schemes.items():
        nav_date_str = scheme.get("date", "")
        if nav_date_str:
            try:
                nav_date = datetime.strptime(nav_date_str, "%d-%m-%Y")
                age_hours = (now.replace(tzinfo=None) - nav_date).total_seconds() / 3600
                if age_hours > STALE_THRESHOLD_HOURS:
                    return True, f"NAV data is {round(age_hours / 24, 1)} days old. Market may have been closed."
            except ValueError:
                pass
    return False, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    no_cache = "--no-cache" in args
    scheme_codes = []
    search_query = None

    # Parse args
    for i, arg in enumerate(args):
        if arg == "--scheme-codes" and i + 1 < len(args):
            scheme_codes = [c.strip() for c in args[i + 1].split(",") if c.strip()]
        elif arg == "--list-search" and i + 1 < len(args):
            search_query = args[i + 1]

    # Handle search mode
    if search_query:
        result = search_schemes(search_query)
        print(json.dumps(result, indent=2))
        return

    # Check cache first
    if not no_cache:
        cached, is_fresh = read_cache()
        if is_fresh and cached:
            # If specific schemes requested, filter cache
            if scheme_codes:
                cached_schemes = cached.get("schemes", {})
                filtered = {k: v for k, v in cached_schemes.items() if k in scheme_codes}
                if len(filtered) == len(scheme_codes):
                    cached["schemes"] = filtered
                    print(json.dumps(cached, indent=2))
                    return
            else:
                print(json.dumps(cached, indent=2))
                return

    # Get scheme codes from profile if not specified
    if not scheme_codes:
        scheme_codes = extract_scheme_codes_from_profile()

    if not scheme_codes:
        print(json.dumps({
            "schemes": {},
            "manual_input_needed": True,
            "error": "No scheme codes found. Add scheme_code to MF holdings in profile.md or use --scheme-codes.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
        return

    if len(scheme_codes) > MAX_SCHEMES_PER_FETCH:
        scheme_codes = scheme_codes[:MAX_SCHEMES_PER_FETCH]

    # Fetch NAV for each scheme
    schemes = {}
    errors = []
    for code in scheme_codes:
        result = fetch_scheme_nav(code)
        if "error" in result:
            errors.append(result)
        else:
            # Fetch history for return calculation
            history, hist_err = fetch_scheme_history(code, days=365)
            if history:
                returns = calculate_returns(history)
                result.update(returns)
            schemes[code] = result

    # Build output
    now = datetime.now(timezone.utc)
    is_stale, stale_warning = check_staleness(schemes, now)

    output = {
        "schemes": schemes,
        "scheme_count": len(schemes),
        "errors": errors,
        "timestamp": now.isoformat(),
        "cached": False,
        "data_age_hours": 0,
        "stale": is_stale,
        "manual_input_needed": len(schemes) == 0 and len(errors) > 0,
    }

    if stale_warning:
        output["stale_warning"] = stale_warning

    # Write cache
    write_cache(output)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
