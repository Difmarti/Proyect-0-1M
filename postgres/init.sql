-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create OHLCV table for price data
-- UPDATED: Changed DECIMAL(10,5) to DECIMAL(12,5) to support crypto prices (BTCUSD ~$43,000)
CREATE TABLE IF NOT EXISTS price_data (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    open        DECIMAL(12, 5) NOT NULL,  -- Supports up to $9,999,999.99999
    high        DECIMAL(12, 5) NOT NULL,
    low         DECIMAL(12, 5) NOT NULL,
    close       DECIMAL(12, 5) NOT NULL,
    volume      DECIMAL(18, 8) NOT NULL,
    timeframe   TEXT NOT NULL
);

-- Convert it to a hypertable
SELECT create_hypertable('price_data', 'time');

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_price_data_symbol_time ON price_data (symbol, time DESC);

-- Create table for active trades
-- UPDATED: Changed price columns to DECIMAL(12,2) for crypto support
CREATE TABLE IF NOT EXISTS active_trades (
    trade_id        BIGSERIAL PRIMARY KEY,
    ticket          BIGINT NOT NULL UNIQUE,
    symbol          TEXT NOT NULL,
    type            TEXT NOT NULL, -- 'BUY' or 'SELL'
    lots            DECIMAL(10, 2) NOT NULL,
    open_time       TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12, 2) NOT NULL,  -- Supports up to $9,999,999.99
    stop_loss       DECIMAL(12, 2),
    take_profit     DECIMAL(12, 2),
    current_profit  DECIMAL(12, 2),           -- Supports larger profit/loss values
    current_pips    DECIMAL(10, 1),
    strategy        TEXT,
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create table for closed trades
-- UPDATED: Changed price columns to DECIMAL(12,2) for crypto support
CREATE TABLE IF NOT EXISTS trade_history (
    trade_id        BIGSERIAL PRIMARY KEY,
    ticket          BIGINT NOT NULL,
    symbol          TEXT NOT NULL,
    type            TEXT NOT NULL,
    lots            DECIMAL(10, 2) NOT NULL,
    open_time       TIMESTAMPTZ NOT NULL,
    close_time      TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12, 2) NOT NULL,  -- Supports up to $9,999,999.99
    close_price     DECIMAL(12, 2) NOT NULL,
    stop_loss       DECIMAL(12, 2),
    take_profit     DECIMAL(12, 2),
    profit          DECIMAL(12, 2) NOT NULL,  -- Supports larger profit/loss values
    pips            DECIMAL(10, 1) NOT NULL,
    strategy        TEXT,
    reason          TEXT
);

-- Create index for trade history
CREATE INDEX IF NOT EXISTS idx_trade_history_time ON trade_history (close_time DESC);

-- Create table for bot decisions and signals
-- UPDATED: Added more fields for better signal tracking and debugging
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id       BIGSERIAL,
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,        -- 'LONG', 'SHORT', 'CLOSE'
    strategy        TEXT NOT NULL,        -- 'crypto', 'forex', etc.
    price           DECIMAL(12, 2),       -- Entry price
    stop_loss       DECIMAL(12, 2),       -- Stop loss price
    take_profit     DECIMAL(12, 2),       -- Take profit price
    confidence      DECIMAL(5, 2),        -- Signal confidence score (0-100)
    rsi             DECIMAL(10, 2),       -- RSI value at signal time
    macd            DECIMAL(10, 5),       -- MACD value
    ema_fast        DECIMAL(12, 2),       -- Fast EMA value
    ema_slow        DECIMAL(12, 2),       -- Slow EMA value
    bb_position     DECIMAL(5, 2),        -- Position relative to Bollinger Bands
    volume_ratio    DECIMAL(5, 2),        -- Current volume / average volume
    executed        BOOLEAN DEFAULT false, -- Was this signal executed?
    ticket          BIGINT,               -- MT5 ticket if executed
    reason          TEXT,                 -- Reason for signal or rejection
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (signal_id, time)
);

-- Convert signals to a hypertable
SELECT create_hypertable('trading_signals', 'time');

-- Create table for account metrics
CREATE TABLE IF NOT EXISTS account_metrics (
    time            TIMESTAMPTZ NOT NULL,
    balance         DECIMAL(15, 2) NOT NULL,
    equity          DECIMAL(15, 2) NOT NULL,
    margin          DECIMAL(15, 2) NOT NULL,
    free_margin     DECIMAL(15, 2) NOT NULL,
    profit_today    DECIMAL(10, 2) NOT NULL DEFAULT 0,
    drawdown        DECIMAL(5, 2) NOT NULL DEFAULT 0,
    open_positions  INTEGER NOT NULL DEFAULT 0
);

-- Convert metrics to a hypertable
SELECT create_hypertable('account_metrics', 'time');

-- Create view for trade statistics
CREATE OR REPLACE VIEW trade_stats AS
SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as win_rate,
    SUM(profit) as total_profit,
    AVG(profit) as avg_profit_per_trade,
    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) / NULLIF(ABS(SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END)), 0) as profit_factor,
    AVG(CASE WHEN profit > 0 THEN profit END) as avg_win,
    AVG(CASE WHEN profit < 0 THEN profit END) as avg_loss,
    MAX(profit) as largest_win,
    MIN(profit) as largest_loss
FROM trade_history
WHERE close_time >= CURRENT_DATE - INTERVAL '30 days';

-- Function to calculate current drawdown
CREATE OR REPLACE FUNCTION calculate_drawdown()
RETURNS DECIMAL AS $$
DECLARE
    peak_balance DECIMAL;
    current_equity DECIMAL;
BEGIN
    -- Get the highest previous balance
    SELECT MAX(balance) INTO peak_balance FROM account_metrics
    WHERE time >= CURRENT_DATE;
    
    -- Get current equity
    SELECT equity INTO current_equity FROM account_metrics
    ORDER BY time DESC LIMIT 1;
    
    -- Calculate drawdown percentage
    RETURN CASE 
        WHEN peak_balance > 0 THEN 
            ((peak_balance - current_equity) / peak_balance * 100)::DECIMAL(5,2)
        ELSE 0
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to update account metrics
CREATE OR REPLACE FUNCTION update_account_metrics(
    p_balance DECIMAL,
    p_equity DECIMAL,
    p_margin DECIMAL,
    p_free_margin DECIMAL
) RETURNS void AS $$
BEGIN
    INSERT INTO account_metrics (
        time,
        balance,
        equity,
        margin,
        free_margin,
        profit_today,
        drawdown,
        open_positions
    )
    VALUES (
        CURRENT_TIMESTAMP,
        p_balance,
        p_equity,
        p_margin,
        p_free_margin,
        (SELECT COALESCE(SUM(profit), 0) FROM trade_history WHERE close_time::date = CURRENT_DATE),
        calculate_drawdown(),
        (SELECT COUNT(*) FROM active_trades)
    );
END;
$$ LANGUAGE plpgsql;