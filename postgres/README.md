# 📊 PostgreSQL Database Schema

## Overview

This directory contains the database schema and migration scripts for the trading bot system using TimescaleDB (PostgreSQL with time-series extensions).

---

## Files

- **`init.sql`** - Initial database schema (v2) - Used for fresh installations
- **`migrate_to_v2.sql`** - Migration script from v1 to v2 - Used for updating existing databases
- **`MIGRATION_INSTRUCTIONS.md`** - Detailed step-by-step migration guide
- **`QUICK_MIGRATION_COMMAND.txt`** - One-line commands for quick migration

---

## Database Schema Versions

### Version 1 (Original)
- `DECIMAL(10,5)` for prices - **ONLY supports prices up to $99,999**
- Limited trading_signals fields
- ❌ **DOES NOT support crypto prices** (BTCUSD ~$43,000)

### Version 2 (Current) ⭐
- `DECIMAL(12,5)` for OHLCV data - **Supports prices up to $9,999,999**
- `DECIMAL(12,2)` for trade prices/profit - **Supports crypto prices**
- Enhanced trading_signals table with detailed tracking
- ✅ **Fully supports cryptocurrency trading**
- ✅ **Prevents numeric overflow errors**

---

## Tables

### 1. `price_data` (Hypertable)
Stores OHLCV (Open, High, Low, Close, Volume) data for all symbols.

```sql
CREATE TABLE price_data (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    open        DECIMAL(12, 5) NOT NULL,
    high        DECIMAL(12, 5) NOT NULL,
    low         DECIMAL(12, 5) NOT NULL,
    close       DECIMAL(12, 5) NOT NULL,
    volume      DECIMAL(18, 8) NOT NULL,
    timeframe   TEXT NOT NULL
);
```

**Indexes:**
- `idx_price_data_symbol_time` on `(symbol, time DESC)`

**Hypertable:** Partitioned by `time` for efficient time-series queries

---

### 2. `active_trades`
Stores currently open positions synced from MT5.

