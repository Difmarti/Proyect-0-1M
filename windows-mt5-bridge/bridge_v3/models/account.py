"""
Account-related data models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AccountMetrics:
    """Account metrics snapshot"""
    timestamp: datetime
    balance: float
    equity: float
    margin: float
    free_margin: float
    profit: float
    drawdown: float = 0.0
    open_positions: int = 0
    leverage: int = 0

    def margin_level(self) -> float:
        """Calculate margin level percentage"""
        if self.margin > 0:
            return (self.equity / self.margin) * 100
        return 0.0

    def is_margin_call(self, margin_call_level: float = 100.0) -> bool:
        """Check if account is in margin call"""
        return self.margin_level() <= margin_call_level

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'time': self.timestamp,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'free_margin': self.free_margin,
            'profit_today': self.profit,
            'drawdown': self.drawdown,
            'open_positions': self.open_positions
        }


@dataclass
class RiskMetrics:
    """Risk management metrics"""
    initial_balance: float
    current_balance: float
    daily_loss_pct: float
    total_positions: int
    forex_positions: int
    crypto_positions: int
    max_daily_loss_pct: float
    max_positions: int
    timestamp: datetime

    def daily_loss_amount(self) -> float:
        """Calculate daily loss in currency"""
        return self.initial_balance * (self.daily_loss_pct / 100)

    def remaining_loss_allowance(self) -> float:
        """Calculate remaining loss allowance before hitting limit"""
        max_loss = self.initial_balance * (self.max_daily_loss_pct / 100)
        current_loss = self.daily_loss_amount()
        return max_loss - current_loss

    def can_trade(self) -> bool:
        """Check if trading is allowed based on risk limits"""
        # Check daily loss limit
        if self.daily_loss_pct >= self.max_daily_loss_pct:
            return False

        # Check position limit
        if self.total_positions >= self.max_positions:
            return False

        return True

    def get_risk_level(self) -> str:
        """Get current risk level as string"""
        if self.daily_loss_pct >= self.max_daily_loss_pct * 0.9:
            return "CRITICAL"
        elif self.daily_loss_pct >= self.max_daily_loss_pct * 0.7:
            return "HIGH"
        elif self.daily_loss_pct >= self.max_daily_loss_pct * 0.5:
            return "MEDIUM"
        else:
            return "LOW"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'daily_loss_pct': self.daily_loss_pct,
            'total_positions': self.total_positions,
            'forex_positions': self.forex_positions,
            'crypto_positions': self.crypto_positions,
            'risk_level': self.get_risk_level(),
            'can_trade': self.can_trade(),
            'timestamp': self.timestamp.isoformat()
        }
