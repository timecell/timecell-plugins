#!/usr/bin/env python3
"""
Fetch Zerodha/Kite Connect data for indian-mf plugin consumption.

Fetches equity holdings, MF holdings, positions, and SIP details
via Kite Connect API v3.

Plugin version for timecell-indian-mf. Cache path: .timecell/indian-mf/zerodha-data.json
Project dir from TIMECELL_PROJECT_DIR env var or current working directory.

Usage:
    python3 scripts/fetch-zerodha-data.py                          # fetch all
    python3 scripts/fetch-zerodha-data.py --no-cache                # skip cache
    python3 scripts/fetch-zerodha-data.py --holdings-only           # equity + MF only
    python3 scripts/fetch-zerodha-data.py --mf-only                 # MF + SIPs only
    python3 scripts/fetch-zerodha-data.py --auth-help               # daily token setup
    python3 scripts/fetch-zerodha-data.py --exchange-token <token>  # exchange request_token

Prints JSON to stdout. All network errors handled gracefully.
Credentials: ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_ACCESS_TOKEN (env vars).
Access token expires daily at 6 AM IST (exchange regulation).
Rate limit: 3 requests/second per API key.
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
KITE_API_BASE = "https://api.kite.trade"
CACHE_MAX_AGE_SECONDS = 3600  # 1 hour
STALE_THRESHOLD_HOURS = 48
REQUEST_TIMEOUT = 15
RATE_LIMIT_DELAY = 0.34  # ~3 requests/second

# Project-dir-aware paths (plugin pattern)
PROJECT_DIR = os.environ.get("TIMECELL_PROJECT_DIR", os.getcwd())
CACHE_DIR = os.path.join(PROJECT_DIR, ".timecell", "indian-mf")
CACHE_FILE = os.path.join(CACHE_DIR, "zerodha-data.json")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def get_credentials():
    """Read credentials from env vars. Returns (api_key, api_secret, access_token)."""
    api_key = os.environ.get("ZERODHA_API_KEY")
    api_secret = os.environ.get("ZERODHA_API_SECRET")
    access_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
    return api_key, api_secret, access_token


def exchange_token(api_key, api_secret, request_token):
    """Exchange request_token for access_token via Kite Connect API.

    Args:
        api_key: Permanent Kite Connect API key
        api_secret: Permanent Kite Connect API secret
        request_token: Single-use token from login redirect

    Returns:
        dict with access_token, user_id, email on success

    Raises:
        ValueError on exchange failure
    """
    checksum = hashlib.sha256(
        (api_key + request_token + api_secret).encode("utf-8")
    ).hexdigest()

    payload = json.dumps({
        "api_key": api_key,
        "request_token": request_token,
        "checksum": checksum,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{KITE_API_BASE}/session/token",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Kite-Version": "3",
            "User-Agent": "TimeCell/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode())
        data = result.get("data", result)
        if "access_token" not in data:
            raise ValueError("No access_token in response")
        return data
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise ValueError(f"Token exchange failed (HTTP {e.code}): {body}")
    except urllib.error.URLError as e:
        raise ValueError(f"Network error during token exchange: {e.reason}")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def kite_get(endpoint, api_key, access_token):
    """GET from Kite API. Returns (data, None) or (None, error_str)."""
    url = f"{KITE_API_BASE}{endpoint}"
    auth = f"token {api_key}:{access_token}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": auth,
            "X-Kite-Version": "3",
            "User-Agent": "TimeCell/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode())
        if result.get("status") == "error":
            return None, result.get("message", "API error")
        return result.get("data", result), None
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, "TokenException: Access token expired or invalid"
        if e.code == 429:
            return None, "RateLimited: Too many requests"
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"Network error: {e.reason}"
    except json.JSONDecodeError:
        return None, "Invalid JSON response"
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
def detect_plan(fund_name):
    """Detect if MF scheme is direct or regular plan from fund name."""
    if re.search(r'\bDirect\b', fund_name, re.IGNORECASE):
        return "direct"
    return "regular"


def normalize_scheme_name(fund_name):
    """Strip plan/growth/dividend suffixes for clean scheme name."""
    name = fund_name
    # Strip trailing " - Direct Plan - Growth", " - Regular - Growth", etc.
    name = re.sub(
        r'\s*-\s*(Direct\s+Plan|Regular\s+Plan|Direct|Regular)\s*-\s*(Growth|Dividend|IDCW)(\s+Plan)?$',
        '', name, flags=re.IGNORECASE
    )
    # Strip standalone plan suffixes
    name = re.sub(r'\s*-\s*(Direct\s+Plan|Regular\s+Plan)$', '', name, flags=re.IGNORECASE)
    # Strip standalone growth/dividend
    name = re.sub(r'\s*-\s*(Growth|Dividend|IDCW)(\s+Plan)?$', '', name, flags=re.IGNORECASE)
    return name.strip()


def normalize_mf_holding(kite_mf):
    """Normalize a Kite Connect MF holding to indian-mf schema."""
    fund = kite_mf.get("fund", kite_mf.get("tradingsymbol", "Unknown"))
    quantity = float(kite_mf.get("quantity", 0))
    avg_price = float(kite_mf.get("average_price", 0))
    last_price = float(kite_mf.get("last_price", 0))
    pnl = kite_mf.get("pnl")
    if pnl is None and avg_price > 0:
        pnl = round((last_price - avg_price) * quantity, 2)
    else:
        pnl = float(pnl) if pnl is not None else 0.0

    return {
        "fund": fund,
        "tradingsymbol": kite_mf.get("tradingsymbol", ""),
        "folio": kite_mf.get("folio"),
        "quantity": quantity,
        "average_price": avg_price,
        "last_price": last_price,
        "last_price_date": kite_mf.get("last_price_date", datetime.now().strftime("%Y-%m-%d")),
        "pnl": round(pnl, 2),
        "scheme_name_normalized": normalize_scheme_name(fund),
        "plan_detected": detect_plan(fund),
        "current_value": round(last_price * quantity, 2),
        "invested_amount": round(avg_price * quantity, 2),
    }


def normalize_equity_holding(kite_holding):
    """Normalize a Kite Connect equity holding."""
    quantity = int(kite_holding.get("quantity", 0))
    avg_price = float(kite_holding.get("average_price", 0))
    last_price = float(kite_holding.get("last_price", 0))
    close_price = float(kite_holding.get("close_price", 0))
    pnl = kite_holding.get("pnl")
    if pnl is None:
        pnl = round((last_price - avg_price) * quantity, 2)
    else:
        pnl = float(pnl)

    day_change_pct = 0.0
    if close_price > 0:
        day_change_pct = round((last_price - close_price) / close_price * 100, 2)

    return {
        "tradingsymbol": kite_holding.get("tradingsymbol", ""),
        "exchange": kite_holding.get("exchange", "NSE"),
        "isin": kite_holding.get("isin", ""),
        "quantity": quantity,
        "average_price": avg_price,
        "last_price": last_price,
        "close_price": close_price,
        "pnl": round(pnl, 2),
        "day_change_pct": day_change_pct,
    }


def normalize_position(kite_pos):
    """Normalize a Kite Connect position."""
    return {
        "tradingsymbol": kite_pos.get("tradingsymbol", ""),
        "exchange": kite_pos.get("exchange", ""),
        "product": kite_pos.get("product", ""),
        "quantity": int(kite_pos.get("quantity", 0)),
        "average_price": float(kite_pos.get("average_price", 0)),
        "last_price": float(kite_pos.get("last_price", 0)),
        "pnl": float(kite_pos.get("pnl", 0)),
        "overnight_quantity": int(kite_pos.get("overnight_quantity", 0)),
    }


def normalize_sip(kite_sip):
    """Normalize a Kite Connect SIP."""
    return {
        "sip_id": str(kite_sip.get("sip_id", "")),
        "fund": kite_sip.get("fund", kite_sip.get("tradingsymbol", "")),
        "tradingsymbol": kite_sip.get("tradingsymbol", ""),
        "frequency": kite_sip.get("frequency", "monthly"),
        "instalment_amount": float(kite_sip.get("instalment_amount", 0)),
        "status": kite_sip.get("status", "unknown"),
        "next_instalment": kite_sip.get("next_instalment_date", kite_sip.get("next_instalment")),
        "completed_instalments": int(kite_sip.get("completed_instalments", 0)),
    }


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
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
    """Write data to cache file. Never includes credentials."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_data = dict(data)
        cache_data["_cached_at"] = time.time()
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main fetch logic
# ---------------------------------------------------------------------------
def build_auth_error_response(message):
    """Build a graceful auth error response."""
    return {
        "plugin": "indian-mf",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "manual_input_needed": True,
        "auth_error": message,
        "data": {
            "equity_holdings": [],
            "mf_holdings": [],
            "positions": [],
            "sips": [],
            "summary": None,
        },
    }