```sql
CREATE TABLE active_trades (
    trade_id        BIGSERIAL PRIMARY KEY,
    ticket          BIGINT NOT NULL UNIQUE,
    symbol          TEXT NOT NULL,
    type            TEXT NOT NULL,
    lots            DECIMAL(10, 2) NOT NULL,
    open_time       TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12, 2) NOT NULL,
    stop_loss       DECIMAL(12, 2),
    take_profit     DECIMAL(12, 2),
    current_profit  DECIMAL(12, 2),
    current_pips    DECIMAL(10, 1),
    strategy        TEXT,
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Unique Constraint:** `ticket` (MT5 ticket number)

---

### 3. `trade_history`
Stores closed trades with profit/loss information.

```sql
CREATE TABLE trade_history (
    trade_id        BIGSERIAL PRIMARY KEY,
    ticket          BIGINT NOT NULL,
    symbol          TEXT NOT NULL,
    type            TEXT NOT NULL,
    lots            DECIMAL(10, 2) NOT NULL,
    open_time       TIMESTAMPTZ NOT NULL,
    close_time      TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12, 2) NOT NULL,
    close_price     DECIMAL(12, 2) NOT NULL,
    stop_loss       DECIMAL(12, 2),
    take_profit     DECIMAL(12, 2),
    profit          DECIMAL(12, 2) NOT NULL,
    pips            DECIMAL(10, 1) NOT NULL,
    strategy        TEXT,
    reason          TEXT
);
```

**Indexes:**
- `idx_trade_history_time` on `(close_time DESC)`

---

### 4. `trading_signals` (Hypertable)
Stores bot decisions and trading signals with detailed technical indicators.

```sql
CREATE TABLE trading_signals (
    signal_id       BIGSERIAL,
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,        -- 'LONG', 'SHORT', 'CLOSE'
    strategy        TEXT NOT NULL,        -- 'crypto', 'forex', etc.
    price           DECIMAL(12, 2),
    stop_loss       DECIMAL(12, 2),
    take_profit     DECIMAL(12, 2),
    confidence      DECIMAL(5, 2),
    rsi             DECIMAL(10, 2),
    macd            DECIMAL(10, 5),
    ema_fast        DECIMAL(12, 2),
    ema_slow        DECIMAL(12, 2),
    bb_position     DECIMAL(5, 2),
    volume_ratio    DECIMAL(5, 2),
    executed        BOOLEAN DEFAULT false,
    ticket          BIGINT,
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (signal_id, time)
);
```

**Hypertable:** Partitioned by `time` for efficient historical analysis

---

### 5. `account_metrics` (Hypertable)
Stores account balance, equity, and margin snapshots.

```sql
CREATE TABLE account_metrics (
    time            TIMESTAMPTZ NOT NULL,
    balance         DECIMAL(15, 2) NOT NULL,
    equity          DECIMAL(15, 2) NOT NULL,
    margin          DECIMAL(15, 2) NOT NULL,
    free_margin     DECIMAL(15, 2) NOT NULL,
    profit_today    DECIMAL(10, 2) NOT NULL DEFAULT 0,
    drawdown        DECIMAL(5, 2) NOT NULL DEFAULT 0,
    open_positions  INTEGER NOT NULL DEFAULT 0
);
```

**Hypertable:** Partitioned by `time` for equity curve analysis

---

### 6. `schema_version`
Tracks database schema version for migrations.

```sql
CREATE TABLE schema_version (
    version         INTEGER PRIMARY KEY,
    description     TEXT NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## Views

### `trade_stats`
Aggregates trading statistics for the last 30 days.

```sql
CREATE VIEW trade_stats AS
SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as win_rate,
    SUM(profit) as total_profit,
    AVG(profit) as avg_profit_per_trade,
    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) /
        NULLIF(ABS(SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END)), 0) as profit_factor,
    AVG(CASE WHEN profit > 0 THEN profit END) as avg_win,
    AVG(CASE WHEN profit < 0 THEN profit END) as avg_loss,
    MAX(profit) as largest_win,
    MIN(profit) as largest_loss
FROM trade_history
WHERE close_time >= CURRENT_DATE - INTERVAL '30 days';
```

---

## Functions

### `calculate_drawdown()`
Calculates current drawdown percentage.

```sql
SELECT calculate_drawdown();
-- Returns: DECIMAL (e.g., 5.23 for 5.23% drawdown)
```

### `update_account_metrics()`
Updates account metrics with current values.

```sql
SELECT update_account_metrics(
    p_balance := 10000.00,
    p_equity := 10150.50,
    p_margin := 250.00,
    p_free_margin := 9900.50
);
```

---

## Migration Guide

### For New Installations

If you're installing the system for the first time:

```bash
# The init.sql will be executed automatically by Docker Compose
docker-compose up -d
```

### For Existing Installations (v1 → v2)

If you have an existing database running v1 schema:

#### Quick Method (One Command):
```bash
cd /path/to/project && \
docker-compose down && \
git pull origin main && \
docker-compose up -d timescaledb && \
sleep 5 && \
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/migrate_to_v2.sql && \
docker-compose up -d
```

#### Detailed Method:
See **`MIGRATION_INSTRUCTIONS.md`** for step-by-step guide.

---

## Checking Schema Version

```bash
# Connect to database
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

# Check version
SELECT * FROM schema_version;
```

Expected output:
```
 version |                    description                     |         applied_at
---------+----------------------------------------------------+---------------------------
       2 | Support for cryptocurrency prices - DECIMAL(12,2) | 2025-10-23 20:00:00
```

---

## Common Queries

### Get Latest Prices
```sql
SELECT symbol, close, time
FROM price_data
WHERE time >= NOW() - INTERVAL '1 hour'
ORDER BY symbol, time DESC;
```

### Get Active Trades
```sql
SELECT ticket, symbol, type, open_price, current_profit
FROM active_trades
ORDER BY open_time DESC;
```

### Get Today's Performance
```sql
SELECT
    COUNT(*) as trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
    SUM(profit) as total_profit
FROM trade_history
WHERE close_time::date = CURRENT_DATE;
```

### Get Trading Signals (Last 24h)
```sql
SELECT time, symbol, signal_type, confidence, executed
FROM trading_signals
WHERE time >= NOW() - INTERVAL '24 hours'
ORDER BY time DESC;
```

---

## Troubleshooting

### Error: "numeric field overflow"

This means you're running schema v1 and trying to store crypto prices.

**Solution:** Run the migration to v2:
```bash
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/migrate_to_v2.sql
```

### Error: "relation does not exist"

The database hasn't been initialized.

**Solution:** Run init.sql:
```bash
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/init.sql
```

### Error: "permission denied"

You don't have proper permissions.

**Solution:** Use postgres superuser:
```bash
docker exec -it trading_timescaledb psql -U postgres -d trading_db
```

---

## Backup & Restore

### Create Backup
```bash
docker exec trading_timescaledb pg_dump -U trading_user trading_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Backup
```bash
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < backup_20250123_120000.sql
```

---

## Performance Tuning

### Hypertable Compression

Enable compression for older data:

```sql
-- Compress data older than 7 days
ALTER TABLE price_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('price_data', INTERVAL '7 days');
```

### Data Retention

Automatically drop old partitions:

```sql
-- Keep only last 90 days
SELECT add_retention_policy('price_data', INTERVAL '90 days');
```

---

## Monitoring

### Check Database Size
```sql
SELECT
    pg_size_pretty(pg_database_size('trading_db')) as total_size,
    pg_size_pretty(pg_total_relation_size('price_data')) as price_data_size,
    pg_size_pretty(pg_total_relation_size('trading_signals')) as signals_size;
```

### Check Record Counts
```sql
SELECT
    (SELECT COUNT(*) FROM price_data) as price_records,
    (SELECT COUNT(*) FROM active_trades) as active_trades,
    (SELECT COUNT(*) FROM trade_history) as closed_trades,
    (SELECT COUNT(*) FROM trading_signals) as signals;
```

---

## Support

For issues or questions:
1. Check `MIGRATION_INSTRUCTIONS.md` for detailed migration steps
2. Review logs: `docker-compose logs timescaledb`
3. Consult PostgreSQL/TimescaleDB documentation

---

**Last Updated:** 2025-10-23
**Schema Version:** v2
**Maintained by:** Claude Code
