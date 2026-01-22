# Trading Notional Calculator - Technical Specification

## Overview
A Python-based tool to calculate total notional trading volume (USD) from exported trade history reports. Supports multiple trading platforms including MT5 and cTrader, with extensible architecture for adding more platforms.

---

## Objectives
1. Parse trade history exports from multiple platforms (MT5, cTrader)
2. Auto-detect platform from file structure
3. Calculate notional volume using broker-standard formula
4. Provide breakdown by symbol, date, and month
5. Export results for record-keeping

---

## Supported Platforms

| Platform | File Format | Status |
|----------|-------------|--------|
| MetaTrader 5 (MT5) | .xlsx, .csv | Supported |
| cTrader | .xlsx, .csv | Supported |
| TradingView | .csv | Future |
| Others | — | Extensible |

---

## Formula

```
Notional Volume (USD) = Lots × Contract Size × Close Price × Exchange Rate
```

### Contract Sizes (Standard)

| Symbol Type | Contract Size | Exchange Rate |
|-------------|---------------|---------------|
| XAUUSD | 100 oz | 1 |
| XAGUSD | 5000 oz | 1 |
| Forex (XXX/USD) | 100,000 | 1 |
| Forex (XXX/YYY) | 100,000 | Base currency to USD rate |
| BTCUSD | 1 | 1 |
| ETHUSD | 1 | 1 |
| Indices (US30, NAS100) | 1 | 1 |
| Indices (GER40) | 1 | EURUSD rate |

---

## Multi-Platform Architecture

### Parser Structure

All parsers inherit from a base class and return a standardized DataFrame:

```python
# utils/parsers/base.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseParser(ABC):
    """Base class for all platform parsers"""
    
    @abstractmethod
    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file"""
        pass
    
    @abstractmethod
    def parse(self, filepath: str) -> pd.DataFrame:
        """Parse file and return standardized DataFrame"""
        pass
    
    def get_platform_name(self) -> str:
        """Return platform name for display"""
        pass
```

### Standardized Output Format

All parsers must return a DataFrame with these columns:

| Column | Type | Description |
|--------|------|-------------|
| open_time | datetime | Trade open timestamp |
| close_time | datetime | Trade close timestamp |
| symbol | str | Cleaned symbol (e.g., XAUUSD) |
| type | str | 'buy' or 'sell' |
| lots | float | Position size in lots |
| open_price | float | Entry price |
| close_price | float | Exit price |
| commission | float | Commission charged |
| swap | float | Swap/rollover fee |
| profit | float | Realized P&L |

### Platform Detection

```python
# utils/parsers/__init__.py
from .mt5 import MT5Parser
from .ctrader import CTraderParser

PARSERS = [MT5Parser(), CTraderParser()]

def detect_platform(filepath: str) -> BaseParser:
    """Auto-detect platform from file structure"""
    for parser in PARSERS:
        if parser.can_parse(filepath):
            return parser
    raise ValueError("Unable to detect platform. Please specify manually.")

def get_parser(platform: str) -> BaseParser:
    """Get parser by platform name"""
    parsers = {
        'mt5': MT5Parser(),
        'ctrader': CTraderParser(),
    }
    if platform not in parsers:
        raise ValueError(f"Unknown platform: {platform}")
    return parsers[platform]
```

### MT5 Parser Detection

```python
# utils/parsers/mt5.py
class MT5Parser(BaseParser):
    def can_parse(self, filepath: str) -> bool:
        # Check if first cell contains "Trade History Report"
        df = pd.read_excel(filepath, nrows=1, header=None)
        return df.iloc[0, 0] == "Trade History Report"
    
    def get_platform_name(self) -> str:
        return "MetaTrader 5"
```

### cTrader Parser Detection

```python
# utils/parsers/ctrader.py
class CTraderParser(BaseParser):
    def can_parse(self, filepath: str) -> bool:
        # Check for cTrader-specific columns
        df = pd.read_excel(filepath, nrows=1)
        ctrader_columns = ['Position ID', 'Opening Time', 'Closing Time']
        return any(col in df.columns for col in ctrader_columns)
    
    def get_platform_name(self) -> str:
        return "cTrader"
```

---

## cTrader Report Format

### Expected Columns (may vary by broker)

| Column | Maps To |
|--------|---------|
| Position ID | position_id |
| Symbol | symbol |
| Direction | type |
| Volume | lots |
| Opening Time | open_time |
| Opening Price | open_price |
| Closing Time | close_time |
| Closing Price | close_price |
| Commission | commission |
| Swap | swap |
| Net Profit | profit |

### cTrader Parsing Notes

- Volume may be in units (100,000) instead of lots (1.0) — divide by 100,000
- Direction: "Buy" or "Sell" — normalize to lowercase
- Symbol format may differ (e.g., "XAU/USD" vs "XAUUSD") — clean slashes

---

## Phase 1: CLI Tool

