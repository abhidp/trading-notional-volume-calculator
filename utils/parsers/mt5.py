import pandas as pd
from .base import BaseParser


class MT5Parser(BaseParser):
    """Parser for MetaTrader 5 trade history exports"""

    # Column name mappings - MT5 exports may use different column names
    # depending on broker or MT5 version
    COLUMN_MAPPINGS = {
        'open_time': ['Open Time', 'Time'],
        'close_time': ['Close Time', 'Time.1'],
        'symbol': ['Symbol'],
        'type': ['Type'],
        'lots': ['Volume'],
        'open_price': ['Open Price', 'Price'],
        'close_price': ['Close Price', 'Price.1'],
        'commission': ['Commission'],
        'swap': ['Swap'],
        'profit': ['Profit'],
    }

    def can_parse(self, filepath: str) -> bool:
        """Check if first cell contains 'Trade History Report'"""
        try:
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath, nrows=1, header=None)
            elif filepath.endswith('.csv'):
                df = pd.read_csv(filepath, nrows=1, header=None)
            else:
                return False

            first_cell = str(df.iloc[0, 0]) if not df.empty else ""
            return "Trade History Report" in first_cell
        except Exception:
            return False

    def _get_column(self, df: pd.DataFrame, field: str) -> str:
        """Find the actual column name for a field from possible alternatives"""
        possible_names = self.COLUMN_MAPPINGS.get(field, [field])
        for name in possible_names:
            if name in df.columns:
                return name
        raise ValueError(f"Could not find column for '{field}'. Expected one of: {possible_names}. Available: {list(df.columns)}")

    def _find_positions_section(self, filepath: str) -> tuple[int, int]:
        """
        Find the start (header row) and end of the Positions section.

        Returns:
            tuple: (header_row, num_rows) - header row index and number of data rows to read
        """
        # Read file to analyze structure
        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath, header=None)
        else:
            df = pd.read_csv(filepath, header=None)

        header_row = None
        end_row = None

        # Section markers that indicate end of Positions section
        section_markers = {'Orders', 'Deals', 'Working Orders', 'Summary'}

        for idx, row in df.iterrows():
            first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            row_values = [str(v).strip() for v in row.values if pd.notna(v)]

            # Find header row (contains 'Type' and 'Symbol')
            if header_row is None:
                if 'Type' in row_values and 'Symbol' in row_values:
                    header_row = idx
                continue

            # After finding header, look for section end
            if first_cell in section_markers:
                end_row = idx
                break

        # If no end marker found, read until end of file
        if header_row is None:
            header_row = 6  # Fallback

        # Calculate number of rows to read (excluding header)
        if end_row is not None:
            num_rows = end_row - header_row - 1
        else:
            num_rows = None  # Read all remaining rows

        return header_row, num_rows

    def parse(self, filepath: str) -> pd.DataFrame:
        """Parse MT5 trade history file"""
        # Find Positions section boundaries
        header_row, num_rows = self._find_positions_section(filepath)

        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath, skiprows=header_row, nrows=num_rows)
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath, skiprows=header_row, nrows=num_rows)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")

        # Filter out non-trade rows (balance operations, pending orders, etc.)
        type_col = self._get_column(df, 'type')
        volume_col = self._get_column(df, 'lots')

        # Filter to only buy/sell trades with valid numeric volume
        df = df[df[type_col].isin(['buy', 'sell'])].copy()

        # Also filter out rows where Volume is not a valid number
        # (MT5 files may have multiple sections with different formats)
        def is_valid_volume(v):
            if pd.isna(v):
                return False
            try:
                float(v)
                return True
            except (ValueError, TypeError):
                return False

        df = df[df[volume_col].apply(is_valid_volume)].copy()

        if df.empty:
            raise ValueError("No trades found in the file")

        # Get actual column names
        open_time_col = self._get_column(df, 'open_time')
        close_time_col = self._get_column(df, 'close_time')
        symbol_col = self._get_column(df, 'symbol')
        lots_col = self._get_column(df, 'lots')
        open_price_col = self._get_column(df, 'open_price')
        close_price_col = self._get_column(df, 'close_price')

        # Map columns to standardized format
        standardized = pd.DataFrame({
            'open_time': pd.to_datetime(df[open_time_col], format='mixed'),
            'close_time': pd.to_datetime(df[close_time_col], format='mixed'),
            'symbol': df[symbol_col].apply(self.clean_symbol),
            'type': df[type_col].str.lower(),
            'lots': df[lots_col].apply(self._parse_number),
            'open_price': df[open_price_col].apply(self._parse_number),
            'close_price': df[close_price_col].apply(self._parse_number),
            'commission': self._get_optional_column(df, 'commission'),
            'swap': self._get_optional_column(df, 'swap'),
            'profit': self._get_optional_column(df, 'profit'),
        })

        return standardized

    def _parse_number(self, value) -> float:
        """Parse a number that may have spaces as thousands separators"""
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        # Remove spaces (used as thousands separator in some locales)
        cleaned = str(value).replace(' ', '').replace('\u00a0', '')
        return float(cleaned)

    def _get_optional_column(self, df: pd.DataFrame, field: str) -> pd.Series:
        """Get an optional column, returning 0.0 if not found"""
        possible_names = self.COLUMN_MAPPINGS.get(field, [field])
        for name in possible_names:
            if name in df.columns:
                return df[name].apply(self._parse_number)
        return pd.Series([0.0] * len(df))

    def get_platform_name(self) -> str:
        return "MetaTrader 5"
