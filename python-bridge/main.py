import os
import sys
import time
import logging
import json
import schedule
from mt4_python import MT4
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
import redis
from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app for health checks
app = FastAPI()

class MT4Bridge:
    def __init__(self):
        self.pg_conn = None
        self.redis_client = None
        self.symbols = os.getenv('TRADING_PAIRS', 'EURUSD,GBPUSD,USDJPY').split(',')
        self.timeframe = os.getenv('TRADING_TIMEFRAME', 'M15')
        self.colombia_tz = pytz.timezone('America/Bogota')
        self.mt4 = None
        self.setup_connections()

    def setup_connections(self):
        """Initialize connections to MT4, PostgreSQL and Redis"""
        try:
            # Connect to MetaTrader 4
            self.mt4 = MT4()
            
            # Login to MT4 account
            login_result = self.mt4.login(
                username=os.getenv('MT4_ACCOUNT'),
                password=os.getenv('MT4_PASSWORD'),
                server=os.getenv('MT4_SERVER'),
                timeout=60000
            )
            
            if not login_result:
                logger.error("MT4 login failed")
                sys.exit(1)
                
            logger.info("Connected to MT4")
        except Exception as e:
            logger.error(f"MT4 initialization failed: {e}")
            sys.exit(1)

        # Connect to PostgreSQL
        try:
            self.pg_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host='timescaledb'
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            sys.exit(1)

        # Connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            sys.exit(1)

    def fetch_and_store_prices(self):
        """Fetch current price data and store in TimescaleDB"""
        for symbol in self.symbols:
            try:
                # Fetch last minute's OHLCV data
                rates = self.mt4.get_last_x_bars(symbol, 'M1', 1)
                if not rates:
                    logger.warning(f"No data received for {symbol}")
                    continue

                df = pd.DataFrame(rates)
                df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
                
                # Store in TimescaleDB
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO price_data (time, symbol, open, high, low, close, volume, timeframe)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (time, symbol) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    """, (
                        df.iloc[0]['time'],
                        symbol,
                        float(df.iloc[0]['open']),
                        float(df.iloc[0]['high']),
                        float(df.iloc[0]['low']),
                        float(df.iloc[0]['close']),
                        float(df.iloc[0]['volume']),
                        'M1'
                    ))
                self.pg_conn.commit()
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                self.pg_conn.rollback()

    def update_account_metrics(self):
        """Update account metrics in database"""
        try:
            account_info = self.mt4.get_account_info()
            if not account_info:
                logger.warning("Could not fetch account info")
                return

            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT update_account_metrics(%s, %s, %s, %s)
                """, (
                    float(account_info['balance']),
                    float(account_info['equity']),
                    float(account_info['margin']),
                    float(account_info['margin_free'])
                ))
            self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error updating account metrics: {e}")
            self.pg_conn.rollback()

    def sync_active_trades(self):
        """Synchronize active trades with MT4"""
        try:
            positions = self.mt4.get_open_positions()
            if not positions:
                logger.info("No active positions")
                positions = []

            # Get current active trades from database
            with self.pg_conn.cursor() as cur:
                cur.execute("SELECT ticket FROM active_trades")
                db_tickets = set(row[0] for row in cur.fetchall())

                # Convert positions to list of tuples for batch update
                position_data = []
                position_tickets = set()

                for pos in positions:
                    position_tickets.add(pos['ticket'])
                    position_data.append((
                        pos['ticket'],
                        pos['symbol'],
                        pos['type'],  # 'buy' or 'sell'
                        pos['lots'],
                        pos['open_time'],
                        pos['open_price'],
                        pos['sl'],
                        pos['tp'],
                        pos['profit'],
                        (pos['current_price'] - pos['open_price']) * (1 if pos['type'].lower() == 'buy' else -1) * 10000,
                        'mean_reversion'  # Strategy name
                    ))

                # Update active trades
                if position_data:
                    execute_batch(cur, """
                        INSERT INTO active_trades (
                            ticket, symbol, type, lots, open_time, open_price,
                            stop_loss, take_profit, current_profit, current_pips, strategy
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (ticket) DO UPDATE SET
                            current_profit = EXCLUDED.current_profit,
                            current_pips = EXCLUDED.current_pips,
                            last_updated = CURRENT_TIMESTAMP
                    """, position_data)

                # Move closed trades to history
                closed_tickets = db_tickets - position_tickets
                if closed_tickets:
                    # Get historical data for closed trades
                    history = self.mt4.get_closed_positions()
                    for ticket in closed_tickets:
                        closed_trade = next((t for t in history if t['ticket'] == ticket), None)
                        if closed_trade:
                            cur.execute("""
                                INSERT INTO trade_history (
                                    ticket, symbol, type, lots, open_time, close_time,
                                    open_price, close_price, stop_loss, take_profit,
                                    profit, pips, strategy, reason
                                )
                                SELECT 
                                    ticket, symbol, type, lots, open_time, %s,
                                    open_price, %s, stop_loss, take_profit,
                                    %s, %s, strategy, %s
                                FROM active_trades
                                WHERE ticket = %s
                            """, (
                                closed_trade['close_time'],
                                closed_trade['close_price'],
                                closed_trade['profit'],
                                (closed_trade['close_price'] - closed_trade['open_price']) * 
                                (1 if closed_trade['type'].lower() == 'buy' else -1) * 10000,
                                closed_trade['comment'] or 'manual',
                                ticket
                            ))
                            
                    # Remove from active trades
                    cur.execute(
                        "DELETE FROM active_trades WHERE ticket = ANY(%s)",
                        (list(closed_tickets),)
                    )

            self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error syncing trades: {e}")
            self.pg_conn.rollback()

    def run(self):
        """Main run loop"""
        # Schedule tasks
        schedule.every(1).minutes.do(self.fetch_and_store_prices)
        schedule.every(1).minutes.do(self.update_account_metrics)
        schedule.every(30).seconds.do(self.sync_active_trades)

        # Start FastAPI server for health checks
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        bridge = MT4Bridge()
        if not bridge.mt4:
            raise HTTPException(status_code=500, detail="MT4 connection failed")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    bridge = MT4Bridge()
    bridge.run()