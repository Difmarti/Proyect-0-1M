from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
from typing import List, Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Trading Bot API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS", "http://localhost:8501")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="timescaledb",
            cursor_factory=RealDictCursor
        )
        yield conn
    finally:
        conn.close()

# Pydantic models
class Trade(BaseModel):
    trade_id: int
    ticket: int
    symbol: str
    type: str
    lots: float
    open_time: datetime
    open_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    current_profit: Optional[float]
    current_pips: Optional[float]
    strategy: Optional[str]
    last_updated: datetime

class TradeHistory(BaseModel):
    trade_id: int
    ticket: int
    symbol: str
    type: str
    lots: float
    open_time: datetime
    close_time: datetime
    open_price: float
    close_price: float
    profit: float
    pips: float
    strategy: Optional[str]
    reason: Optional[str]

class AccountMetrics(BaseModel):
    balance: float
    equity: float
    profit_today: float
    drawdown: float
    open_positions: int
    win_rate: float
    profit_factor: float

# API endpoints
@app.get("/health")
async def health_check(db: psycopg2.extensions.connection = Depends(get_db)):
    """Health check endpoint"""
    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_model=AccountMetrics)
async def get_metrics(db: psycopg2.extensions.connection = Depends(get_db)):
    """Get current account metrics"""
    try:
        with db.cursor() as cur:
            # Get latest metrics
            cur.execute("""
                SELECT * FROM account_metrics
                ORDER BY time DESC LIMIT 1
            """)
            metrics = cur.fetchone()

            # Get trading statistics
            cur.execute("SELECT * FROM trade_stats")
            stats = cur.fetchone()

            if not metrics:
                raise HTTPException(status_code=404, detail="No metrics found")

            return {
                "balance": float(metrics["balance"]),
                "equity": float(metrics["equity"]),
                "profit_today": float(metrics["profit_today"]),
                "drawdown": float(metrics["drawdown"]),
                "open_positions": int(metrics["open_positions"]),
                "win_rate": float(stats["win_rate"]) if stats and stats["win_rate"] is not None else 0.0,
                "profit_factor": float(stats["profit_factor"]) if stats and stats["profit_factor"] is not None else 0.0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/open", response_model=List[Trade])
async def get_open_trades(db: psycopg2.extensions.connection = Depends(get_db)):
    """Get all currently open trades"""
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT * FROM active_trades
                ORDER BY open_time DESC
            """)
            trades = cur.fetchall()
            return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/history", response_model=List[TradeHistory])
async def get_trade_history(
    symbol: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=365),
    profitable: Optional[bool] = None,
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """Get historical trades with optional filters"""
    try:
        with db.cursor() as cur:
            query = """
                SELECT * FROM trade_history
                WHERE close_time >= NOW() - INTERVAL '%s days'
            """
            params = [days]

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)

            if profitable is not None:
                query += " AND profit {} 0".format('>' if profitable else '<=')

            query += " ORDER BY close_time DESC LIMIT 50"

            cur.execute(query, params)
            trades = cur.fetchall()
            return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance/by_pair")
async def get_performance_by_pair(
    days: int = Query(default=30, ge=1, le=365),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """Get performance statistics grouped by currency pair"""
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as win_rate,
                    SUM(profit) as total_profit,
                    AVG(profit) as avg_profit,
                    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) / 
                        NULLIF(ABS(SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END)), 0) as profit_factor
                FROM trade_history
                WHERE close_time >= NOW() - INTERVAL '%s days'
                GROUP BY symbol
                ORDER BY total_profit DESC
            """, [days])
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance/hourly")
async def get_hourly_performance(
    days: int = Query(default=30, ge=1, le=365),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """Get performance statistics by hour of day"""
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT 
                    EXTRACT(HOUR FROM close_time AT TIME ZONE 'America/Bogota') as hour,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as win_rate,
                    SUM(profit) as total_profit
                FROM trade_history
                WHERE close_time >= NOW() - INTERVAL '%s days'
                GROUP BY hour
                ORDER BY hour
            """, [days])
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equity/curve")
async def get_equity_curve(
    days: int = Query(default=30, ge=1, le=365),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """Get equity curve data"""
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT time, balance, equity
                FROM account_metrics
                WHERE time >= NOW() - INTERVAL '%s days'
                ORDER BY time
            """, [days])
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)