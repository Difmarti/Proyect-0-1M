"""
PostgreSQL database service with connection pooling
"""

import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import SimpleConnectionPool
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from bridge_v3.config import Settings
from bridge_v3.models import Trade, PriceData, AccountMetrics
from bridge_v3.services.logger_service import LoggerService


logger = LoggerService.get_logger(__name__)


class DatabaseService:
    """PostgreSQL database operations with connection pooling"""

    def __init__(self, pool_min: int = 1, pool_max: int = 10):
        self.pool: Optional[SimpleConnectionPool] = None
        self.pool_min = pool_min
        self.pool_max = pool_max

    def connect(self) -> bool:
        """Initialize connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                self.pool_min,
                self.pool_max,
                host=Settings.POSTGRES_HOST,
                port=Settings.POSTGRES_PORT,
                database=Settings.POSTGRES_DB,
                user=Settings.POSTGRES_USER,
                password=Settings.POSTGRES_PASSWORD
            )
            logger.info(
                f"Connected to PostgreSQL at {Settings.POSTGRES_HOST}:{Settings.POSTGRES_PORT} "
                f"(pool: {self.pool_min}-{self.pool_max})"
            )
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def close(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)"""
        if not self.pool:
            raise RuntimeError("Database not connected")

        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query and optionally fetch results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()

                if fetch:
                    return cursor.fetchall()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {e}")
                raise
            finally:
                cursor.close()

    def store_price_data(self, price_data: PriceData) -> int:
        """Store price data in database"""
        if price_data is None or price_data.data.empty:
            return 0

        records = price_data.to_records()
        inserted = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO price_data (time, symbol, timeframe, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """

            for record in records:
                try:
                    cursor.execute(query, (
                        record['time'],
                        record['symbol'],
                        record['timeframe'],
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume']
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except psycopg2.errors.NumericValueOutOfRange:
                    # Price too large (e.g., crypto prices)
                    conn.rollback()
                    continue
                except Exception as e:
                    conn.rollback()
                    logger.warning(f"Error inserting price data: {e}")
                    continue

            conn.commit()
            cursor.close()

        if inserted > 0:
            logger.info(f"Stored {inserted}/{len(records)} price records for {price_data.symbol}")

        return inserted

    def store_account_metrics(self, metrics: AccountMetrics) -> bool:
        """Store account metrics"""
        try:
            query = """
                INSERT INTO account_metrics
                (time, balance, equity, margin, free_margin, profit_today, drawdown, open_positions)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.execute_query(query, (
                metrics.timestamp,
                metrics.balance,
                metrics.equity,
                metrics.margin,
                metrics.free_margin,
                metrics.profit,
                metrics.drawdown,
                metrics.open_positions
            ))

            logger.info(f"Stored account metrics: Balance={metrics.balance}, Equity={metrics.equity}")
            return True

        except Exception as e:
            logger.error(f"Error storing account metrics: {e}")
            return False

    def sync_active_trades(self, trades: List[Trade]) -> bool:
        """Sync active trades to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get active tickets
                active_tickets = [trade.ticket for trade in trades]

                # Delete trades no longer active
                if active_tickets:
                    cursor.execute(
                        "DELETE FROM active_trades WHERE ticket NOT IN %s",
                        (tuple(active_tickets),)
                    )
                else:
                    cursor.execute("DELETE FROM active_trades")

                # Insert or update active trades
                for trade in trades:
                    # Check if exists
                    cursor.execute("SELECT COUNT(*) FROM active_trades WHERE ticket = %s", (trade.ticket,))
                    exists = cursor.fetchone()[0] > 0

                    if exists:
                        # Update existing
                        query = """
                            UPDATE active_trades
                            SET current_profit = %s, current_pips = %s,
                                stop_loss = %s, take_profit = %s, last_updated = NOW()
                            WHERE ticket = %s
                        """
                        cursor.execute(query, (
                            trade.profit, trade.pips,
                            trade.stop_loss, trade.take_profit,
                            trade.ticket
                        ))
                    else:
                        # Insert new
                        query = """
                            INSERT INTO active_trades
                            (ticket, symbol, type, lots, open_time, open_price,
                             stop_loss, take_profit, current_profit, current_pips, strategy, last_updated)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                        cursor.execute(query, (
                            trade.ticket, trade.symbol, trade.trade_type, trade.lots,
                            trade.open_time, trade.open_price,
                            trade.stop_loss, trade.take_profit,
                            trade.profit, trade.pips, trade.strategy
                        ))

                conn.commit()
                cursor.close()

            logger.info(f"Synced {len(trades)} active trades")
            return True

        except Exception as e:
            logger.error(f"Error syncing active trades: {e}")
            return False

    def get_latest_balance(self) -> Optional[float]:
        """Get latest account balance from database"""
        try:
            query = "SELECT balance FROM account_metrics ORDER BY time DESC LIMIT 1"
            result = self.execute_query(query, fetch=True)
            if result:
                return float(result[0][0])
            return None
        except Exception as e:
            logger.error(f"Error getting latest balance: {e}")
            return None

    def get_daily_trades_count(self) -> int:
        """Get count of trades today"""
        try:
            query = """
                SELECT COUNT(*) FROM trade_history
                WHERE DATE(open_time) = CURRENT_DATE
            """
            result = self.execute_query(query, fetch=True)
            if result:
                return int(result[0][0])
            return 0
        except Exception as e:
            logger.error(f"Error getting daily trades count: {e}")
            return 0

    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            result = self.execute_query("SELECT 1", fetch=True)
            return result is not None
        except Exception:
            return False
