# Claude Code Prompt - Trading Notional Calculator

---

## Full Build Prompt

---

Build a Python tool to calculate notional trading volume (USD) from exported trade history reports. Support multiple platforms (MT5, cTrader) with auto-detection. Split into 2 phases.

## PHASE 1: CLI Tool with Multi-Platform Support

Create a Python CLI script that:

1. **Supports multiple trading platforms:**
   - MetaTrader 5 (MT5)
   - cTrader
   - Auto-detect platform from file structure

2. **Parser architecture:**
   
   Create `utils/parsers/base.py`:
   ```python
   from abc import ABC, abstractmethod
   import pandas as pd
   
   class BaseParser(ABC):
       @abstractmethod
       def can_parse(self, filepath: str) -> bool:
           pass
       
       @abstractmethod
       def parse(self, filepath: str) -> pd.DataFrame:
           pass
       
       def get_platform_name(self) -> str:
           pass
   ```
   
   Create `utils/parsers/mt5.py`:
   - Detection: First cell = "Trade History Report"
   - Skip 6 header rows
   - Extract: Symbol, Type, Volume, Close Price, Close Time
   
   Create `utils/parsers/ctrader.py`:
   - Detection: Has "Position ID" column
   - Volume may be in units (100,000) — convert to lots
   - Symbol may have slashes (XAU/USD) — clean them
   
   Create `utils/parsers/__init__.py`:
   - PARSERS list with all parser instances
   - `detect_platform(filepath)` function
   - `get_parser(platform_name)` function

3. **Standardized DataFrame output from all parsers:**
   Columns: open_time, close_time, symbol, type, lots, open_price, close_price, commission, swap, profit

4. **Calculates notional volume using this formula:**
   ```
   Notional (USD) = Lots × Contract Size × Close Price × Exchange Rate
   ```
   
   Contract sizes:
   - XAUUSD: 100
   - XAGUSD: 5000
   - BTCUSD, ETHUSD: 1
   - Forex pairs: 100,000
   - Indices (GER40, US30, NAS100): 1
   
   **Exchange rates - use this priority:**
   
   a) **Historical API (Primary):** Fetch rate for trade's close date from frankfurter.app
      ```
      GET https://api.frankfurter.app/2026-01-19?from=GBP&to=USD
      → {"rates": {"USD": 1.3425}}
      ```
   
   b) **Fallback static rates (if API fails):**
      - GBP to USD: 1.345
      - EUR to USD: 1.08
      - AUD to USD: 0.67
   
   **Important:** Cache API responses in memory. Multiple trades on same day should reuse the cached rate.

5. **Track FX source for each trade:**
   - 'direct' = USD-quoted instrument (rate = 1)
   - 'api' = fetched from frankfurter.app
   - 'api_cached' = reused from cache
   - 'fallback' = static rate (API failed)

6. **CLI arguments:**
   ```
   python cli.py <filepath> [--platform mt5|ctrader] [-o output.csv] [--format csv|json]
   ```
   - If --platform not provided, auto-detect
   - If auto-detect fails, show error with supported platforms

7. **Outputs:**
   - Console: Platform detected, trade-by-trade breakdown (include FX rate + source columns) + summary by symbol + grand total
   - File: CSV export with all details including FX source
   - Note at bottom indicating if any fallback rates were used

8. **Error handling:**
   - Invalid file path
   - Unsupported format
   - Unknown platform (prompt to specify)
   - Missing required columns
   - API failures (use fallback gracefully)

## PHASE 2: Web UI

Create a Flask web app that:

1. **Upload page:**
   - Title: "Trading Notional Volume Calculator"
   - Platform selector dropdown: [Auto-Detect] [MT5] [cTrader]
   - Drag & drop file upload (or click to browse)
   - Accept .xlsx and .csv files
   - "Calculate" button

2. **Results page:**
   - Platform badge showing detected/selected platform
   - Summary cards: Total Notional, Total Trades, Total Lots
   - Trade-by-trade table (sortable) with FX Rate and Source columns
   - Summary by symbol table with percentage
   - Pie chart showing symbol distribution (use Plotly)
   - FX source summary (X trades API, Y trades fallback)
   - Download button (CSV export)

3. **Styling:**
   - Bootstrap 5
   - Clean, professional look
   - Mobile responsive
   - Platform badges: MT5 = blue, cTrader = green

