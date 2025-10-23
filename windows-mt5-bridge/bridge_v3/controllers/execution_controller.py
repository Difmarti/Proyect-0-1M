"""
Trade execution controller - handles opening positions based on signals
"""

import MetaTrader5 as mt5
from datetime import datetime

from bridge_v3.config import Settings
from bridge_v3.services import MT5Service, LoggerService
from bridge_v3.models import TradeSignal, SignalType


logger = LoggerService.get_logger(__name__)


class ExecutionController:
    """Controller for executing trades based on signals"""

    def __init__(self, mt5_service: MT5Service):
        self.mt5 = mt5_service
        self.execution_enabled = False  # Safety flag

    def enable_execution(self):
        """Enable trade execution (USE WITH CAUTION!)"""
        self.execution_enabled = True
        logger.warning("⚠️ TRADE EXECUTION ENABLED - Bot will open positions automatically!")

    def disable_execution(self):
        """Disable trade execution (safety mode)"""
        self.execution_enabled = False
        logger.info("Trade execution disabled (safety mode)")

    def execute_signal(self, signal: TradeSignal, risk_pct: float = 2.0) -> dict:
        """
        Execute a trade based on signal

        Args:
            signal: TradeSignal with entry, SL, TP
            risk_pct: Risk percentage per trade (default 2%)

        Returns:
            dict with execution result
        """
        if not self.execution_enabled:
            logger.warning(f"Execution disabled - Signal for {signal.symbol} NOT executed (safety mode)")
            return {'success': False, 'reason': 'Execution disabled', 'ticket': None}

        try:
            # Get account info
            account_info = self.mt5.get_account_info()
            if not account_info:
                return {'success': False, 'reason': 'Failed to get account info', 'ticket': None}

            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(signal.symbol)
            if not symbol_info:
                return {'success': False, 'reason': f'Symbol {signal.symbol} not found', 'ticket': None}

            # Calculate position size
            position_size = self._calculate_position_size(
                account_info.balance,
                signal.price,
                signal.stop_loss,
                risk_pct,
                symbol_info
            )

            if position_size <= 0:
                return {'success': False, 'reason': 'Invalid position size', 'ticket': None}

            # Determine order type
            order_type = mt5.ORDER_TYPE_BUY if signal.signal_type == SignalType.LONG else mt5.ORDER_TYPE_SELL

            # Get current price
            tick = self.mt5.get_symbol_info_tick(signal.symbol)
            if not tick:
                return {'success': False, 'reason': 'Failed to get current price', 'ticket': None}

            execution_price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal.symbol,
                "volume": position_size,
                "type": order_type,
                "price": execution_price,
                "sl": signal.stop_loss,
                "tp": signal.take_profit,
                "deviation": 20,
                "magic": 234000,  # Magic number for V3 trades
                "comment": f"BridgeV3_{signal.strategy}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = self.mt5.send_order(request)

            if result is None:
                return {'success': False, 'reason': 'Order send returned None', 'ticket': None}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment} (retcode: {result.retcode})")
                return {
                    'success': False,
                    'reason': f'{result.comment}',
                    'ticket': None,
                    'retcode': result.retcode
                }

            # Success
            logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅ TRADE EXECUTED SUCCESSFULLY                          ║
╠══════════════════════════════════════════════════════════╣
║  Ticket: {result.order:<47} ║
║  Symbol: {signal.symbol:<47} ║
║  Type: {signal.signal_type.value:<49} ║
║  Volume: {position_size:<46.2f} ║
║  Price: ${execution_price:<45.2f} ║
║  Stop Loss: ${signal.stop_loss:<41.2f} ║
║  Take Profit: ${signal.take_profit:<39.2f} ║
║  Strategy: {signal.strategy:<44} ║
╚══════════════════════════════════════════════════════════╝
            """)

            return {
                'success': True,
                'ticket': result.order,
                'price': execution_price,
                'volume': position_size,
                'sl': signal.stop_loss,
                'tp': signal.take_profit
            }

        except Exception as e:
            logger.error(f"Error executing signal for {signal.symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'reason': str(e), 'ticket': None}

    def _calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float,
        risk_pct: float,
        symbol_info
    ) -> float:
        """
        Calculate position size based on risk percentage

        Args:
            balance: Account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_pct: Risk percentage (e.g., 2.0 for 2%)
            symbol_info: MT5 symbol info

        Returns:
            Position size in lots
        """
        try:
            # Calculate risk amount in account currency
            risk_amount = balance * (risk_pct / 100)

            # Calculate stop loss distance in price
            sl_distance = abs(entry_price - stop_loss)

            if sl_distance <= 0:
                logger.error("Invalid SL distance")
                return 0.0

            # For Forex: lot size calculation
            # risk_amount = sl_distance * lot_size * contract_size * point_value
            # lot_size = risk_amount / (sl_distance * contract_size * point_value)

            # Get contract size (usually 100000 for Forex, 1 for Crypto)
            contract_size = symbol_info.trade_contract_size

            # Calculate position size
            # For crypto: simpler calculation
            if 'USD' in symbol_info.name and symbol_info.name.startswith('BTC'):
                # Crypto (e.g., BTCUSD)
                # Position size = risk_amount / sl_distance
                position_size = risk_amount / sl_distance
            else:
                # Forex
                # Account for pip value
                point = symbol_info.point
                if point == 0:
                    point = 0.00001

                # Calculate lot size
                pip_distance = sl_distance / point
                position_size = risk_amount / (pip_distance * 10)  # Standard lot

            # Round to symbol's volume step
            volume_step = symbol_info.volume_step
            position_size = round(position_size / volume_step) * volume_step

            # Apply min/max limits
            position_size = max(symbol_info.volume_min, position_size)
            position_size = min(symbol_info.volume_max, position_size)

            logger.info(
                f"Position size calculated: {position_size:.2f} lots "
                f"(Risk: ${risk_amount:.2f}, SL distance: {sl_distance:.5f})"
            )

            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0

    def execute_signals_batch(self, signals: list, risk_pct: float = 2.0) -> dict:
        """
        Execute multiple signals

        Returns:
            dict with execution summary
        """
        results = {
            'executed': 0,
            'failed': 0,
            'skipped': 0,
            'tickets': []
        }

        for signal in signals:
            result = self.execute_signal(signal, risk_pct)

            if result['success']:
                results['executed'] += 1
                results['tickets'].append(result['ticket'])
            elif result['reason'] == 'Execution disabled':
                results['skipped'] += 1
            else:
                results['failed'] += 1

        logger.info(
            f"Batch execution complete: "
            f"{results['executed']} executed, "
            f"{results['failed']} failed, "
            f"{results['skipped']} skipped"
        )

        return results
