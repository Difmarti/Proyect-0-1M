#!/usr/bin/env python3
"""
MT5 Windows Bridge - Standalone Python script for Windows
Connects to MT5 locally and syncs data to Linux containers via PostgreSQL/Redis

Requirements:
- Python 3.11+
- MetaTrader5 installed and running on Windows
- Network access to Linux server (PostgreSQL, Redis)

Installation:
    pip install -r requirements.txt

Usage:
    python mt5_bridge.py
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_values
import redis
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment
MT5_ACCOUNT = int(os.getenv('MT5_ACCOUNT', '0'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')
MT5_PATH = os.getenv('MT5_PATH', '')  # Optional: path to terminal64.exe

# Database configuration (Linux server)
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'trading_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'trading_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

# Redis configuration (Linux server)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Trading configuration
TRADING_PAIRS = os.getenv('TRADING_PAIRS', 'EURUSD,GBPUSD,USDJPY').split(',')
TRADING_TIMEFRAME = os.getenv('TRADING_TIMEFRAME', 'M15')

# Timeframe mapping
TIMEFRAMES = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
    'W1': mt5.TIMEFRAME_W1,
    'MN1': mt5.TIMEFRAME_MN1
}


class MT5Bridge:
    """Bridge between MT5 on Windows and Linux PostgreSQL/Redis"""

    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.mt5_initialized = False

    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if MT5_PATH:
                if not mt5.initialize(MT5_PATH):
                    logger.error(f"MT5 initialize() failed with path {MT5_PATH}, error code: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    logger.error(f"MT5 initialize() failed, error code: {mt5.last_error()}")
                    return False

            # Login if credentials provided
            if MT5_ACCOUNT and MT5_PASSWORD and MT5_SERVER:
                authorized = mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER)
                if not authorized:
                    logger.error(f"MT5 login failed, error code: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
                logger.info(f"MT5 logged in successfully to {MT5_SERVER} with account {MT5_ACCOUNT}")
            else:
                logger.info("MT5 initialized without login (using existing session)")

            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False

            logger.info(f"MT5 Account: {account_info.login}, Balance: {account_info.balance}, Server: {account_info.server}")
            self.mt5_initialized = True
            return True

        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def connect_database(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            logger.info(f"Connected to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def connect_redis(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            return False

    def fetch_price_data(self, symbol: str, timeframe: str, bars: int = 1000) -> Optional[pd.DataFrame]:
        """Fetch price data from MT5"""
        try:
            tf = TIMEFRAMES.get(timeframe, mt5.TIMEFRAME_M15)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

            if rates is None or len(rates) == 0:
                logger.warning(f"No data received for {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['symbol'] = symbol
            df['timeframe'] = timeframe

            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None

    def store_price_data(self, df: pd.DataFrame):
        """Store price data in PostgreSQL"""
        if df is None or df.empty:
            return

        try:
            cursor = self.db_conn.cursor()

            # Prepare data for insertion
            values = [
                (
                    row['time'],
                    row['symbol'],
                    row['timeframe'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['tick_volume'])
                )
                for _, row in df.iterrows()
            ]

            # Insert with ON CONFLICT DO NOTHING to avoid duplicates
            query = """
                INSERT INTO price_data (timestamp, symbol, timeframe, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (timestamp, symbol, timeframe) DO NOTHING
            """

            execute_values(cursor, query, values)
            self.db_conn.commit()
            cursor.close()

            logger.info(f"Stored {len(values)} price records for {df['symbol'].iloc[0]}")

        except Exception as e:
            logger.error(f"Error storing price data: {e}")
            self.db_conn.rollback()

    def sync_account_metrics(self):
        """Sync account metrics to database"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return

            cursor = self.db_conn.cursor()

            query = """
                INSERT INTO account_metrics (timestamp, balance, equity, margin, free_margin, margin_level, profit)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s)
            """

            margin_level = (account_info.equity / account_info.margin * 100) if account_info.margin > 0 else 0

            cursor.execute(query, (
                account_info.balance,
                account_info.equity,
                account_info.margin,
                account_info.margin_free,
                margin_level,
                account_info.profit
            ))

            self.db_conn.commit()
            cursor.close()

            # Also cache in Redis for fast access
            self.redis_client.hmset('account:metrics', {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': margin_level,
                'profit': account_info.profit,
                'updated_at': datetime.now().isoformat()
            })

            logger.info(f"Synced account metrics: Balance={account_info.balance}, Equity={account_info.equity}")

        except Exception as e:
            logger.error(f"Error syncing account metrics: {e}")
            self.db_conn.rollback()

    def sync_active_trades(self):
        """Sync active positions to database"""
        try:
            positions = mt5.positions_get()
            if positions is None:
                positions = []

            cursor = self.db_conn.cursor()

            # Get current active trade tickets
            active_tickets = [pos.ticket for pos in positions]

            # Mark trades as closed if they're no longer in MT5
            if active_tickets:
                cursor.execute("""
                    UPDATE active_trades
                    SET closed_at = NOW()
                    WHERE ticket NOT IN %s AND closed_at IS NULL
                """, (tuple(active_tickets),))
            else:
                cursor.execute("""
                    UPDATE active_trades
                    SET closed_at = NOW()
                    WHERE closed_at IS NULL
                """)

            # Insert or update active positions
            for pos in positions:
                query = """
                    INSERT INTO active_trades
                    (ticket, symbol, type, volume, open_price, current_price, stop_loss, take_profit, profit, opened_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket) DO UPDATE SET
                        current_price = EXCLUDED.current_price,
                        profit = EXCLUDED.profit,
                        stop_loss = EXCLUDED.stop_loss,
                        take_profit = EXCLUDED.take_profit
                """

                cursor.execute(query, (
                    pos.ticket,
                    pos.symbol,
                    'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    pos.volume,
                    pos.price_open,
                    pos.price_current,
                    pos.sl if pos.sl > 0 else None,
                    pos.tp if pos.tp > 0 else None,
                    pos.profit,
                    datetime.fromtimestamp(pos.time)
                ))

            self.db_conn.commit()
            cursor.close()

            logger.info(f"Synced {len(positions)} active trades")

        except Exception as e:
            logger.error(f"Error syncing active trades: {e}")
            self.db_conn.rollback()

    def sync_trade_history(self, days: int = 30):
        """Sync trade history to database"""
        try:
            # Get history from last N days
            from_date = datetime.now() - timedelta(days=days)
            deals = mt5.history_deals_get(from_date, datetime.now())

            if deals is None or len(deals) == 0:
                logger.info("No trade history to sync")
                return

            cursor = self.db_conn.cursor()

            for deal in deals:
                # Only process IN/OUT deals (actual trades)
                if deal.entry not in [mt5.DEAL_ENTRY_IN, mt5.DEAL_ENTRY_OUT]:
                    continue

                query = """
                    INSERT INTO trade_history
                    (ticket, symbol, type, volume, open_price, close_price, profit, opened_at, closed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket) DO NOTHING
                """

                cursor.execute(query, (
                    deal.order,
                    deal.symbol,
                    'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                    deal.volume,
                    deal.price,
                    deal.price,
                    deal.profit,
                    datetime.fromtimestamp(deal.time),
                    datetime.fromtimestamp(deal.time)
                ))

            self.db_conn.commit()
            cursor.close()

            logger.info(f"Synced {len(deals)} trade history records")

        except Exception as e:
            logger.error(f"Error syncing trade history: {e}")
            self.db_conn.rollback()

    def job_fetch_prices(self):
        """Scheduled job: Fetch and store price data"""
        logger.info("Running job: Fetch prices")
        for symbol in TRADING_PAIRS:
            df = self.fetch_price_data(symbol, TRADING_TIMEFRAME)
            if df is not None:
                self.store_price_data(df)

    def job_sync_metrics(self):
        """Scheduled job: Sync account metrics"""
        logger.info("Running job: Sync account metrics")
        self.sync_account_metrics()

    def job_sync_trades(self):
        """Scheduled job: Sync active trades"""
        logger.info("Running job: Sync active trades")
        self.sync_active_trades()

    def run(self):
        """Main run loop"""
        logger.info("=" * 60)
        logger.info("MT5 Windows Bridge Starting...")
        logger.info("=" * 60)

        # Initialize connections
        if not self.initialize_mt5():
            logger.error("Failed to initialize MT5. Exiting.")
            return

        if not self.connect_database():
            logger.error("Failed to connect to database. Exiting.")
            mt5.shutdown()
            return

        if not self.connect_redis():
            logger.error("Failed to connect to Redis. Exiting.")
            self.db_conn.close()
            mt5.shutdown()
            return

        # Initial sync
        logger.info("Performing initial sync...")
        self.job_fetch_prices()
        self.job_sync_metrics()
        self.job_sync_trades()
        self.sync_trade_history(days=90)

        # Schedule periodic tasks
        schedule.every(1).minutes.do(self.job_fetch_prices)
        schedule.every(1).minutes.do(self.job_sync_metrics)
        schedule.every(30).seconds.do(self.job_sync_trades)

        logger.info("=" * 60)
        logger.info("MT5 Windows Bridge Running!")
        logger.info("Scheduled tasks:")
        logger.info("  - Fetch prices: Every 1 minute")
        logger.info("  - Sync metrics: Every 1 minute")
        logger.info("  - Sync trades: Every 30 seconds")
        logger.info("=" * 60)

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.db_conn:
                self.db_conn.close()
            if self.mt5_initialized:
                mt5.shutdown()
            logger.info("MT5 Windows Bridge stopped.")


if __name__ == "__main__":
    bridge = MT5Bridge()
    bridge.run()