def fetch_all(api_key, access_token, holdings_only=False, mf_only=False):
    """Fetch all Zerodha data. Returns result dict."""
    result_data = {
        "equity_holdings": [],
        "mf_holdings": [],
        "positions": [],
        "sips": [],
        "summary": None,
    }
    errors = []

    # Equity holdings
    if not mf_only:
        eq_data, eq_err = kite_get("/portfolio/holdings", api_key, access_token)
        if eq_err:
            if "TokenException" in str(eq_err):
                return None, eq_err
            errors.append(f"Equity: {eq_err}")
        elif eq_data:
            holdings_list = eq_data if isinstance(eq_data, list) else []
            for h in holdings_list:
                try:
                    result_data["equity_holdings"].append(normalize_equity_holding(h))
                except (KeyError, TypeError, ValueError):
                    errors.append(f"Skipped malformed equity holding: {h.get('tradingsymbol', 'unknown')}")
        time.sleep(RATE_LIMIT_DELAY)

    # MF holdings
    mf_data, mf_err = kite_get("/mf/holdings", api_key, access_token)
    if mf_err:
        if "TokenException" in str(mf_err):
            return None, mf_err
        errors.append(f"MF: {mf_err}")
    elif mf_data:
        mf_list = mf_data if isinstance(mf_data, list) else []
        for h in mf_list:
            try:
                result_data["mf_holdings"].append(normalize_mf_holding(h))
            except (KeyError, TypeError, ValueError):
                errors.append(f"Skipped malformed MF holding: {h.get('fund', 'unknown')}")
    time.sleep(RATE_LIMIT_DELAY)

    # Positions (skip if holdings-only or mf-only)
    if not holdings_only and not mf_only:
        pos_data, pos_err = kite_get("/portfolio/positions", api_key, access_token)
        if pos_err:
            if "TokenException" in str(pos_err):
                return None, pos_err
            errors.append(f"Positions: {pos_err}")
        elif pos_data:
            net_positions = pos_data.get("net", pos_data) if isinstance(pos_data, dict) else pos_data
            if isinstance(net_positions, list):
                for p in net_positions:
                    try:
                        result_data["positions"].append(normalize_position(p))
                    except (KeyError, TypeError, ValueError):
                        pass
        time.sleep(RATE_LIMIT_DELAY)

    # SIPs (fetch if not holdings-only without mf)
    if not holdings_only or mf_only:
        sip_data, sip_err = kite_get("/mf/sips", api_key, access_token)
        if sip_err:
            if "TokenException" in str(sip_err):
                return None, sip_err
            errors.append(f"SIPs: {sip_err}")
        elif sip_data:
            sip_list = sip_data if isinstance(sip_data, list) else []
            for s in sip_list:
                try:
                    result_data["sips"].append(normalize_sip(s))
                except (KeyError, TypeError, ValueError):
                    pass

    # Summary
    eq_total = sum(h["last_price"] * h["quantity"] for h in result_data["equity_holdings"])
    mf_total = sum(h["current_value"] for h in result_data["mf_holdings"])
    active_sips = [s for s in result_data["sips"] if s.get("status") == "active"]
    sip_monthly = sum(s["instalment_amount"] for s in active_sips)

    result_data["summary"] = {
        "equity_holdings_count": len(result_data["equity_holdings"]),
        "equity_total_value": round(eq_total, 2),
        "mf_holdings_count": len(result_data["mf_holdings"]),
        "mf_total_value": round(mf_total, 2),
        "active_sips": len(active_sips),
        "monthly_sip_total": round(sip_monthly, 2),
    }

    return result_data, None


