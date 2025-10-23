"""Risk management controller"""
from datetime import datetime
from bridge_v3.config import Settings
from bridge_v3.services import MT5Service, RedisService, LoggerService
from bridge_v3.models import RiskMetrics

logger = LoggerService.get_logger(__name__)


class RiskController:
    """Controller for risk management"""

    def __init__(self, mt5_service: MT5Service, redis_service: RedisService):
        self.mt5 = mt5_service
        self.redis = redis_service
        self.initial_balance = 0.0

    def initialize(self):
        """Initialize risk manager with current balance"""
        account_info = self.mt5.get_account_info()
        if account_info:
            self.initial_balance = account_info.balance
            self.redis.set('risk:initial_balance', self.initial_balance)
            logger.info(f"Risk manager initialized with balance: {self.initial_balance}")

    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        account_info = self.mt5.get_account_info()
        positions = self.mt5.get_positions()

        # Count positions by type
        forex_count = 0
        crypto_count = 0
        for pos in positions:
            if pos.symbol in Settings.CRYPTO_PAIRS:
                crypto_count += 1
            else:
                forex_count += 1

        # Calculate daily loss
        daily_loss_pct = ((account_info.balance - self.initial_balance) / self.initial_balance) * 100

        return RiskMetrics(
            initial_balance=self.initial_balance,
            current_balance=account_info.balance,
            daily_loss_pct=abs(daily_loss_pct) if daily_loss_pct < 0 else 0,
            total_positions=len(positions),
            forex_positions=forex_count,
            crypto_positions=crypto_count,
            max_daily_loss_pct=Settings.MAX_DAILY_LOSS_PCT,
            max_positions=Settings.MAX_SIMULTANEOUS_TRADES,
            timestamp=datetime.now()
        )

    def can_open_position(self, strategy_type: str) -> tuple[bool, str]:
        """Check if can open a new position"""
        metrics = self.get_risk_metrics()

        # Check daily loss limit
        if metrics.daily_loss_pct >= Settings.MAX_DAILY_LOSS_PCT:
            return False, f"Daily loss limit reached: {metrics.daily_loss_pct:.2f}%"

        # Check position limit
        if metrics.total_positions >= Settings.MAX_SIMULTANEOUS_TRADES:
            return False, f"Max positions reached: {metrics.total_positions}"

        # Check strategy-specific limits
        if strategy_type == 'crypto' and metrics.crypto_positions >= 3:
            return False, "Max crypto positions reached (3)"

        if strategy_type == 'forex' and metrics.forex_positions >= 3:
            return False, "Max forex positions reached (3)"

        return True, "OK"

    def update_cache(self):
        """Update risk metrics cache"""
        metrics = self.get_risk_metrics()
        self.redis.hset('risk:metrics', metrics.to_dict())
