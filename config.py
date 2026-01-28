# Contract sizes for different instruments
CONTRACT_SIZES = {
    # Precious metals
    "XAUUSD": 100,  # 100 oz
    "XAGUSD": 5000,  # 5000 oz
    # Crypto
    "BTCUSD": 1,
    "ETHUSD": 1,
    # Indices (contract size = 1, i.e. 1 CFD = index value)
    "GER40": 1,  # DAX
    "GER30": 1,  # DAX (legacy)
    "US30": 1,  # Dow Jones
    "DJ30": 1,  # Dow Jones
    "NAS100": 1,  # Nasdaq 100
    "USTEC": 1,  # Nasdaq 100
    "US500": 1,  # S&P 500
    "SPX500": 1,  # S&P 500
    "SP500": 1,  # S&P 500
    "UK100": 1,  # FTSE 100
    "FTSE100": 1,  # FTSE 100
    "EU50": 1,  # Euro Stoxx 50
    "STOXX50": 1,  # Euro Stoxx 50
    "FRA40": 1,  # CAC 40
    "JPN225": 1,  # Nikkei 225
    "AUS200": 1,  # ASX 200
    "HK50": 1,  # Hang Seng
    "CHINA50": 1,  # China A50
    "SPA35": 1,  # IBEX 35
    "NETH25": 1,  # AEX 25
    "SWI20": 1,  # SMI 20
    "CAN60": 1,  # S&P/TSX 60
    "CHINAH": 1,  # Hang Seng China Enterprises
    "SING30": 1,  # SGX 30
    "SAFR40": 1,  # South Africa Top 40
    "US2000": 1,  # Russell 2000
    "VIX": 1,  # Volatility Index
    # Crude oil (1000 barrels)
    "SPOTCRUDE": 1000,
    "USOIL": 1000,
    "WTI": 1000,
    "XTIUSD": 1000,
    "BRENT": 1000,
    "XBRUSD": 1000,
    # Natural gas
    "NATGAS": 10000,
    "XNGUSD": 10000,
}

# Default contract size for forex pairs
DEFAULT_FOREX_CONTRACT_SIZE = 100000

# Static FX rates (FALLBACK ONLY - used when API fails)
FALLBACK_FX_RATES = {
    "GBP": 1.345,
    "EUR": 1.08,
    "AUD": 0.67,
    "JPY": 0.0067,
    "CAD": 0.74,
    "CHF": 1.12,
    "NZD": 0.62,
}

# Historical FX API configuration
FX_API_URL = "https://api.frankfurter.app"
FX_API_TIMEOUT = 5  # seconds
