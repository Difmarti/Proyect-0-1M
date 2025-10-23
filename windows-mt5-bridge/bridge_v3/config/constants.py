"""
Constants and enumerations for MT5 Bridge V3
"""

import MetaTrader5 as mt5
from enum import Enum


class TimeFrames:
    """MT5 Timeframe mapping"""
    M1 = mt5.TIMEFRAME_M1
    M5 = mt5.TIMEFRAME_M5
    M15 = mt5.TIMEFRAME_M15
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H4 = mt5.TIMEFRAME_H4
    D1 = mt5.TIMEFRAME_D1
    W1 = mt5.TIMEFRAME_W1
    MN1 = mt5.TIMEFRAME_MN1

    @classmethod
    def get(cls, name: str):
        """Get timeframe by string name"""
        return getattr(cls, name.upper(), cls.M15)

    @classmethod
    def from_minutes(cls, minutes: int):
        """Get timeframe from minutes"""
        mapping = {
            1: cls.M1,
            5: cls.M5,
            15: cls.M15,
            30: cls.M30,
            60: cls.H1,
            240: cls.H4,
            1440: cls.D1,
        }
        return mapping.get(minutes, cls.M15)


class OrderTypes:
    """MT5 Order types"""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP


class TradeAction(Enum):
    """Trade action types"""
    DEAL = mt5.TRADE_ACTION_DEAL
    PENDING = mt5.TRADE_ACTION_PENDING
    SLTP = mt5.TRADE_ACTION_SLTP
    MODIFY = mt5.TRADE_ACTION_MODIFY
    REMOVE = mt5.TRADE_ACTION_REMOVE


class StrategyType(Enum):
    """Strategy types"""
    FOREX = "forex"
    CRYPTO = "crypto"
    CUSTOM = "custom"


class TaskPriority(Enum):
    """Task priority levels for parallel execution"""
    CRITICAL = 0  # Must execute immediately (e.g., risk management)
    HIGH = 1      # Important but can queue (e.g., trade sync)
    NORMAL = 2    # Regular tasks (e.g., price fetch)
    LOW = 3       # Background tasks (e.g., history sync)
