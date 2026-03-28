#!/usr/bin/env python3
"""Fetch exchange rates with 24hr cache. Uses free API, stdlib only."""
import sys
import os
import json
import time
from urllib.request import urlopen, Request
from urllib.error import URLError

CACHE_TTL = 3600  # 1 hour in seconds
API_URL = "https://open.er-api.com/v6/latest/USD"
BTC_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"


def _data_dir(project_dir):
    """Return persistent data directory.

    Checks ${CLAUDE_PLUGIN_DATA} first (Cowork marketplace),
    falls back to <project_dir>/.timecell/ for project-files installs.
    """
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return plugin_data
    return os.path.join(project_dir, ".timecell")


def get_cache_path(project_dir):
    cache_dir = os.path.join(_data_dir(project_dir), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "exchange-rates.json")


def read_cache(cache_path):
    """Read cache if fresh (within TTL). Returns data or None."""
    try:
        with open(cache_path) as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) < CACHE_TTL:
            return data
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None


def fetch_btc_price():
    """Fetch BTC/USD price from CoinGecko."""
    try:
        req = Request(BTC_API_URL, headers={"User-Agent": "TimeCell/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("bitcoin", {}).get("usd")
    except (URLError, OSError):
        return None


def fetch_rates():
    """Fetch live rates from API, including BTC/USD."""
    req = Request(API_URL, headers={"User-Agent": "TimeCell/1.0"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    rates = data.get("rates", {})
    # Add BTC price (USD per 1 BTC)
    btc_price = fetch_btc_price()
    if btc_price:
        rates["BTC"] = btc_price
    return rates


def get_exchange_rates(project_dir="."):
    """Get exchange rates, using cache if fresh."""
    cache_path = get_cache_path(project_dir)

    cached = read_cache(cache_path)
    if cached:
        return cached["rates"]

    try:
        rates = fetch_rates()
        cache_data = {"timestamp": time.time(), "rates": rates, "base": "USD"}
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)
        return rates
    except (URLError, OSError) as e:
        # Fall back to stale cache if available
        try:
            with open(cache_path) as f:
                return json.load(f).get("rates", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {"error": str(e)}


if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "TIMECELL_PROJECT_DIR", "."
    )
    rates = get_exchange_rates(project_dir)
    print(json.dumps(rates, indent=2))
