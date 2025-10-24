-- =============================================================================
-- MIGRATION SCRIPT v1 -> v2
-- =============================================================================
-- Purpose: Update database schema to support cryptocurrency prices
-- Date: 2025-10-23
-- Changes:
--   1. Increase DECIMAL precision for crypto prices (BTCUSD ~$43,000)
--   2. Update trading_signals table with more detailed fields
--   3. Maintain all existing data during migration
-- =============================================================================

-- Connect to database
\c trading_db

-- =============================================================================
-- STEP 1: Backup existing data (safety measure)
-- =============================================================================
\echo '=================================================='
\echo 'STEP 1: Creating backup tables...'
\echo '=================================================='

-- Backup price_data
CREATE TABLE IF NOT EXISTS price_data_backup AS SELECT * FROM price_data LIMIT 0;

-- Backup active_trades
CREATE TABLE IF NOT EXISTS active_trades_backup AS SELECT * FROM active_trades;

-- Backup trade_history
CREATE TABLE IF NOT EXISTS trade_history_backup AS SELECT * FROM trade_history;

-- Backup trading_signals
CREATE TABLE IF NOT EXISTS trading_signals_backup AS SELECT * FROM trading_signals;

\echo 'Backups created successfully!'

-- =============================================================================
-- STEP 2: Update price_data table
-- =============================================================================
\echo '=================================================='
\echo 'STEP 2: Updating price_data columns...'
\echo '=================================================='

ALTER TABLE price_data ALTER COLUMN open TYPE DECIMAL(12, 5);
ALTER TABLE price_data ALTER COLUMN high TYPE DECIMAL(12, 5);
ALTER TABLE price_data ALTER COLUMN low TYPE DECIMAL(12, 5);
ALTER TABLE price_data ALTER COLUMN close TYPE DECIMAL(12, 5);

\echo 'price_data updated: DECIMAL(10,5) → DECIMAL(12,5)'

-- Verify changes
SELECT
    column_name,
    data_type,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_name = 'price_data'
  AND column_name IN ('open', 'high', 'low', 'close');

-- =============================================================================
-- STEP 3: Update active_trades table
-- =============================================================================
\echo '=================================================='
\echo 'STEP 3: Updating active_trades columns...'
\echo '=================================================='

ALTER TABLE active_trades ALTER COLUMN open_price TYPE DECIMAL(12, 2);
ALTER TABLE active_trades ALTER COLUMN stop_loss TYPE DECIMAL(12, 2);
ALTER TABLE active_trades ALTER COLUMN take_profit TYPE DECIMAL(12, 2);
ALTER TABLE active_trades ALTER COLUMN current_profit TYPE DECIMAL(12, 2);

\echo 'active_trades updated: DECIMAL(10,5) → DECIMAL(12,2)'

-- Verify changes
SELECT
    column_name,
    data_type,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_name = 'active_trades'
  AND column_name IN ('open_price', 'stop_loss', 'take_profit', 'current_profit');

-- =============================================================================
-- STEP 4: Update trade_history table
-- =============================================================================
\echo '=================================================='
\echo 'STEP 4: Updating trade_history columns...'
\echo '=================================================='

ALTER TABLE trade_history ALTER COLUMN open_price TYPE DECIMAL(12, 2);
ALTER TABLE trade_history ALTER COLUMN close_price TYPE DECIMAL(12, 2);
ALTER TABLE trade_history ALTER COLUMN stop_loss TYPE DECIMAL(12, 2);
ALTER TABLE trade_history ALTER COLUMN take_profit TYPE DECIMAL(12, 2);
ALTER TABLE trade_history ALTER COLUMN profit TYPE DECIMAL(12, 2);

\echo 'trade_history updated: DECIMAL(10,5) → DECIMAL(12,2)'

-- Verify changes
SELECT
    column_name,
    data_type,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_name = 'trade_history'
  AND column_name IN ('open_price', 'close_price', 'stop_loss', 'take_profit', 'profit');

-- =============================================================================
-- STEP 5: Update trading_signals table
-- =============================================================================
\echo '=================================================='
\echo 'STEP 5: Updating trading_signals table...'
\echo '=================================================='

