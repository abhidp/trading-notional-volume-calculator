# Contract sizes for different instruments
CONTRACT_SIZES = {
    'XAUUSD': 100,       # 100 oz
    'XAGUSD': 5000,      # 5000 oz
    'BTCUSD': 1,
    'ETHUSD': 1,
    'GER40': 1,
    'US30': 1,
    'NAS100': 1,
    'US500': 1,
    'UK100': 1,
    'SPOTCRUDE': 1000,   # 1000 barrels (standard crude oil contract)
    'USOIL': 1000,       # Alternative name for crude oil
    'WTI': 1000,         # WTI crude oil
    'XTIUSD': 1000,      # Another crude oil symbol
}

# Default contract size for forex pairs
DEFAULT_FOREX_CONTRACT_SIZE = 100000

# Static FX rates (FALLBACK ONLY - used when API fails)
FALLBACK_FX_RATES = {
    'GBP': 1.345,
    'EUR': 1.08,
    'AUD': 0.67,
    'JPY': 0.0067,
    'CAD': 0.74,
    'CHF': 1.12,
    'NZD': 0.62,
}

# Historical FX API configuration
FX_API_URL = "https://api.frankfurter.app"
FX_API_TIMEOUT = 5  # seconds