## File Structure
```
trading-notional-calculator/
├── app.py
├── cli.py
├── config.py
├── requirements.txt
├── uploads/
├── outputs/
├── templates/
│   ├── base.html
│   ├── index.html
│   └── results.html
├── static/
│   └── css/
└── utils/
    ├── __init__.py
    ├── parsers/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── mt5.py
    │   └── ctrader.py
    ├── calculator.py
    ├── fx_rates.py
    └── report_generator.py
```

Start with Phase 1. Test with both MT5 and cTrader files. Then proceed to Phase 2.

---

## Phased Prompts (Alternative)

---

### Prompt 1A - Base Parser Architecture
```
Create a multi-platform parser architecture:

1. Create utils/parsers/base.py:
   - Abstract BaseParser class with methods:
     - can_parse(filepath) -> bool
     - parse(filepath) -> pd.DataFrame
     - get_platform_name() -> str

2. Create utils/parsers/mt5.py:
   - MT5Parser class inheriting BaseParser
   - can_parse(): Check if first cell = "Trade History Report"
   - parse(): Skip 6 header rows, extract Symbol, Type, Volume, Close Price, Close Time
   - Clean symbol names (remove + suffix)

3. Create utils/parsers/ctrader.py:
   - CTraderParser class inheriting BaseParser
   - can_parse(): Check for "Position ID" column
   - parse(): Handle cTrader column names, convert volume if in units
   - Clean symbol names (remove / slashes)

4. Create utils/parsers/__init__.py:
   - PARSERS = [MT5Parser(), CTraderParser()]
   - detect_platform(filepath) function
   - get_parser(platform_name) function

All parsers return standardized DataFrame with columns:
open_time, close_time, symbol, type, lots, open_price, close_price, commission, swap, profit

Use pandas and openpyxl.
```

---

### Prompt 1B - Notional Calculator with Historical FX Rates
```
Extend the script to calculate notional volume:

Formula: Lots × Contract Size × Close Price × Exchange Rate

Create config.py with:
- CONTRACT_SIZES dict (XAUUSD: 100, XAGUSD: 5000, BTCUSD: 1, ETHUSD: 1, Forex default: 100000, Indices: 1)
- FALLBACK_FX_RATES dict (GBP: 1.345, EUR: 1.08, AUD: 0.67)
- FX_API_URL = "https://api.frankfurter.app"

Create utils/fx_rates.py with:
- In-memory cache dict for rates
- get_fx_rate(currency, trade_date) function that:
  1. Returns (1.0, 'direct') if currency is USD
  2. Checks cache first, returns (rate, 'api_cached') if found
  3. Tries frankfurter.app API: GET /{date}?from={currency}&to=USD
  4. On success: cache the rate, return (rate, 'api')
  5. On failure: return (FALLBACK_RATE, 'fallback')
- Use 5 second timeout for API calls

Calculate notional for each trade:
- Extract close date from close_time column
- Determine base currency (GBP from GBPJPY, EUR from EURUSD)
- Get FX rate using get_fx_rate()
- Track which source was used (api/fallback/direct)
- Apply formula

Output:
- Trade-by-trade table with FX Rate, FX Source, and Notional columns
- Summary by symbol
- Grand total in USD
- Warning if any fallback rates were used
```

---

### Prompt 1C - CLI Interface with Platform Selection
```
Convert the script to a proper CLI tool:

Usage:
  python cli.py <filepath> [--platform mt5|ctrader] [-o output.csv] [--format csv|json]
  python cli.py --list-platforms

Features:
- argparse for argument handling
- --platform flag (optional, auto-detect if not provided)
- --list-platforms to show supported platforms
- Validate file exists and is .xlsx or .csv
- Export results to CSV or JSON
- Show detected platform in output
- Pretty console output with formatting
- Error handling with user-friendly messages
```

---

### Prompt 2A - Flask Upload Page with Platform Selector
```
Create a Flask app with an upload page:

1. Home page (/) with:
   - Title: "Trading Notional Volume Calculator"
   - Platform dropdown: [Auto-Detect] [MT5] [cTrader]
   - Drag & drop file upload zone
   - "Calculate" button
   - Accepts .xlsx and .csv files

2. File handling:
   - Save uploaded file to uploads/ directory
   - Get selected platform from form
   - Auto-detect if "Auto-Detect" selected
   - Process using the calculator from Phase 1
   - Redirect to results page

Use Bootstrap 5 for styling.
```

