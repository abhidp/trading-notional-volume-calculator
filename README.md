# Trading Notional Volume Calculator

[![Vercel](https://vercelbadge.vercel.app/api/abhidp/trading-notional-volume-calculator)](https://vercel.com/abhidp/trading-notional-volume-calculator)
[![Lint](https://github.com/abhidp/trading-notional-volume-calculator/actions/workflows/lint.yml/badge.svg)](https://github.com/abhidp/trading-notional-volume-calculator/actions/workflows/lint.yml)
[![CodeQL](https://github.com/abhidp/trading-notional-volume-calculator/actions/workflows/codeql.yml/badge.svg)](https://github.com/abhidp/trading-notional-volume-calculator/actions/workflows/codeql.yml)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen)](https://github.com/abhidp/trading-notional-volume-calculator)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

A tool to calculate total notional trading volume in USD from trade history exports. Supports both **CLI** and **Web UI** interfaces.

> **Privacy First**: All data is processed in memory and never stored. This is open-source software - [verify the code yourself](https://github.com/abhidp/trading-notional-volume-calculator).

## Features

- **Multi-platform support**: MetaTrader 5 (MT5) and cTrader
- **Auto-detection**: Automatically detects the trading platform from file format
- **Date range filtering**: Filter trades by custom dates, last N days, or current month
- **Historical FX rates**: Fetches accurate exchange rates for the trade date via API
- **Multiple export formats**: CSV, HTML, and PDF reports
- **Interactive Web UI**: Upload files and view results with animated charts
- **Command Line Interface**: For automation, scripting, and offline use
- **Privacy focused**: No data storage, no tracking, fully open-source

## Supported Platforms

| Platform | File Format | Export Location |
|----------|-------------|-----------------|
| MetaTrader 5 | `.xlsx` | History tab → Right-click → Report |
| cTrader | `.xlsx`, `.csv` | History → Statement/Export |

## Live Demo

Try the web app at: **[trading-notional-volume-calculator.vercel.app](https://trading-notional-volume-calculator.vercel.app)**

## Installation

### Prerequisites
- Python 3.10 or higher

### Setup

1. Clone the repository:
```bash
git clone https://github.com/abhidp/trading-notional-volume-calculator.git
cd trading-notional-volume-calculator
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web UI (Recommended)

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5001
```

3. Upload your trade history file and view the results

#### Web UI Features:
- **Drag & drop** file upload
- **Auto-detection** of trading platform
- **Interactive pie chart** showing volume distribution by symbol
- **Date range filtering** with presets (Last 7 Days, Last 30 Days, This Month) or custom range
- **Export reports** in CSV, HTML, or PDF format
- **Animated UI** with smooth transitions and count-up effects

### Command Line Interface

The CLI is perfect for automation, scripting, or when you prefer to keep all data on your local machine.

```bash
python cli.py <input_file> [options]
```

#### Options

| Option | Description |
|--------|-------------|
| `-p, --platform` | Specify platform (`mt5` or `ctrader`). Default: auto-detect |
| `-o, --output` | Output file path for the report |
| `-f, --format` | Output format: `csv` or `json` (default: `csv`) |
| `--list-platforms` | List all supported platforms |

#### Date Filtering Options

| Option | Description |
|--------|-------------|
| `-F, --from` | Start date in DD-MM-YYYY format |
| `-T, --to` | End date in DD-MM-YYYY format |
| `--last N` | Filter to last N days (e.g., `--last 7`) |
| `--this-month` | Filter to current calendar month |

#### Examples

```bash
# Basic usage - auto-detect platform, all trades
python cli.py trades.xlsx

# Specify platform explicitly
python cli.py trades.xlsx --platform mt5

# Custom output file
python cli.py trades.xlsx --output my_report.csv

# Export as JSON
python cli.py trades.xlsx --format json

# Date filtering - last 7 days
python cli.py trades.xlsx --last 7

# Date filtering - last 30 days
python cli.py trades.xlsx --last 30

# Date filtering - current month
python cli.py trades.xlsx --this-month

# Date filtering - custom range
python cli.py trades.xlsx --from 01-01-2026 --to 15-01-2026

# Date filtering - from a specific date
python cli.py trades.xlsx --from 01-01-2026

# Combine options
python cli.py trades.xlsx --last 30 --format json --output monthly_report.json
```

## Privacy & Data Handling

We understand that trading history contains sensitive information. Here's how we handle your data:

| Aspect | How We Handle It |
|--------|------------------|
| **Storage** | Files are processed in memory and never saved to servers |
| **Tracking** | No personal information, account numbers, or broker details are collected |
| **Sharing** | Your data is never shared with third parties |
| **Session** | All data is cleared when you close your browser |
| **Transparency** | Code is open-source and publicly auditable on GitHub |

**Prefer complete privacy?** Use the CLI version - your data never leaves your machine.

## How It Works

### Notional Volume Calculation

Notional volume represents the total market value of a leveraged position. The formula varies by instrument type:

| Instrument Type | Examples | Formula |
|-----------------|----------|---------|
| USD Base Pairs | USDJPY, USDCAD | `Lots × 100,000` |
| USD Quote Pairs | EURUSD, GBPUSD | `Lots × 100,000 × Close Price` |
| Cross Pairs | GBPJPY, EURAUD | `Lots × 100,000 × Base-to-USD Rate` |
| Commodities | XAUUSD, XAGUSD | `Lots × Contract Size × Close Price` |
| Indices | GER40, US500 | `Lots × Contract Size × Close Price × FX Rate` |
| Crypto | BTCUSD, ETHUSD | `Lots × Close Price` |

### Contract Sizes

| Instrument | Contract Size |
|------------|---------------|
| Forex Pairs | 100,000 units |
| Gold (XAUUSD) | 100 troy ounces |
| Silver (XAGUSD) | 5,000 troy ounces |
| Crude Oil | 1,000 barrels |
| Crypto (BTC/ETH) | 1 unit |
| Indices | 1 unit (varies) |

### FX Rate Sources

The calculator uses historical exchange rates for accurate USD conversion:

| Source | Badge | Description |
|--------|-------|-------------|
| Direct | `direct` | Instrument already quoted in USD (rate = 1.0) |
| API | `api` | Fresh rate from [Frankfurter API](https://www.frankfurter.app/) |
| Cached | `cached` | Previously fetched rate reused from memory |
| Fallback | `fallback` | Approximate static rate (when API unavailable) |

## Project Structure

```
trading-notional-volume-calculator/
├── app.py                 # Flask web application
├── cli.py                 # Command line interface
├── config.py              # Configuration (contract sizes, FX rates)
├── requirements.txt       # Python dependencies
├── LICENSE                # MIT License
├── README.md              # This file
├── TODO.md                # Future enhancements
├── utils/
│   ├── calculator.py      # Notional volume calculations
│   ├── fx_rates.py        # FX rate fetching and caching
│   ├── report_generator.py# Report generation (CSV, JSON, console)
│   └── parsers/
│       ├── __init__.py    # Parser registry and detection
│       ├── base.py        # Abstract parser base class
│       ├── mt5.py         # MetaTrader 5 parser
│       └── ctrader.py     # cTrader parser
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base layout template
│   ├── index.html         # Upload page
│   ├── results.html       # Results page with charts
│   ├── export.html        # HTML export template
│   └── help.html          # How it works page
├── static/
│   └── css/
│       └── style.css      # Custom styles and animations
└── outputs/               # Generated reports (CLI)
```

## Example Output

After processing a trade history file, you'll see:

- **Total Notional Volume**: Sum of all trade values in USD
- **Total Trades**: Number of closed positions
- **Total Lots**: Sum of all lot sizes
- **Distribution Chart**: Interactive pie chart showing volume by symbol
- **Summary Table**: Breakdown by symbol with percentages
- **Detailed Trade Table**: Individual trade breakdown with FX rates
- **FX Rate Sources**: Summary of how rates were obtained

## Tech Stack

- **Backend**: Python 3.10+, Flask
- **Frontend**: Bootstrap 5, Plotly.js, html2pdf.js
- **Data Processing**: Pandas, OpenPyXL
- **FX Rates**: Frankfurter API (free, no API key required)

## Limitations

- **CFD Instruments Only**: Designed for Forex, Commodities, Indices, and Cryptocurrencies
- **Not for**: Futures, Options, or exchange-traded securities (results may be inaccurate)
- **Stock CFDs**: Currently not supported (planned for future release)

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install pre-commit hooks (runs linting before each commit):
```bash
pre-commit install
```

3. Run linting manually:
```bash
ruff check .        # Check for issues
ruff check . --fix  # Auto-fix issues
ruff format .       # Format code
```

### CI/CD

This project uses GitHub Actions for:
- **Lint** - Ruff linter runs on all PRs
- **CodeQL** - Security vulnerability scanning (free for public repos)
- **Snyk** - Dependency vulnerability scanning (free tier)

## License

MIT License - see [LICENSE](LICENSE) for details.

© 2026 ABHI TRADES PTY LTD. All rights reserved.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up pre-commit hooks (`pre-commit install`)
4. Make your changes and commit (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Support

For issues or feature requests, please [open an issue](https://github.com/abhidp/trading-notional-volume-calculator/issues) on GitHub.
