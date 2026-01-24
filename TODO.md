# Future Enhancements

This document tracks planned features and improvements for the Trading Notional Volume Calculator.

---

## High Priority

### Stock CFD Support
**Status:** Not Implemented

**Problem:** Stock CFDs (like AAPL, TSLA, MSFT) are currently not supported correctly. They would use the default forex contract size of 100,000, resulting in calculations that are 100,000x too high.

**Solution Required:**
- Stock CFDs typically have contract size of 1 (1 CFD = 1 share)
- Need to detect stock symbols and apply correct contract size
- Consider using an API or database of stock symbols for accurate detection

**Implementation Notes:**
- Add stock symbol detection logic to `is_supported_symbol()` in `utils/calculator.py`
- Add stock contract sizes to `config.py`
- May need to fetch real-time price data for accurate USD conversion

---

## Medium Priority

### Additional Platform Support
- Interactive Brokers (IBKR) statement parsing
- eToro trade history format
- Plus500 export format
- IG trading platform format

### Enhanced Reporting
- PDF export of results
- Email reports functionality
- Comparison between multiple statement periods

---

## Low Priority

### Data Persistence
- Database storage for historical calculations
- User accounts and saved reports
- API endpoint for programmatic access

### UI Enhancements
- Dark mode support
- Mobile app version
- Real-time FX rate updates

---

## Completed
- [x] MT5 statement parsing
- [x] cTrader statement parsing
- [x] Historical FX rate lookup via API
- [x] Web UI with charts
- [x] CLI interface
- [x] Unsupported symbol detection and warning