### Input
- Trade history export file (.xlsx or .csv)
- Optional: Platform flag (--platform mt5|ctrader)
- If not specified, auto-detect platform

### Processing
1. Detect or validate platform
2. Load appropriate parser
3. Parse file into standardized DataFrame
4. Extract close date for FX rate lookup
5. Fetch historical FX rates (API with fallback)
6. Apply notional formula per trade
7. Aggregate results

### Output (Console)
```
==========================================
NOTIONAL VOLUME REPORT
==========================================
File: ReportHistory-19301139.xlsx
Platform: MetaTrader 5 (auto-detected)
Period: 2026-01-19 to 2026-01-21
------------------------------------------

TRADE DETAILS:
Symbol     Lots    Close Price    FX Rate   Source     Notional (USD)
----------------------------------------------------------------------
XAUUSD     0.17    4,732.52       1.0000    direct     $80,452.84
BTCUSD     0.05    92,975.46      1.0000    direct     $4,648.77
GBPJPY     0.32    212.06         1.3425    api        $43,040.00
...

SUMMARY BY SYMBOL:
Symbol     Total Lots    Notional (USD)    %
------------------------------------------------
GBPJPY     1.61          $216,545.00       62.2%
XAUUSD     0.19          $89,946.84        25.8%
...

GRAND TOTAL: $347,902.67 USD
==========================================
```

### Output (File)
- `notional_report_YYYYMMDD_HHMMSS.csv`
- `notional_report_YYYYMMDD_HHMMSS.json` (optional)

---

## Phase 2: Web UI

### Technical Stack
- Flask web framework
- Bootstrap 5 for styling
- Pandas for data processing
- Plotly for charts (optional)

### Pages

#### 1. Home / Upload Page
- Platform selector: [Auto-Detect] [MT5] [cTrader]
- Drag & drop file upload area
- Supported formats: .xlsx, .csv
- "Calculate" button

#### 2. Results Page
- Platform badge (e.g., "MetaTrader 5")
- Summary cards (Total Notional, Total Trades, Total Lots)
- Trade-by-trade table (sortable, includes FX Rate and Source)
- Breakdown by symbol (table + pie chart)
- Breakdown by date (if multiple days)
- FX source summary (how many api vs fallback)
- Download buttons (CSV, PDF)

### API Endpoints
```
POST /upload          - Upload file and process
GET  /results/{id}    - Get calculation results
GET  /download/{id}   - Download report (CSV/PDF)
GET  /platforms       - List supported platforms
```

---

## File Structure

```
trading-notional-calculator/
├── app.py                    # Flask application
├── cli.py                    # CLI entry point
├── requirements.txt
├── config.py                 # Contract sizes, FX rates config
├── uploads/                  # Temporary upload storage
├── outputs/                  # Generated reports
├── templates/
│   ├── base.html
│   ├── index.html
│   └── results.html
├── static/
│   ├── css/
│   └── js/
└── utils/
    ├── __init__.py
    ├── parsers/
    │   ├── __init__.py       # Parser registry & auto-detect
    │   ├── base.py           # Abstract base parser
    │   ├── mt5.py            # MT5 parser
    │   └── ctrader.py        # cTrader parser
    ├── calculator.py         # Notional calculation logic
    ├── fx_rates.py           # Exchange rate handling (API + fallback)
    └── report_generator.py   # CSV/PDF export
```

---

## Configuration (config.py)

```python
CONTRACT_SIZES = {
    'XAUUSD': 100,
    'XAGUSD': 5000,
    'BTCUSD': 1,
    'ETHUSD': 1,
    'GER40': 1,
    'US30': 1,
    'NAS100': 1,
    # Forex defaults to 100000
}

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
```

---

## FX Rate Strategy

### Priority Order
1. **Historical API** (frankfurter.app) — fetch rate for trade's close date
2. **Fallback static rates** — if API fails or times out

### Historical FX API (frankfurter.app)

**Why this API:**
- Free, no API key required
- Reliable historical data (ECB rates)
- Simple REST interface

**Endpoint:**
```
GET https://api.frankfurter.app/{date}?from={base}&to=USD

Example:
https://api.frankfurter.app/2026-01-19?from=GBP&to=USD
→ {"amount":1.0,"base":"GBP","date":"2026-01-19","rates":{"USD":1.3425}}
```

**Rate Caching:**
- Cache fetched rates in memory during session
- Same date + currency pair = reuse cached rate
- Reduces API calls for reports with multiple trades on same day

### FX Rate Module (utils/fx_rates.py)

