import os
import sys
from datetime import datetime

import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FALLBACK_FX_RATES, FX_API_TIMEOUT, FX_API_URL

# In-memory cache: {("2026-01-19", "GBP"): 1.3425}
_rate_cache: dict[tuple[str, str], float] = {}


def get_fx_rate(currency: str, trade_date: str) -> tuple[float, str]:
    """
    Get exchange rate to USD for a given currency and date.

    Returns:
        tuple: (rate, source) where source is 'direct', 'api', 'api_cached', or 'fallback'
    """
    # USD-quoted instruments need no conversion
    if currency == "USD":
        return (1.0, "direct")

    # Normalize date format to YYYY-MM-DD
    normalized_date = normalize_date(trade_date)

    cache_key = (normalized_date, currency)

    # Check cache first
    if cache_key in _rate_cache:
        return (_rate_cache[cache_key], "api_cached")

    # Try API first
    try:
        response = requests.get(
            f"{FX_API_URL}/{normalized_date}", params={"from": currency, "to": "USD"}, timeout=FX_API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            rate = data["rates"]["USD"]
            _rate_cache[cache_key] = rate
            return (rate, "api")
    except Exception:
        pass

    # Fallback to static rate
    if currency in FALLBACK_FX_RATES:
        return (FALLBACK_FX_RATES[currency], "fallback")

    raise ValueError(f"Unknown currency: {currency}. No API rate or fallback available.")


def normalize_date(date_str: str) -> str:
    """
    Normalize date string to YYYY-MM-DD format.
    Handles formats like:
    - 2026.01.19 (MT5)
    - 2026-01-19 (cTrader/standard)
    - 2026/01/19
    """
    if isinstance(date_str, datetime):
        return date_str.strftime("%Y-%m-%d")

    # Replace common separators with dashes
    normalized = str(date_str).replace(".", "-").replace("/", "-")

    # Handle datetime strings (take only the date part)
    if " " in normalized:
        normalized = normalized.split(" ")[0]

    return normalized


def clear_cache():
    """Clear the rate cache (useful for testing)"""
    global _rate_cache
    _rate_cache = {}


def get_cache_stats() -> dict:
    """Return cache statistics"""
    return {
        "cached_rates": len(_rate_cache),
        "currencies": list({key[1] for key in _rate_cache}),
    }
