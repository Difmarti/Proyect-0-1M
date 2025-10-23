#!/usr/bin/env python3
"""
MT5 Windows Bridge V2 - Integrated Forex + Crypto Trading
Connects to MT5 locally and syncs data to Linux containers via PostgreSQL/Redis

NEW FEATURES:
- Crypto trading strategy (BTC, ETH, LTC, XRP)
- Integrated risk management (10% daily loss limit shared between Forex and Crypto)
- Multi-asset support with independent timeframes
- Position tracking for both asset types

Requirements:
- Python 3.11+
- MetaTrader5 installed and running on Windows
- Network access to Linux server (PostgreSQL, Redis)

Installation:
    pip install -r requirements.txt

Usage:
    python mt5_bridge_v2.py
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

# Import strategies
from crypto_strategy import CryptoStrategy
from risk_manager import RiskManager

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding for Windows console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_bridge_v2.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Set console output to UTF-8 for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
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

# Forex configuration
FOREX_PAIRS = os.getenv('FOREX_PAIRS', 'EURUSD,GBPUSD,USDJPY').split(',')
FOREX_TIMEFRAME = os.getenv('FOREX_TIMEFRAME', 'M15')

# Crypto configuration
CRYPTO_ENABLED = os.getenv('CRYPTO_ENABLED', 'false').lower() == 'true'
CRYPTO_PAIRS = os.getenv('CRYPTO_PAIRS', 'BTCUSD,ETHUSD,LTCUSD,XRPUSD').split(',') if CRYPTO_ENABLED else []
CRYPTO_TIMEFRAME = int(os.getenv('CRYPTO_TIMEFRAME', '15'))

# Risk management
MAX_DAILY_LOSS_PCT = float(os.getenv('MAX_DAILY_LOSS_PCT', '10.0'))

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

# Crypto timeframe mapping (minutes to MT5 constant)
CRYPTO_TF_MAPPING = {
    5: mt5.TIMEFRAME_M5,
    15: mt5.TIMEFRAME_M15,
    30: mt5.TIMEFRAME_M30,
    60: mt5.TIMEFRAME_H1
}


class MT5BridgeV2:
    """Bridge between MT5 on Windows and Linux PostgreSQL/Redis - V2 with Crypto Support"""

    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.mt5_initialized = False

        # Strategies
        self.crypto_strategy = CryptoStrategy() if CRYPTO_ENABLED else None
        self.risk_manager = None  # Will be initialized after Redis connection

        logger.info("=" * 70)
        logger.info("MT5 Windows Bridge V2 - Forex + Crypto Integration")
        logger.info("=" * 70)
        logger.info(f"Forex Pairs: {', '.join(FOREX_PAIRS)}")
        logger.info(f"Forex Timeframe: {FOREX_TIMEFRAME}")
        if CRYPTO_ENABLED:
            logger.info(f"Crypto Pairs: {', '.join(CRYPTO_PAIRS)}")
            logger.info(f"Crypto Timeframe: {CRYPTO_TIMEFRAME} minutes")
            logger.info(f"Crypto Strategy: ENABLED ✓")
        else:
            logger.info(f"Crypto Strategy: DISABLED")
        logger.info(f"Max Daily Loss: {MAX_DAILY_LOSS_PCT}% (shared between Forex and Crypto)")
        logger.info("=" * 70)

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

    def initialize_risk_manager(self):
        """Initialize risk manager after Redis connection"""
        if self.redis_client:
            self.risk_manager = RiskManager(self.redis_client, MAX_DAILY_LOSS_PCT)
            logger.info("Risk Manager initialized")

            # Set initial balance
            account_info = mt5.account_info()
            if account_info:
                self.risk_manager.update_initial_balance(account_info.balance)

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

    def fetch_crypto_data(self, symbol: str, bars: int = 200) -> Optional[pd.DataFrame]:
        """Fetch crypto price data with specific timeframe"""
        try:
            tf = CRYPTO_TF_MAPPING.get(CRYPTO_TIMEFRAME, mt5.TIMEFRAME_M15)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

            if rates is None or len(rates) == 0:
                logger.warning(f"No crypto data received for {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['symbol'] = symbol
            df['timeframe'] = f"M{CRYPTO_TIMEFRAME}"

            # MT5 uses 'tick_volume' for crypto
            if 'volume' not in df.columns and 'tick_volume' in df.columns:
                df['volume'] = df['tick_volume']

            return df

        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
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

            # Insert price data one by one to handle duplicates and overflows gracefully
            query = """
                INSERT INTO price_data (time, symbol, timeframe, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            inserted = 0
            for value in values:
                try:
                    cursor.execute(query, value)
                    self.db_conn.commit()
                    inserted += 1
                except psycopg2.IntegrityError:
                    # Duplicate entry, skip it
                    self.db_conn.rollback()
                    continue
                except psycopg2.errors.NumericValueOutOfRange:
                    # Price too large for database field (crypto prices like BTC=$107,000)
                    logger.warning(f"Price value too large for {value[1]} at {value[0]} - skipping")
                    self.db_conn.rollback()
                    continue
                except Exception as e:
                    logger.warning(f"Error inserting price data for {value[1]}: {e}")
                    self.db_conn.rollback()
                    continue

            cursor.close()

            if inserted > 0:
                logger.info(f"Stored {inserted}/{len(values)} price records for {df['symbol'].iloc[0]}")

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
                INSERT INTO account_metrics (time, balance, equity, margin, free_margin, profit_today, drawdown, open_positions)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
            """

            # Get number of open positions
            positions = mt5.positions_get()
            open_positions = len(positions) if positions else 0

            cursor.execute(query, (
                account_info.balance,
                account_info.equity,
                account_info.margin,
                account_info.margin_free,
                account_info.profit,
                0.0,  # drawdown - will be calculated later
                open_positions
            ))

            self.db_conn.commit()
            cursor.close()

            # Also cache in Redis for fast access
            self.redis_client.hset('account:metrics', mapping={
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'profit': account_info.profit,
                'open_positions': open_positions,
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

            # Delete old trades that are no longer active
            active_tickets = [pos.ticket for pos in positions]

            if active_tickets:
                cursor.execute("""
                    DELETE FROM active_trades
                    WHERE ticket NOT IN %s
                """, (tuple(active_tickets),))
            else:
                cursor.execute("DELETE FROM active_trades")

            # Insert or update active positions
            for pos in positions:
                # Calculate pips for profit
                point = 0.0001 if 'JPY' not in pos.symbol else 0.01
                pips = (pos.price_current - pos.price_open) / point
                if pos.type != mt5.ORDER_TYPE_BUY:
                    pips = -pips

                # Determine strategy type
                is_crypto = any(crypto_pair in pos.symbol for crypto_pair in CRYPTO_PAIRS)
                strategy = 'crypto' if is_crypto else 'forex'

                # Check if trade already exists, then update, else insert
                cursor.execute("SELECT COUNT(*) FROM active_trades WHERE ticket = %s", (pos.ticket,))
                exists = cursor.fetchone()[0] > 0

                if exists:
                    query = """
                        UPDATE active_trades
                        SET current_profit = %s, current_pips = %s, stop_loss = %s, take_profit = %s, last_updated = NOW()
                        WHERE ticket = %s
                    """
                    cursor.execute(query, (pos.profit, pips, pos.sl if pos.sl > 0 else None, pos.tp if pos.tp > 0 else None, pos.ticket))
                    continue

                query = """
                    INSERT INTO active_trades
                    (ticket, symbol, type, lots, open_time, open_price, stop_loss, take_profit, current_profit, current_pips, strategy, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """

                cursor.execute(query, (
                    pos.ticket,
                    pos.symbol,
                    'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    pos.volume,
                    datetime.fromtimestamp(pos.time),
                    pos.price_open,
                    pos.sl if pos.sl > 0 else None,
                    pos.tp if pos.tp > 0 else None,
                    pos.profit,
                    pips,
                    strategy
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

                # Calculate pips
                point = 0.0001 if 'JPY' not in deal.symbol else 0.01
                pips = 0.0  # Will be calculated when we have both entry and exit

                # Determine strategy
                is_crypto = any(crypto_pair in deal.symbol for crypto_pair in CRYPTO_PAIRS)
                strategy = 'crypto' if is_crypto else 'forex'

                query = """
                    INSERT INTO trade_history
                    (ticket, symbol, type, lots, open_time, close_time, open_price, close_price, stop_loss, take_profit, profit, pips, strategy, reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket) DO NOTHING
                """

                cursor.execute(query, (
                    deal.order,
                    deal.symbol,
                    'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                    deal.volume,
                    datetime.fromtimestamp(deal.time),
                    datetime.fromtimestamp(deal.time),
                    deal.price,
                    deal.price,
                    None,  # stop_loss
                    None,  # take_profit
                    deal.profit,
                    pips,
                    strategy,
                    None  # reason
                ))

            self.db_conn.commit()
            cursor.close()

            logger.info(f"Synced {len(deals)} trade history records")

        except Exception as e:
            logger.error(f"Error syncing trade history: {e}")
            self.db_conn.rollback()

    def analyze_crypto_signals(self):
        """Analyze crypto signals and execute trades"""
        if not CRYPTO_ENABLED or not self.mt5_initialized or not self.crypto_strategy:
            return

        try:
            for symbol in CRYPTO_PAIRS:
                symbol = symbol.strip()

                # Fetch crypto data
                df = self.fetch_crypto_data(symbol, bars=200)

                if df is None or df.empty:
                    logger.warning(f"No data for {symbol}")
                    continue

                # Analyze signal
                signal = self.crypto_strategy.analyze_signal(df, symbol)

                if signal:
                    current_price = df['close'].iloc[-1]
                    logger.info(f"🪙 {symbol}: Señal {signal} detectada a ${current_price:.2f}")

                    # Check if can open position
                    account_info = mt5.account_info()
                    can_trade, reason = self.risk_manager.can_open_position('crypto', account_info.balance)

                    if can_trade:
                        self.execute_crypto_trade(symbol, signal, current_price)
                    else:
                        logger.warning(f"⚠️ No se puede abrir posición en {symbol}: {reason}")

        except Exception as e:
            logger.error(f"Error analyzing crypto signals: {e}")
            import traceback
            traceback.print_exc()

    def execute_crypto_trade(self, symbol, signal_type, current_price):
        """Execute crypto trade (LOGGING ONLY FOR NOW - SAFETY MODE)"""

        # Calculate SL and TP
        sl, tp = self.crypto_strategy.calculate_sl_tp(current_price, signal_type)

        logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║  🪙 SEÑAL DE CRYPTO DETECTADA                            ║
╠══════════════════════════════════════════════════════════╣
║  Símbolo: {symbol:<45} ║
║  Tipo: {signal_type:<48} ║
║  Precio: ${current_price:<45.2f} ║
║  Stop Loss: ${sl:<42.2f} ║
║  Take Profit: ${tp:<40.2f} ║
║  Risk/Reward: 1:{abs((tp - current_price) / (current_price - sl)):<38.2f} ║
╚══════════════════════════════════════════════════════════╝
        """)

        # SAFETY MODE: Only log signals, don't execute
        # To enable real trading, uncomment the code below and set CRYPTO_TRADE_EXECUTION=true in .env

        # UNCOMMENT TO ENABLE REAL TRADING:
        # try:
        #     # Determine order type
        #     order_type = mt5.ORDER_TYPE_BUY if signal_type == 'LONG' else mt5.ORDER_TYPE_SELL
        #
        #     # Calculate position size
        #     account_info = mt5.account_info()
        #     position_size = self.crypto_strategy.calculate_position_size(
        #         account_info.balance,
        #         2.0,  # 2% risk per trade
        #         2.0   # 2% stop loss
        #     )
        #
        #     # Prepare order request
        #     request = {
        #         "action": mt5.TRADE_ACTION_DEAL,
        #         "symbol": symbol,
        #         "volume": position_size,
        #         "type": order_type,
        #         "price": current_price,
        #         "sl": sl,
        #         "tp": tp,
        #         "deviation": 20,
        #         "magic": 234567,
        #         "comment": f"crypto_{signal_type.lower()}",
        #         "type_time": mt5.ORDER_TIME_GTC,
        #         "type_filling": mt5.ORDER_FILLING_IOC,
        #     }
        #
        #     # Send order
        #     result = mt5.order_send(request)
        #
        #     if result.retcode != mt5.TRADE_RETCODE_DONE:
        #         logger.error(f"Error executing crypto trade: {result.comment}")
        #     else:
        #         logger.info(f"✅ Crypto trade executed: {symbol} {signal_type} at ${current_price:.2f}")
        #         self.risk_manager.register_position_opened('crypto')
        #
        # except Exception as e:
        #     logger.error(f"Error executing crypto trade: {e}")

    def job_fetch_prices(self):
        """Scheduled job: Fetch and store price data"""
        logger.info("Running job: Fetch prices")

        # Fetch Forex prices
        for symbol in FOREX_PAIRS:
            df = self.fetch_price_data(symbol, FOREX_TIMEFRAME)
            if df is not None:
                self.store_price_data(df)

        # Fetch Crypto prices
        if CRYPTO_ENABLED:
            for symbol in CRYPTO_PAIRS:
                symbol = symbol.strip()
                df = self.fetch_crypto_data(symbol)
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

    def job_analyze_crypto(self):
        """Scheduled job: Analyze crypto signals"""
        if CRYPTO_ENABLED:
            logger.info("Running job: Analyze crypto signals")
            self.analyze_crypto_signals()

    def run(self):
        """Main run loop"""
        logger.info("=" * 70)
        logger.info("MT5 Windows Bridge V2 Starting...")
        logger.info("=" * 70)

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

        # Initialize risk manager
        self.initialize_risk_manager()

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

        # Crypto signal analysis (if enabled)
        if CRYPTO_ENABLED:
            schedule.every(1).minutes.do(self.job_analyze_crypto)

        logger.info("=" * 70)
        logger.info("MT5 Windows Bridge V2 Running!")
        logger.info("Scheduled tasks:")
        logger.info("  - Fetch prices: Every 1 minute (Forex + Crypto)")
        logger.info("  - Sync metrics: Every 1 minute")
        logger.info("  - Sync trades: Every 30 seconds")
        if CRYPTO_ENABLED:
            logger.info("  - Analyze crypto signals: Every 1 minute")
        logger.info("=" * 70)

        if CRYPTO_ENABLED:
            logger.info("")
            logger.info("⚠️  CRYPTO TRADING IN SAFETY MODE ⚠️")
            logger.info("Signals will be logged but NOT executed automatically.")
            logger.info("To enable real trading, uncomment execution code in execute_crypto_trade()")
            logger.info("=" * 70)

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
            logger.info("MT5 Windows Bridge V2 stopped.")


if __name__ == "__main__":
    bridge = MT5BridgeV2()
    bridge.run()
