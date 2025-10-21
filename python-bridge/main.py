import os
import sys
import time
import logging
import json
import schedule
import MetaTrader5 as mt5
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
        self.setup_connections()

    def setup_connections(self):
        """Initialize connections to MT4, PostgreSQL and Redis"""
        # Connect to MetaTrader 5
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            sys.exit(1)

        # Login to MT4 account
        if not mt5.login(
            int(os.getenv('MT4_ACCOUNT')),
            password=os.getenv('MT4_PASSWORD'),
            server=os.getenv('MT4_SERVER')
        ):
            logger.error("MT4 login failed")
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
                rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, datetime.now(), 1)
                if rates is None:
                    logger.warning(f"No data received for {symbol}")
                    continue

                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
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
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Could not fetch account info")
                return

            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT update_account_metrics(%s, %s, %s, %s)
                """, (
                    float(account_info.balance),
                    float(account_info.equity),
                    float(account_info.margin),
                    float(account_info.margin_free)
                ))
            self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error updating account metrics: {e}")
            self.pg_conn.rollback()

    def sync_active_trades(self):
        """Synchronize active trades with MT4"""
        try:
            positions = mt5.positions_get()
            if positions is None:
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
                    position_tickets.add(pos.ticket)
                    position_data.append((
                        pos.ticket,
                        pos.symbol,
                        'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        pos.volume,
                        datetime.fromtimestamp(pos.time, tz=pytz.UTC),
                        pos.price_open,
                        pos.sl,
                        pos.tp,
                        pos.profit,
                        (pos.price_current - pos.price_open) * (1 if pos.type == mt5.POSITION_TYPE_BUY else -1) * 10000,
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
                    for ticket in closed_tickets:
                        history = mt5.history_deals_get(ticket=ticket)
                        if history:
                            deal = history[-1]  # Get the closing deal
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
                                datetime.fromtimestamp(deal.time, tz=pytz.UTC),
                                deal.price,
                                deal.profit,
                                (deal.price - deal.price_open) * (1 if deal.type == mt5.DEAL_TYPE_BUY else -1) * 10000,
                                deal.comment or 'manual',
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
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="MT5 connection failed")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    bridge = MT4Bridge()
    bridge.run()