```python
import requests
from datetime import datetime
from config import FALLBACK_FX_RATES, FX_API_URL, FX_API_TIMEOUT

# In-memory cache: {("2026-01-19", "GBP"): 1.3425}
_rate_cache = {}

def get_fx_rate(currency: str, trade_date: str) -> tuple[float, str]:
    """
    Returns (rate, source) where source is 'api' or 'fallback'
    """
    if currency == 'USD':
        return (1.0, 'direct')
    
    cache_key = (trade_date, currency)
    if cache_key in _rate_cache:
        return (_rate_cache[cache_key], 'api_cached')
    
    # Try API first
    try:
        response = requests.get(
            f"{FX_API_URL}/{trade_date}",
            params={"from": currency, "to": "USD"},
            timeout=FX_API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            rate = data["rates"]["USD"]
            _rate_cache[cache_key] = rate
            return (rate, 'api')
    except Exception:
        pass
    
    # Fallback to static rate
    if currency in FALLBACK_FX_RATES:
        return (FALLBACK_FX_RATES[currency], 'fallback')
    
    raise ValueError(f"Unknown currency: {currency}")
```

### Handling Cross Pairs (e.g., GBPJPY)

For GBPJPY, we need GBPUSD rate (not JPYUSD):
1. Extract base currency from symbol (GBP from GBPJPY)
2. Fetch GBPUSD rate for that date
3. Notional = Lots × 100,000 × GBPUSD rate

### Report Transparency

The output report should indicate which FX source was used:

```
TRADE DETAILS:
Symbol     Lots    Close Price    FX Rate    FX Source    Notional (USD)
-------------------------------------------------------------------------
XAUUSD     0.17    4,732.52       1.0000     direct       $80,452.84
GBPJPY     0.32    212.06         1.3425     api          $42,960.00
EURJPY     0.50    162.50         1.0812     fallback     $54,060.00

Note: 'api' = historical rate from frankfurter.app
      'fallback' = static approximate rate (API unavailable)
      'direct' = USD-quoted instrument (no conversion needed)
```

---

## Supported Broker Report Formats

### MT5 (MetaTrader 5)
- Export from: MT5 → History → Right-click → Report
- Format: Excel (.xlsx)
- Header rows: 6
- Key columns: Symbol, Type, Volume, Close Price
- Detection: First cell = "Trade History Report"

**Tested with:**
- Vantage
- Pepperstone
- Fusion Markets
- FP Markets

### cTrader
- Export from: cTrader → History → Export
- Format: Excel (.xlsx) or CSV
- Header rows: 0-1 (varies)
- Key columns: Position ID, Symbol, Direction, Volume, Closing Price
- Detection: Contains "Position ID" column

**Tested with:**
- Pepperstone
- IC Markets
- FxPro

### Adding New Platforms

1. Create `utils/parsers/newplatform.py`
2. Inherit from `BaseParser`
3. Implement `can_parse()`, `parse()`, `get_platform_name()`
4. Register in `utils/parsers/__init__.py`

```python
# Example: utils/parsers/tradingview.py
class TradingViewParser(BaseParser):
    def can_parse(self, filepath: str) -> bool:
        df = pd.read_csv(filepath, nrows=1)
        return 'Trade ID' in df.columns and 'Instrument' in df.columns
    
    def parse(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        # Map columns to standard format
        return standardized_df
    
    def get_platform_name(self) -> str:
        return "TradingView"
```

---

## Edge Cases to Handle

1. **Partial fills** - Sum volumes for same position ID
2. **Pending orders** - Exclude (no close price)
3. **Balance operations** - Exclude (deposits/withdrawals)
4. **Symbol suffixes** - Strip (+, ., /) → XAUUSD+, XAU/USD become XAUUSD
5. **Missing FX rates** - Warn user, use fallback or skip
6. **Empty files** - Show friendly error
7. **Unknown platform** - Prompt user to select manually
8. **cTrader volume in units** - Detect and convert to lots (÷ 100,000)
9. **Different date formats** - Handle both 2026.01.19 and 2026-01-19
10. **Mixed platforms** - Reject (one platform per file)

---

## CLI Usage

```bash
# Auto-detect platform
python cli.py path/to/ReportHistory.xlsx

# Specify platform explicitly
python cli.py path/to/ReportHistory.xlsx --platform mt5
python cli.py path/to/ReportHistory.xlsx --platform ctrader

# With output file
python cli.py path/to/ReportHistory.xlsx -o report.csv

# JSON output
python cli.py path/to/ReportHistory.xlsx --format json

# List supported platforms
python cli.py --list-platforms
```

---

## Web UI Usage

```bash
# Start server
python app.py

# Access at http://localhost:5001
```

### Upload Flow
1. Select platform (or leave as "Auto-Detect")
2. Drag & drop file or click to browse
3. Click "Calculate"
4. View results with charts
5. Download CSV report

---

## Future Enhancements (Out of Scope for MVP)

- Live FX rate fetching with multiple API fallbacks
- Multi-file upload (batch processing)
- Historical tracking database
- Monthly/weekly trend charts
- PDF report with charts
- Email report delivery
- Additional platforms:
  - TradingView
  - TradeStation
  - NinjaTrader
  - Interactive Brokers
- Broker auto-detection within platform (Vantage vs Pepperstone MT5)
- API mode for integration with other tools
