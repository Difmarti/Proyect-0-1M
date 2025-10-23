"""
Trade controller - handles trade synchronization and management
"""

from typing import List
from datetime import datetime

from bridge_v3.services import MT5Service, DatabaseService, RedisService, LoggerService
from bridge_v3.models import Trade, Position


logger = LoggerService.get_logger(__name__)


class TradeController:
    """Controller for trade operations"""

    def __init__(self, mt5_service: MT5Service, db_service: DatabaseService, redis_service: RedisService):
        self.mt5 = mt5_service
        self.db = db_service
        self.redis = redis_service

    def sync_active_trades(self) -> dict:
        """Sync active positions to database and cache"""
        try:
            # Get positions from MT5
            positions = self.mt5.get_positions()

            # Convert to Trade models
            trades = [pos.to_trade() for pos in positions]

            # Determine strategy for each trade
            for trade in trades:
                trade.strategy = self._determine_strategy(trade.symbol)

            # Store in database
            self.db.sync_active_trades(trades)

            # Cache in Redis
            self._cache_active_trades(trades)

            logger.info(f"Synced {len(trades)} active trades")
            return {
                'success': True,
                'count': len(trades),
                'trades': [t.to_dict() for t in trades]
            }

        except Exception as e:
            logger.error(f"Error syncing active trades: {e}")
            return {'success': False, 'count': 0, 'trades': []}

    def _determine_strategy(self, symbol: str) -> str:
        """Determine strategy type based on symbol"""
        from bridge_v3.config import Settings

        if symbol in Settings.CRYPTO_PAIRS:
            return 'crypto'
        elif symbol in Settings.FOREX_PAIRS:
            return 'forex'
        else:
            return 'manual'

    def _cache_active_trades(self, trades: List[Trade]):
        """Cache active trades in Redis"""
        try:
            # Store count
            self.redis.set('trades:active:count', len(trades), ttl=300)

            # Store trades by type
            forex_count = sum(1 for t in trades if t.strategy == 'forex')
            crypto_count = sum(1 for t in trades if t.strategy == 'crypto')

            self.redis.hset('trades:active:by_type', {
                'forex': forex_count,
                'crypto': crypto_count,
                'total': len(trades),
                'updated_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error caching active trades: {e}")

    def get_active_trades_summary(self) -> dict:
        """Get summary of active trades"""
        try:
            positions = self.mt5.get_positions()

            summary = {
                'total': len(positions),
                'forex': 0,
                'crypto': 0,
                'total_profit': 0.0,
                'total_pips': 0.0,
                'trades': []
            }

            for pos in positions:
                trade = pos.to_trade()
                trade.strategy = self._determine_strategy(pos.symbol)

                if trade.strategy == 'forex':
                    summary['forex'] += 1
                elif trade.strategy == 'crypto':
                    summary['crypto'] += 1

                summary['total_profit'] += trade.profit
                summary['total_pips'] += trade.pips
                summary['trades'].append(trade.to_dict())

            return summary

        except Exception as e:
            logger.error(f"Error getting active trades summary: {e}")
            return {'total': 0, 'forex': 0, 'crypto': 0, 'total_profit': 0.0, 'total_pips': 0.0, 'trades': []}

    def close_trade(self, ticket: int) -> bool:
        """Close a trade by ticket"""
        try:
            result = self.mt5.close_position(ticket)
            if result:
                logger.info(f"Successfully closed trade {ticket}")
                # Trigger sync to update database
                self.sync_active_trades()
            return result
        except Exception as e:
            logger.error(f"Error closing trade {ticket}: {e}")
            return False

    def close_all_trades(self, strategy: str = None) -> dict:
        """Close all trades, optionally filtered by strategy"""
        try:
            positions = self.mt5.get_positions()
            closed = 0
            failed = 0

            for pos in positions:
                trade_strategy = self._determine_strategy(pos.symbol)

                # Skip if strategy filter is set and doesn't match
                if strategy and trade_strategy != strategy:
                    continue

                if self.mt5.close_position(pos.ticket):
                    closed += 1
                else:
                    failed += 1

            logger.info(f"Closed {closed} trades (failed: {failed})")
            return {'closed': closed, 'failed': failed}

        except Exception as e:
            logger.error(f"Error closing all trades: {e}")
            return {'closed': 0, 'failed': 0}