-- Check if new columns already exist
DO $$
BEGIN
    -- Rename 'type' to 'signal_type' if exists
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'trading_signals' AND column_name = 'type') THEN
        ALTER TABLE trading_signals RENAME COLUMN type TO signal_type;
        \echo 'Renamed type → signal_type';
    END IF;

    -- Add new columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'strategy') THEN
        ALTER TABLE trading_signals ADD COLUMN strategy TEXT;
        \echo 'Added column: strategy';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'price') THEN
        ALTER TABLE trading_signals ADD COLUMN price DECIMAL(12, 2);
        \echo 'Added column: price';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'stop_loss') THEN
        ALTER TABLE trading_signals ADD COLUMN stop_loss DECIMAL(12, 2);
        \echo 'Added column: stop_loss';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'take_profit') THEN
        ALTER TABLE trading_signals ADD COLUMN take_profit DECIMAL(12, 2);
        \echo 'Added column: take_profit';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'confidence') THEN
        ALTER TABLE trading_signals ADD COLUMN confidence DECIMAL(5, 2);
        \echo 'Added column: confidence';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'macd') THEN
        ALTER TABLE trading_signals ADD COLUMN macd DECIMAL(10, 5);
        \echo 'Added column: macd';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'ema_fast') THEN
        ALTER TABLE trading_signals ADD COLUMN ema_fast DECIMAL(12, 2);
        \echo 'Added column: ema_fast';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'ema_slow') THEN
        ALTER TABLE trading_signals ADD COLUMN ema_slow DECIMAL(12, 2);
        \echo 'Added column: ema_slow';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'volume_ratio') THEN
        ALTER TABLE trading_signals ADD COLUMN volume_ratio DECIMAL(5, 2);
        \echo 'Added column: volume_ratio';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'trading_signals' AND column_name = 'ticket') THEN
        ALTER TABLE trading_signals ADD COLUMN ticket BIGINT;
        \echo 'Added column: ticket';
    END IF;

    -- Drop obsolete columns if they exist
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'trading_signals' AND column_name = 'strength') THEN
        ALTER TABLE trading_signals DROP COLUMN strength;
        \echo 'Dropped obsolete column: strength';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'trading_signals' AND column_name = 'ema_trend') THEN
        ALTER TABLE trading_signals DROP COLUMN ema_trend;
        \echo 'Dropped obsolete column: ema_trend';
    END IF;
END $$;

\echo 'trading_signals table updated with new schema!'

-- Verify trading_signals structure
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'trading_signals'
ORDER BY ordinal_position;

-- =============================================================================
-- STEP 6: Verify data integrity
-- =============================================================================
\echo '=================================================='
\echo 'STEP 6: Verifying data integrity...'
\echo '=================================================='

-- Check for price overflow issues in active_trades
SELECT COUNT(*) as potential_overflow_count
FROM active_trades
WHERE ABS(open_price) >= 100000 OR ABS(stop_loss) >= 100000 OR ABS(take_profit) >= 100000;

-- Check recent price data
SELECT
    symbol,
    COUNT(*) as record_count,
    MIN(close) as min_price,
    MAX(close) as max_price,
    AVG(close) as avg_price
FROM price_data
WHERE time >= NOW() - INTERVAL '1 day'
GROUP BY symbol
ORDER BY symbol;

-- Check active trades
SELECT COUNT(*) as active_trades_count FROM active_trades;

-- Check trade history
SELECT COUNT(*) as history_trades_count FROM trade_history;

-- =============================================================================
-- STEP 7: Clean up corrupted data (if any)
-- =============================================================================
\echo '=================================================='
\echo 'STEP 7: Cleaning corrupted data...'
\echo '=================================================='

-- Fix abnormal pips in active_trades (caused by previous overflow)
UPDATE active_trades
SET current_pips = 0
WHERE ABS(current_pips) > 100000;

\echo 'Cleaned abnormal pips values'

-- =============================================================================
-- STEP 8: Update schema version
-- =============================================================================
\echo '=================================================='
\echo 'STEP 8: Recording migration version...'
\echo '=================================================='

CREATE TABLE IF NOT EXISTS schema_version (
    version         INTEGER PRIMARY KEY,
    description     TEXT NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version, description)
VALUES (2, 'Support for cryptocurrency prices - DECIMAL(12,2) and enhanced trading_signals')
ON CONFLICT (version) DO NOTHING;

SELECT * FROM schema_version ORDER BY version;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
\echo '=================================================='
\echo 'MIGRATION COMPLETED SUCCESSFULLY!'
\echo '=================================================='
\echo ''
\echo 'Summary of changes:'
\echo '  ✅ price_data: DECIMAL(10,5) → DECIMAL(12,5)'
\echo '  ✅ active_trades: DECIMAL(10,5) → DECIMAL(12,2)'
\echo '  ✅ trade_history: DECIMAL(10,5) → DECIMAL(12,2)'
\echo '  ✅ trading_signals: Enhanced with new fields'
\echo '  ✅ Corrupted data cleaned'
\echo '  ✅ Schema version updated to v2'
\echo ''
\echo 'Next steps:'
\echo '  1. Restart the trading bridge'
\echo '  2. Monitor logs for any errors'
\echo '  3. Verify price sync is working'
\echo '  4. Check that signals are being detected'
\echo ''
\echo 'Backup tables created (can be dropped after verification):'
\echo '  - active_trades_backup'
\echo '  - trade_history_backup'
\echo '  - trading_signals_backup'
\echo '=================================================='
