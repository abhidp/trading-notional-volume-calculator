# Trading Notional Volume Calculator

A tool to calculate total notional trading volume in USD from trade history exports. Supports both **CLI** and **Web UI** interfaces.

## Features

- **Multi-platform support**: MetaTrader 5 (MT5) and cTrader
- **Auto-detection**: Automatically detects the trading platform from file format
- **Historical FX rates**: Fetches accurate exchange rates for the trade date via API
- **Multiple output formats**: CSV reports with detailed breakdowns
- **Interactive Web UI**: Upload files and view results with charts
- **Command Line Interface**: For automation and scripting

## Supported Platforms

| Platform | File Format | Export Location |
|----------|-------------|-----------------|
| MetaTrader 5 | `.xlsx` | History tab → Right-click → Report |
| cTrader | `.xlsx`, `.csv` | History → Statement/Export |

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

### Command Line Interface

```bash
python cli.py <input_file> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-p, --platform` | Specify platform (`mt5` or `ctrader`). Default: auto-detect |
| `-o, --output` | Output file path for the CSV report |
| `-f, --format` | Output format: `csv` or `json` (default: `csv`) |

**Examples:**
```bash
# Auto-detect platform
python cli.py trades.xlsx

# Specify platform explicitly
python cli.py trades.xlsx --platform mt5

# Custom output file
python cli.py trades.xlsx --output my_report.csv
```

## How It Works

### Notional Volume Calculation

Notional volume represents the total market value of a leveraged position. The formula varies by instrument type:

| Instrument Type | Examples | Formula |
|-----------------|----------|---------|
| USD Base Pairs | USDJPY, USDCAD | `Lots × 100,000` |
| USD Quote Pairs | EURUSD, GBPUSD | `Lots × 100,000 × Close Price` |
| Cross Pairs | GBPJPY, EURAUD | `Lots × 100,000 × Base-to-USD Rate` |
| Commodities/Indices | XAUUSD, GER40 | `Lots × Contract Size × Close Price × FX Rate` |

### Contract Sizes

| Instrument | Contract Size |
|------------|---------------|
| Forex Pairs | 100,000 units |
| Gold (XAUUSD) | 100 troy ounces |
| Silver (XAGUSD) | 5,000 troy ounces |
| Crude Oil | 1,000 barrels |
| Crypto (BTC/ETH) | 1 unit |
| Indices | 1 unit |

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
├── utils/
│   ├── calculator.py      # Notional volume calculations
│   ├── fx_rates.py        # FX rate fetching and caching
│   ├── report_generator.py# CSV/JSON report generation
│   └── parsers/
│       ├── base.py        # Abstract parser base class
│       ├── mt5.py         # MetaTrader 5 parser
│       └── ctrader.py     # cTrader parser
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   └── help.html
├── static/
│   └── css/
│       └── style.css      # Custom styles
├── uploads/               # Temporary upload storage
└── outputs/               # Generated reports
```

## Example Output

After processing a trade history file, you'll see:

- **Total Notional Volume**: Sum of all trade values in USD
- **Total Trades**: Number of closed positions
- **Total Lots**: Sum of all lot sizes
- **Distribution Chart**: Pie chart showing volume by symbol
- **Detailed Trade Table**: Individual trade breakdown with FX rates

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: Bootstrap 5, Plotly.js
- **Data Processing**: Pandas, OpenPyXL
- **FX Rates**: Frankfurter API

## License

MIT License - see [LICENSE](LICENSE) for details.

© 2026 ABHI TRADES PTY LTD. All rights reserved.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or feature requests, please [open an issue](https://github.com/abhidp/trading-notional-volume-calculator/issues) on GitHub.
