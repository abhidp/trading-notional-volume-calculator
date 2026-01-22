import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONTRACT_SIZES, DEFAULT_FOREX_CONTRACT_SIZE
from utils.fx_rates import get_fx_rate


def get_contract_size(symbol: str) -> float:
    """Get contract size for a symbol"""
    # Check if symbol is in predefined sizes
    if symbol in CONTRACT_SIZES:
        return CONTRACT_SIZES[symbol]

    # Default to forex contract size for currency pairs
    return DEFAULT_FOREX_CONTRACT_SIZE


def get_symbol_type(symbol: str) -> str:
    """
    Determine the type of symbol for notional calculation.

    Returns one of:
    - 'forex_usd_base': USDXXX pairs (e.g., USDJPY, USDCAD) - base is USD
    - 'forex_usd_quote': XXXUSD pairs (e.g., EURUSD, AUDUSD) - quote is USD
    - 'forex_cross': XXXYYY pairs (e.g., GBPJPY, EURJPY) - neither is USD
    - 'commodity': Commodities, crypto, indices (e.g., XAUUSD, BTCUSD, GER40)
    """
    # Check if it's a 6-character forex pair
    if len(symbol) == 6:
        base_ccy = symbol[:3]
        quote_ccy = symbol[3:6]

        # Common currency codes
        currencies = {'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF'}

        if base_ccy in currencies and quote_ccy in currencies:
            if base_ccy == 'USD':
                return 'forex_usd_base'
            elif quote_ccy == 'USD':
                return 'forex_usd_quote'
            else:
                return 'forex_cross'

    return 'commodity'


def extract_base_currency(symbol: str, symbol_type: str) -> str:
    """
    Extract base currency from a symbol for FX rate lookup.
    """
    if symbol_type == 'forex_usd_base':
        return 'USD'
    elif symbol_type == 'forex_usd_quote':
        return 'USD'
    elif symbol_type == 'forex_cross':
        return symbol[:3]  # First 3 chars (e.g., GBP from GBPJPY)

    # For commodities/indices
    if symbol.endswith('USD'):
        return 'USD'

    # Index instruments with specific currencies
    index_currencies = {
        'GER40': 'EUR',
        'GER30': 'EUR',
        'UK100': 'GBP',
        'EU50': 'EUR',
        'SPOTCRUDE': 'USD',
    }
    if symbol in index_currencies:
        return index_currencies[symbol]

    return 'USD'


def calculate_notional(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate notional volume for each trade.

    Args:
        trades_df: DataFrame with standardized trade columns

    Returns:
        DataFrame with additional columns:
        - contract_size: float
        - base_currency: str
        - fx_rate: float
        - fx_source: str ('direct', 'api', 'api_cached', 'fallback')
        - notional_usd: float
    """
    results = []

    for _, trade in trades_df.iterrows():
        symbol = trade['symbol']
        lots = trade['lots']
        close_price = trade['close_price']
        close_time = trade['close_time']

        # Determine symbol type and contract size
        symbol_type = get_symbol_type(symbol)
        contract_size = get_contract_size(symbol)

        # Extract base currency for FX rate lookup
        base_currency = extract_base_currency(symbol, symbol_type)

        # Get FX rate
        trade_date = close_time.strftime('%Y-%m-%d') if hasattr(close_time, 'strftime') else str(close_time)
        fx_rate, fx_source = get_fx_rate(base_currency, trade_date)

        # Calculate notional based on symbol type
        if symbol_type == 'forex_usd_base':
            # USDXXX pairs (e.g., USDJPY, USDCAD)
            # Notional = lots × 100,000 (base is already USD)
            notional_usd = lots * contract_size
        elif symbol_type == 'forex_usd_quote':
            # XXXUSD pairs (e.g., EURUSD, AUDUSD)
            # Notional = lots × 100,000 × close_price (close_price IS the USD rate)
            notional_usd = lots * contract_size * close_price
        elif symbol_type == 'forex_cross':
            # XXXYYY cross pairs (e.g., GBPJPY, EURJPY, AUDCAD)
            # Notional = lots × 100,000 × base_to_USD rate
            notional_usd = lots * contract_size * fx_rate
        else:
            # Commodities, crypto, indices (e.g., XAUUSD, BTCUSD, GER40)
            # Notional = lots × contract_size × close_price × fx_rate
            notional_usd = lots * contract_size * close_price * fx_rate

        results.append({
            **trade.to_dict(),
            'contract_size': contract_size,
            'base_currency': base_currency,
            'fx_rate': fx_rate,
            'fx_source': fx_source,
            'notional_usd': notional_usd,
        })

    return pd.DataFrame(results)


def summarize_by_symbol(calculated_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize notional volume by symbol.

    Returns DataFrame with columns:
    - symbol
    - total_lots
    - notional_usd
    - percentage
    """
    # Use named aggregation for explicit column naming
    summary = calculated_df.groupby('symbol', as_index=False).agg(
        total_lots=('lots', 'sum'),
        notional_usd=('notional_usd', 'sum')
    )

    # Ensure notional_usd is float type
    summary['notional_usd'] = summary['notional_usd'].astype(float)

    # Calculate percentage
    total_notional = summary['notional_usd'].sum()
    summary['percentage'] = (summary['notional_usd'] / total_notional * 100) if total_notional > 0 else 0

    # Sort by notional descending
    summary = summary.sort_values('notional_usd', ascending=False).reset_index(drop=True)

    return summary


def get_fx_source_summary(calculated_df: pd.DataFrame) -> dict:
    """
    Get summary of FX sources used.

    Returns dict with counts for each source type.
    """
    source_counts = calculated_df['fx_source'].value_counts().to_dict()
    return {
        'direct': source_counts.get('direct', 0),
        'api': source_counts.get('api', 0),
        'api_cached': source_counts.get('api_cached', 0),
        'fallback': source_counts.get('fallback', 0),
    }
