#!/usr/bin/env python3
"""
Fetch live Bitcoin market data for pack consumption.

Primary: TimeCell hosted API (MVRV + RHODL composite temperature + BTC price)
Fallback 1: CoinGecko (price) + CoinMetrics (MVRV) → MVRV-only temperature
Fallback 2: blockchain.info (price only)
Last resort: manual_input_needed flag

Usage:
    python3 scripts/fetch-btc-data.py                  # USD default
    python3 scripts/fetch-btc-data.py --currency SGD   # local currency
    python3 scripts/fetch-btc-data.py --no-cache        # skip cache

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
TIMECELL_API = "https://timecell.vercel.app/api/temperature"
COINGECKO_PRICE = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,sgd,gbp,eur,aud,inr,hkd"
COINMETRICS_MVRV = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=btc&metrics=CapMVRVCur&frequency=1d&limit=1"
BLOCKCHAIN_INFO = "https://blockchain.info/ticker"

CACHE_MAX_AGE_SECONDS = 3600  # 1 hour
STALE_THRESHOLD_HOURS = 48    # data older than this triggers warning
REQUEST_TIMEOUT = 15          # seconds per request


# ---------------------------------------------------------------------------
# Cache path (project-dir aware)
# ---------------------------------------------------------------------------
def get_cache_path(project_dir):
    cache_dir = os.path.join(project_dir, ".timecell", "bitcoin")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "market-data.json")


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


def read_cache(cache_path, currency="USD"):
    """Read cache file. Returns (data, is_fresh) or (None, False).
    Cache only valid if currency matches."""
    try:
        with open(cache_path, "r") as f:
            cached = json.load(f)
        cached_at = cached.get("_cached_at", 0)
        age = time.time() - cached_at
        if age < CACHE_MAX_AGE_SECONDS and cached.get("currency") == currency:
            cached["cached"] = True
            cached["data_age_hours"] = round(age / 3600, 1)
            return cached, True
        return None, False
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None, False


def write_cache(cache_path, data):
    """Write data to cache file."""
    try:
        to_write = {**data, "_cached_at": time.time()}
        with open(cache_path, "w") as f:
            json.dump(to_write, f, indent=2)
    except OSError:
        pass  # cache write failure is non-fatal


def compute_data_age(timestamp_str):
    """Compute hours since timestamp. Returns (hours, is_stale)."""
    try:
        # Handle ISO format with or without Z
        ts = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return round(age_hours, 1), age_hours > STALE_THRESHOLD_HOURS
    except (ValueError, TypeError):
        return None, True  # can't parse → treat as stale


def get_local_price(coingecko_data, currency):
    """Extract local currency price from CoinGecko response."""
    currency_lower = currency.lower()
    prices = coingecko_data.get("bitcoin", {})
    return prices.get(currency_lower)


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------
def fetch_timecell():
    """Primary: TimeCell API → full temperature + BTC price."""
    data, err = fetch_json(TIMECELL_API)
    if err:
        return None, err
    if not data or "score" not in data:
        return None, "Missing 'score' in response"
    return data, None


def fetch_coingecko_price():
    """Fallback price source: CoinGecko free API."""
    data, err = fetch_json(COINGECKO_PRICE)
    if err:
        return None, err
    prices = data.get("bitcoin", {})
    if "usd" not in prices:
        return None, "Missing USD price"
    return prices, None


def fetch_coinmetrics_mvrv():
    """Fallback MVRV source: CoinMetrics community API."""
    data, err = fetch_json(COINMETRICS_MVRV)
    if err:
        return None, err
    try:
        series = data["data"][0]
        mvrv = float(series["CapMVRVCur"])
        return mvrv, None
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return None, f"Parse error: {e}"


def fetch_blockchain_info():
    """Last-resort price source: blockchain.info."""
    data, err = fetch_json(BLOCKCHAIN_INFO)
    if err:
        return None, err
    if "USD" not in data:
        return None, "Missing USD in response"
    return data, None


# ---------------------------------------------------------------------------
# MVRV-only temperature (no RHODL)
# ---------------------------------------------------------------------------
def mvrv_only_temperature(mvrv):
    """Approximate temperature from MVRV alone (linear scale, no RHODL)."""
    # MVRV ranges: <1 = deep value, 1-2 = fair, 2-3 = warm, 3-4 = hot, >4 = overheated
    if mvrv <= 0.5:
        score = 5
    elif mvrv <= 1.0:
        score = int(10 + (mvrv - 0.5) * 30)  # 10-25
    elif mvrv <= 2.0:
        score = int(25 + (mvrv - 1.0) * 25)  # 25-50
    elif mvrv <= 3.0:
        score = int(50 + (mvrv - 2.0) * 20)  # 50-70
    elif mvrv <= 4.0:
        score = int(70 + (mvrv - 3.0) * 15)  # 70-85
    else:
        score = min(100, int(85 + (mvrv - 4.0) * 10))  # 85-100

    zones = [(30, "COLD"), (50, "COOL"), (60, "NEUTRAL"), (80, "CAUTION"), (95, "GREED")]
    zone = "EXTREME GREED"
    for threshold, z in zones:
        if score <= threshold:
            zone = z
            break

    return {"score": score, "zone": zone, "mvrv": mvrv, "rhodl": None,
            "source": "coinmetrics-fallback"}


# ---------------------------------------------------------------------------
# Main fetch logic
# ---------------------------------------------------------------------------
def fetch_market_data(currency="USD", use_cache=True, project_dir="."):
    """Fetch BTC market data with fallback chain. Returns result dict."""
    cache_path = get_cache_path(project_dir)

    # 1. Check cache
    if use_cache:
        cached, is_fresh = read_cache(cache_path, currency.upper())
        if is_fresh and cached:
            return cached

    result = {
        "btc_price_usd": None,
        "btc_price_local": None,
        "currency": currency.upper(),
        "temperature": None,
        "timestamp": None,
        "cached": False,
        "data_age_hours": None,
        "stale": False,
        "stale_warning": None,
    }

    errors = []

    # 2. Primary: TimeCell API
    tc_data, tc_err = fetch_timecell()
    if tc_data:
        result["btc_price_usd"] = tc_data.get("btcPrice")
        result["timestamp"] = tc_data.get("timestamp")
        result["temperature"] = {
            "score": tc_data.get("score"),
            "zone": tc_data.get("zone"),
            "mvrv": tc_data.get("mvrv"),
            "rhodl": tc_data.get("rhodl"),
            "source": "timecell-api",
        }
    else:
        errors.append(f"TimeCell API: {tc_err}")

    # 3. Multi-currency price via CoinGecko (always try — gives local price)
    cg_prices, cg_err = fetch_coingecko_price()
    if cg_prices:
        # If TimeCell didn't give us a price, use CoinGecko USD
        if result["btc_price_usd"] is None:
            result["btc_price_usd"] = cg_prices.get("usd")
        # Local currency price
        local = cg_prices.get(currency.lower())
        if local:
            result["btc_price_local"] = local
        elif currency.upper() == "USD":
            result["btc_price_local"] = result["btc_price_usd"]
    else:
        errors.append(f"CoinGecko: {cg_err}")
        if currency.upper() == "USD":
            result["btc_price_local"] = result["btc_price_usd"]

    # 4. Fallback: if no temperature yet, try CoinMetrics MVRV
    if result["temperature"] is None:
        mvrv, mvrv_err = fetch_coinmetrics_mvrv()
        if mvrv is not None:
            result["temperature"] = mvrv_only_temperature(mvrv)
            if result["timestamp"] is None:
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
        else:
            errors.append(f"CoinMetrics: {mvrv_err}")

    # 5. Fallback: if still no price or no local price, try blockchain.info
    if result["btc_price_usd"] is None or result["btc_price_local"] is None:
        bi_data, bi_err = fetch_blockchain_info()
        if bi_data:
            if result["btc_price_usd"] is None:
                result["btc_price_usd"] = bi_data.get("USD", {}).get("last")
            if result["btc_price_local"] is None:
                if currency.upper() == "USD":
                    result["btc_price_local"] = result["btc_price_usd"]
                else:
                    local_data = bi_data.get(currency.upper(), {})
                    result["btc_price_local"] = local_data.get("last")
            if result["timestamp"] is None:
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
        else:
            errors.append(f"blockchain.info: {bi_err}")

    # 6. Staleness detection
    if result["timestamp"]:
        age_hours, is_stale = compute_data_age(result["timestamp"])
        result["data_age_hours"] = age_hours
        if is_stale:
            result["stale"] = True
            result["stale_warning"] = (
                f"Temperature data is {age_hours:.0f} hours old — "
                "fo-web sync may have failed"
            )
    else:
        result["data_age_hours"] = None

    # 7. If nothing worked at all
    if result["btc_price_usd"] is None and result["temperature"] is None:
        return {
            "manual_input_needed": True,
            "error": "; ".join(errors) if errors else "All data sources failed",
            "cached": False,
        }

    # 8. Add framework envelope for multi-framework support
    result["framework"] = "bitcoin-conviction"
    result["data"] = {
        "btc_price_usd": result.get("btc_price_usd"),
        "btc_price_local": result.get("btc_price_local"),
        "temperature": result.get("temperature"),
    }

    # 9. Cache and return
    write_cache(cache_path, result)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Bitcoin market data")
    parser.add_argument("--currency", default="USD",
                        help="Local currency code (default: USD)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Skip cache, fetch fresh data")
    args = parser.parse_args()

    project_dir = os.environ.get("TIMECELL_PROJECT_DIR", ".")
    data = fetch_market_data(
        currency=args.currency.upper(),
        use_cache=not args.no_cache,
        project_dir=project_dir,
    )
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
