import pandas as pd
from .base import BaseParser


class CTraderParser(BaseParser):
    """Parser for cTrader trade history exports"""

    # Column name mappings - cTrader exports may use different column names
    # depending on broker or cTrader version
    COLUMN_MAPPINGS = {
        'position_id': ['Position ID', 'Order ID'],
        'symbol': ['Symbol'],
        'direction': ['Direction', 'Opening direction'],
        'open_time': ['Opening Time', 'Opening time'],
        'close_time': ['Closing Time', 'Closing time'],
        'open_price': ['Opening Price', 'Entry price'],
        'close_price': ['Closing Price', 'Closing price'],
        'volume': ['Volume', 'Closing Quantity'],
        'commission': ['Commission'],
        'swap': ['Swap'],
        'profit': ['Net Profit', 'Net AUD', 'Net USD', 'Net EUR', 'Gross Profit'],
    }

    # Threshold to determine if volume is in units or lots
    # If max volume > 100, assume it's in units and needs conversion
    VOLUME_UNITS_THRESHOLD = 100
    VOLUME_DIVISOR = 100000

    def can_parse(self, filepath: str) -> bool:
        """Check for cTrader-specific columns"""
        try:
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath, nrows=1)
            elif filepath.endswith('.csv'):
                df = pd.read_csv(filepath, nrows=1)
            else:
                return False

            # Check for any cTrader-specific column combinations
            ctrader_indicators = [
                'Position ID', 'Order ID', 'Opening direction',
                'Closing Quantity', 'Entry price'
            ]
            return any(col in df.columns for col in ctrader_indicators)
        except Exception:
            return False

    def _get_column(self, df: pd.DataFrame, field: str) -> str:
        """Find the actual column name for a field from possible alternatives"""
        possible_names = self.COLUMN_MAPPINGS.get(field, [field])
        for name in possible_names:
            if name in df.columns:
                return name
        return None

    def _get_column_required(self, df: pd.DataFrame, field: str) -> str:
        """Find required column, raise error if not found"""
        col = self._get_column(df, field)
        if col is None:
            possible_names = self.COLUMN_MAPPINGS.get(field, [field])
            raise ValueError(f"Could not find column for '{field}'. Expected one of: {possible_names}. Available: {list(df.columns)}")
        return col

    def parse(self, filepath: str) -> pd.DataFrame:
        """Parse cTrader trade history file"""
        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")

        if df.empty:
            raise ValueError("No data found in the file")

        # Get actual column names
        symbol_col = self._get_column_required(df, 'symbol')
        direction_col = self._get_column_required(df, 'direction')
        volume_col = self._get_column_required(df, 'volume')
        close_price_col = self._get_column_required(df, 'close_price')
        close_time_col = self._get_column_required(df, 'close_time')

        # Optional columns
        open_price_col = self._get_column(df, 'open_price')
        open_time_col = self._get_column(df, 'open_time')
        commission_col = self._get_column(df, 'commission')
        swap_col = self._get_column(df, 'swap')
        profit_col = self._get_column(df, 'profit')

        # Clean symbols
        df['_clean_symbol'] = df[symbol_col].apply(self.clean_symbol)

        # Determine if volume is in units or lots
        max_volume = df[volume_col].max()
        if max_volume > self.VOLUME_UNITS_THRESHOLD:
            # Volume is in units, convert to lots
            df['_lots'] = df[volume_col] / self.VOLUME_DIVISOR
        else:
            # Volume is already in lots
            df['_lots'] = df[volume_col].astype(float)

        # Handle open_time - use close_time if not available
        if open_time_col:
            open_times = pd.to_datetime(df[open_time_col], format='mixed')
        else:
            open_times = pd.to_datetime(df[close_time_col], format='mixed')

        # Map columns to standardized format
        standardized = pd.DataFrame({
            'open_time': open_times,
            'close_time': pd.to_datetime(df[close_time_col], format='mixed'),
            'symbol': df['_clean_symbol'],
            'type': df[direction_col].str.lower(),
            'lots': df['_lots'],
            'open_price': df[open_price_col].astype(float) if open_price_col else 0.0,
            'close_price': df[close_price_col].astype(float),
            'commission': df[commission_col].astype(float) if commission_col else 0.0,
            'swap': df[swap_col].astype(float) if swap_col else 0.0,
            'profit': df[profit_col].astype(float) if profit_col else 0.0,
        })

        return standardized

    def get_platform_name(self) -> str:
        return "cTrader"