---

### Prompt 2B - Results Page
```
Add a results page to the Flask app:

1. Display platform badge (e.g., "MetaTrader 5" in blue, "cTrader" in green)

2. Summary cards:
   - Total Notional Volume (USD)
   - Total Trades
   - Total Lots

3. Trade-by-trade table:
   - Columns: Symbol, Type, Lots, Close Price, FX Rate, FX Source, Notional
   - Sortable headers
   - Zebra striping

4. Summary by symbol table:
   - Columns: Symbol, Total Lots, Total Notional, Percentage
   - Sorted by notional descending

5. FX Source summary:
   - "X trades used historical API rates"
   - "Y trades used fallback rates" (if any, show warning)

6. Download CSV button

Use Bootstrap 5 tables and cards.
```

---

### Prompt 2C - Charts
```
Add a pie chart to the results page:

1. Use Plotly.js
2. Show notional volume distribution by symbol
3. Interactive hover showing exact values
4. Responsive sizing

Also add a bar chart showing notional by symbol.
```

---

## Sample Test Data

### MT5 Format
```csv
Open Time,Position,Symbol,Type,Volume,Open Price,S/L,T/P,Close Time,Close Price,Commission,Swap,Profit
2026.01.19 06:05:41,8110098,XAUUSD+,buy,0.17,4727.21,0,0,2026.01.19 12:47:19,4732.52,0,0,134.02
2026.01.19 06:23:01,8110107,BTCUSD,buy,0.05,92565.26,0,0,2026.01.19 12:05:14,92975.46,0,0,30.62
2026.01.19 13:45:26,8116866,GBPJPY+,buy,0.32,211.909,0,0,2026.01.19 17:28:13,212.065,0,0,47.08
```

### cTrader Format
```csv
Position ID,Symbol,Direction,Volume,Opening Time,Opening Price,Closing Time,Closing Price,Commission,Swap,Net Profit
12345678,XAU/USD,Buy,17000,2026-01-19 06:05:41,4727.21,2026-01-19 12:47:19,4732.52,0,0,134.02
12345679,BTC/USD,Buy,5000,2026-01-19 06:23:01,92565.26,2026-01-19 12:05:14,92975.46,0,0,30.62
12345680,GBP/JPY,Buy,32000,2026-01-19 13:45:26,211.909,2026-01-19 17:28:13,212.065,0,0,47.08
```

Note: cTrader volume is in units (17000 = 0.17 lots for gold, 32000 = 0.32 lots for forex)

### Expected Results (both platforms)
- XAUUSD: 0.17 × 100 × 4732.52 × 1 = $80,452.84
- BTCUSD: 0.05 × 1 × 92975.46 × 1 = $4,648.77
- GBPJPY: 0.32 × 100000 × 1 × 1.345 = $43,040.00

---

## Tips for Claude Code

1. Test Phase 1 thoroughly with both MT5 and cTrader files before moving to Phase 2
2. Use the sample test data above to verify calculations match across platforms
3. **MT5 parser notes:**
   - Skip 6 header rows
   - First cell = "Trade History Report"
   - Symbol cleaning: XAUUSD+ → XAUUSD
4. **cTrader parser notes:**
   - Volume may be in units — detect and convert to lots
   - Symbol cleaning: XAU/USD → XAUUSD
   - Column names differ from MT5
5. For forex pairs like GBPJPY, the close price is in JPY, so notional = lots × 100000 × GBPUSD rate
6. Keep contract sizes and FX rates in config.py for easy updates
7. **FX API notes:**
   - frankfurter.app is free, no API key needed
   - Always cache rates to avoid redundant API calls
   - Use 5 second timeout to prevent hanging
   - Handle different date formats: 2026.01.19 (MT5) vs 2026-01-19 (cTrader)
   - API date format is YYYY-MM-DD
8. **Testing FX module:**
   - Test with a known date: `https://api.frankfurter.app/2025-01-20?from=GBP&to=USD`
   - Verify fallback works by testing with invalid date or disconnected network
9. **Report transparency:**
   - Always show which FX source was used per trade
   - Show detected platform in output
   - Add a note at bottom if any fallback rates were used
10. **Auto-detection:**
    - Try each parser's can_parse() method
    - Return first parser that returns True
    - If none match, raise helpful error with supported platforms