def fetch_zerodha_data(use_cache=True, holdings_only=False, mf_only=False):
    """Main entry: fetch Zerodha data with cache and graceful degradation."""
    # Check cache first
    if use_cache:
        cached, is_fresh = read_cache()
        if is_fresh and cached:
            return cached

    # Check credentials
    api_key, api_secret, access_token = get_credentials()

    if not api_key:
        return build_auth_error_response(
            "Zerodha credentials not configured. "
            "Run: python3 scripts/fetch-zerodha-data.py --auth-help"
        )

    if not access_token:
        return build_auth_error_response(
            "Access token not set. Kite Connect requires daily login. "
            "Run: python3 scripts/fetch-zerodha-data.py --auth-help"
        )

    # Fetch data
    data, err = fetch_all(api_key, access_token, holdings_only, mf_only)

    if err and "TokenException" in str(err):
        return build_auth_error_response(
            "Access token expired (expires daily at 6 AM IST). "
            "Run: python3 scripts/fetch-zerodha-data.py --auth-help"
        )

    if data is None:
        return {
            "plugin": "indian-mf",
            "manual_input_needed": True,
            "error": f"All Zerodha endpoints failed: {err}",
            "cached": False,
        }

    now = datetime.now(timezone.utc)
    result = {
        "plugin": "indian-mf",
        "timestamp": now.isoformat(),
        "cached": False,
        "stale": False,
        "data_age_hours": 0.0,
        "data": data,
    }

    # Write cache
    write_cache(result)
    return result


