"""
Price data models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd


@dataclass
class OHLCV:
    """Single OHLCV candlestick"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str
    timeframe: str

    def body_size(self) -> float:
        """Calculate candle body size"""
        return abs(self.close - self.open)

    def upper_wick(self) -> float:
        """Calculate upper wick size"""
        return self.high - max(self.open, self.close)

    def lower_wick(self) -> float:
        """Calculate lower wick size"""
        return min(self.open, self.close) - self.low

    def is_bullish(self) -> bool:
        """Check if candle is bullish"""
        return self.close > self.open

    def is_bearish(self) -> bool:
        """Check if candle is bearish"""
        return self.close < self.open

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'time': self.timestamp,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


@dataclass
class PriceData:
    """Collection of OHLCV data for a symbol"""
    symbol: str
    timeframe: str
    data: pd.DataFrame
    last_update: datetime

    def __post_init__(self):
        """Validate DataFrame has required columns"""
        required_columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume']
        if not all(col in self.data.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

    def get_latest(self) -> Optional[OHLCV]:
        """Get latest OHLCV candle"""
        if self.data.empty:
            return None

        latest = self.data.iloc[-1]
        return OHLCV(
            timestamp=latest['time'],
            open=float(latest['open']),
            high=float(latest['high']),
            low=float(latest['low']),
            close=float(latest['close']),
            volume=int(latest['tick_volume']),
            symbol=self.symbol,
            timeframe=self.timeframe
        )

    def get_close_prices(self) -> pd.Series:
        """Get close prices as Series"""
        return self.data['close']

    def get_high_prices(self) -> pd.Series:
        """Get high prices as Series"""
        return self.data['high']

    def get_low_prices(self) -> pd.Series:
        """Get low prices as Series"""
        return self.data['low']

    def slice(self, start: int = None, end: int = None) -> pd.DataFrame:
        """Get a slice of the data"""
        return self.data.iloc[start:end]

    def add_indicator(self, name: str, values: pd.Series):
        """Add a technical indicator to the DataFrame"""
        self.data[name] = values

    def has_indicator(self, name: str) -> bool:
        """Check if indicator exists"""
        return name in self.data.columns

    def to_records(self) -> list:
        """Convert to list of dictionaries for database insertion"""
        records = []
        for _, row in self.data.iterrows():
            records.append({
                'time': row['time'],
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['tick_volume'])
            })
        return records
