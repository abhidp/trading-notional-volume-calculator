from abc import ABC, abstractmethod
from io import BytesIO

import pandas as pd


class BaseParser(ABC):
    """Base class for all platform parsers"""

    @abstractmethod
    def can_parse(self, file_data: BytesIO, filename: str) -> bool:
        """Check if this parser can handle the file"""
        pass

    @abstractmethod
    def parse(self, file_data: BytesIO, filename: str) -> pd.DataFrame:
        """
        Parse file and return standardized DataFrame.

        Returns DataFrame with columns:
        - open_time: datetime
        - close_time: datetime
        - symbol: str (cleaned, e.g., XAUUSD)
        - type: str ('buy' or 'sell')
        - lots: float
        - open_price: float
        - close_price: float
        - commission: float
        - swap: float
        - profit: float
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name for display"""
        pass

    def clean_symbol(self, symbol: str) -> str:
        """Clean symbol name by removing suffixes and special characters"""
        if not isinstance(symbol, str):
            return str(symbol)
        # Remove common suffixes and special characters
        cleaned = symbol.replace("+", "").replace(".", "").replace("/", "").replace("_", "")
        return cleaned.upper()
