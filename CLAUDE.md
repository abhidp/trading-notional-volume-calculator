# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trading Notional Volume Calculator - calculates total notional trading volume in USD from trade history exports. Supports MetaTrader 5 (MT5) and cTrader platforms via both CLI and Flask web UI.

## Commands

### Run Web UI
```bash
python app.py
# Opens at http://127.0.0.1:5001
```

### Run CLI
```bash
python cli.py <input_file> [--platform mt5|ctrader] [-o output.csv] [--format csv|json]
python cli.py --list-platforms
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Deploy to Vercel
```bash
git push origin main
# Vercel auto-deploys from main branch
```

## Architecture

### Data Flow
1. **Parsers** (`utils/parsers/`) - Parse trade history files into standardized DataFrame
   - `base.py`: Abstract base class with `can_parse()` and `parse()` methods accepting `BytesIO` + filename
   - `mt5.py`: MetaTrader 5 parser - looks for "Trade History Report" header, handles Positions section
   - `ctrader.py`: cTrader parser - detects by column names like "Position ID", "Opening direction"

2. **Calculator** (`utils/calculator.py`) - Core notional calculation logic
   - `get_symbol_type()`: Classifies as forex_usd_base, forex_usd_quote, forex_cross, or commodity
   - `calculate_notional()`: Applies correct formula per symbol type, returns (DataFrame, skipped_symbols dict)
   - `is_supported_symbol()`: Filters out Stock CFDs (short alphabetic symbols)

3. **FX Rates** (`utils/fx_rates.py`) - Historical exchange rate fetching
   - Uses Frankfurter API (`api.frankfurter.app`) for historical rates
   - In-memory cache keyed by (date, currency)
   - Falls back to static rates in `config.py` when API fails

4. **Web App** (`app.py`) - Flask application
   - All file processing done in-memory (no disk storage for compliance)
   - Results stored in `results_store` dict with MAX_RESULTS=5 limit
   - Chart generation via Plotly

### Key Configuration (`config.py`)
- `CONTRACT_SIZES`: Non-forex contract sizes (XAUUSD=100oz, XAGUSD=5000oz, crude=1000 barrels)
- `DEFAULT_FOREX_CONTRACT_SIZE`: 100,000 units
- `FALLBACK_FX_RATES`: Static rates when API unavailable

### Notional Formulas
| Type | Example | Formula |
|------|---------|---------|
| forex_usd_base | USDJPY | lots × 100,000 |
| forex_usd_quote | EURUSD | lots × 100,000 × close_price |
| forex_cross | GBPJPY | lots × 100,000 × base_to_USD_rate |
| commodity | XAUUSD | lots × contract_size × close_price × fx_rate |

### Deployment
- Hosted on Vercel (serverless)
- `vercel.json` configures Python runtime
- No file system access - all processing in memory
- Export HTML uses client-side Plotly.js for charts

## Adding New Trading Platform Parser

1. Create `utils/parsers/<platform>.py` extending `BaseParser`
2. Implement `can_parse(file_data: BytesIO, filename: str)` - detection logic
3. Implement `parse(file_data: BytesIO, filename: str)` - return standardized DataFrame with columns: open_time, close_time, symbol, type, lots, open_price, close_price, commission, swap, profit
4. Register in `utils/parsers/__init__.py`: add to `PARSERS` list and `PLATFORM_PARSERS` dict