# ---------------------------------------------------------------------------
# Auth help
# ---------------------------------------------------------------------------
AUTH_HELP_TEXT = """Zerodha/Kite Connect Daily Setup
================================

Kite Connect requires a daily login (exchange regulation -- NSE/BSE mandate).
Your API key and secret are permanent. Only the access token needs daily refresh.

ONE-TIME SETUP (do once):
  1. Sign up at https://developers.kite.trade/ (costs Rs 2000/month)
  2. Create an app, note your API key and API secret
  3. Set redirect URL to any URL you control (e.g., http://localhost:8000)
  4. Export permanently:
     export ZERODHA_API_KEY=your_api_key
     export ZERODHA_API_SECRET=your_api_secret

DAILY REFRESH (do each morning):
  1. Open: https://kite.zerodha.com/connect/login?v=3&api_key=YOUR_KEY
  2. Log in with your Zerodha credentials
  3. After redirect, copy the request_token from the URL parameter
  4. Run: python3 scripts/fetch-zerodha-data.py --exchange-token <request_token>
  5. Export: export ZERODHA_ACCESS_TOKEN=<returned_token>

Then fetch your data:
  python3 scripts/fetch-zerodha-data.py
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Zerodha/Kite Connect data")
    parser.add_argument("--no-cache", action="store_true",
                        help="Skip cache, fetch fresh data")
    parser.add_argument("--holdings-only", action="store_true",
                        help="Equity + MF holdings only (skip positions + SIPs)")
    parser.add_argument("--mf-only", action="store_true",
                        help="MF holdings + SIPs only")
    parser.add_argument("--auth-help", action="store_true",
                        help="Print daily token setup instructions")
    parser.add_argument("--exchange-token", type=str, default=None,
                        help="Exchange request_token for access_token")
    args = parser.parse_args()

    if args.auth_help:
        print(AUTH_HELP_TEXT)
        return

    if args.exchange_token:
        api_key, api_secret, _ = get_credentials()
        if not api_key or not api_secret:
            print(json.dumps({
                "error": "ZERODHA_API_KEY and ZERODHA_API_SECRET must be set. Run --auth-help."
            }))
            sys.exit(1)
        try:
            result = exchange_token(api_key, api_secret, args.exchange_token)
            token = result.get("access_token", "")
            print(f"Access token: {token}")
            print(f"\nExport it:\n  export ZERODHA_ACCESS_TOKEN={token}")
        except ValueError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
        return

    data = fetch_zerodha_data(
        use_cache=not args.no_cache,
        holdings_only=args.holdings_only,
        mf_only=args.mf_only,
    )
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
