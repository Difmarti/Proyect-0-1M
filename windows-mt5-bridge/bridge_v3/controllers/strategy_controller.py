"""Strategy analysis controller"""
from typing import Optional
from datetime import datetime

from bridge_v3.config import Settings
from bridge_v3.services import MT5Service, DatabaseService, LoggerService
from bridge_v3.models import TradeSignal, SignalType

# Import existing strategies
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
#from crypto_strategy import CryptoStrategy
from crypto_strategy_relaxed import CryptoStrategyRelaxed as CryptoStrategy

logger = LoggerService.get_logger(__name__)


class StrategyController:
    """Controller for strategy analysis"""

    def __init__(self, mt5_service: MT5Service, db_service: DatabaseService):
        self.mt5 = mt5_service
        self.db = db_service
        self.crypto_strategy = CryptoStrategy() if Settings.CRYPTO_ENABLED else None

    def analyze_crypto_signals(self) -> list[TradeSignal]:
        """Analyze crypto signals for all pairs"""
        if not Settings.CRYPTO_ENABLED or not self.crypto_strategy:
            return []

        signals = []

        for symbol in Settings.CRYPTO_PAIRS:
            symbol = symbol.strip()

            try:
                # Fetch data
                price_data = self.mt5.fetch_crypto_data(symbol, Settings.CRYPTO_TIMEFRAME, bars=200)

                if not price_data or price_data.data.empty:
                    continue

                # Analyze signal
                signal_str = self.crypto_strategy.analyze_signal(price_data.data, symbol)

                if signal_str and signal_str != 'NEUTRAL':
                    current_price = float(price_data.data['close'].iloc[-1])
                    signal_type = SignalType.LONG if signal_str == 'LONG' else SignalType.SHORT

                    # Calculate SL/TP
                    sl, tp = self.crypto_strategy.calculate_sl_tp(current_price, signal_str)

                    signal = TradeSignal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strategy='crypto',
                        price=current_price,
                        stop_loss=sl,
                        take_profit=tp,
                        timestamp=datetime.now(),
                        confidence=0.8,  # You can enhance this with actual confidence calculation
                        reason=f"Crypto strategy signal for {symbol}"
                    )

                    signals.append(signal)
                    logger.info(f"Crypto signal: {symbol} - {signal_type.value} at ${current_price:.2f}")

            except Exception as e:
                logger.error(f"Error analyzing crypto signal for {symbol}: {e}")

        return signals

    def log_signal(self, signal: TradeSignal):
        """Log a trading signal (safety mode)"""
        logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║  Signal Detected: {signal.strategy.upper():<42} ║
╠══════════════════════════════════════════════════════════╣
║  Symbol: {signal.symbol:<47} ║
║  Type: {signal.signal_type.value:<49} ║
║  Price: ${signal.price:<46.2f} ║
║  Stop Loss: ${signal.stop_loss:<41.2f} ║
║  Take Profit: ${signal.take_profit:<39.2f} ║
║  R/R: 1:{signal.risk_reward_ratio():<46.2f} ║
║  Confidence: {signal.confidence * 100:<41.1f}% ║
╚══════════════════════════════════════════════════════════╝
        """)
