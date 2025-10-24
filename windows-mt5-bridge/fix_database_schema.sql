-- =============================================================================
-- FIX DATABASE SCHEMA FOR CRYPTO PRICES
-- =============================================================================
-- Problema: NUMERIC(10,5) no soporta precios de crypto (BTCUSD ~43,000)
-- Solución: Cambiar a NUMERIC(12,2) para precios y NUMERIC(12,5) para OHLCV
-- =============================================================================

\c trading_db

-- 1. ACTIVE_TRADES - Cambiar precisión de precios
-- -----------------------------------------------------------------------------
ALTER TABLE active_trades ALTER COLUMN open_price TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN stop_loss TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN take_profit TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN current_profit TYPE NUMERIC(12,2);

-- Verificar cambios
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'active_trades'
  AND column_name IN ('open_price', 'stop_loss', 'take_profit', 'current_profit');

-- 2. TRADE_HISTORY - Cambiar precisión de precios
-- -----------------------------------------------------------------------------
ALTER TABLE trade_history ALTER COLUMN open_price TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN close_price TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN stop_loss TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN take_profit TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN profit TYPE NUMERIC(12,2);

-- Verificar cambios
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'trade_history'
  AND column_name IN ('open_price', 'close_price', 'stop_loss', 'take_profit', 'profit');

-- 3. PRICE_DATA - Cambiar precisión de OHLCV
-- -----------------------------------------------------------------------------
ALTER TABLE price_data ALTER COLUMN open TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN high TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN low TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN close TYPE NUMERIC(12,5);

-- Verificar cambios
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'price_data'
  AND column_name IN ('open', 'high', 'low', 'close');

-- 4. VERIFICACIÓN FINAL
-- -----------------------------------------------------------------------------
-- Verificar que los datos actuales sean válidos
SELECT
    'active_trades' as table_name,
    COUNT(*) as total_records,
    MAX(open_price) as max_price,
    MIN(open_price) as min_price
FROM active_trades
UNION ALL
SELECT
    'price_data' as table_name,
    COUNT(*) as total_records,
    MAX(close) as max_price,
    MIN(close) as min_price
FROM price_data
WHERE time >= NOW() - INTERVAL '1 day';

-- 5. LIMPIAR DATOS CORRUPTOS (OPCIONAL)
-- -----------------------------------------------------------------------------
-- Si hay datos con pips calculados incorrectamente, limpiarlos
UPDATE active_trades
SET current_pips = (current_profit / lots) * 10
WHERE ABS(current_pips) > 100000;  -- Pips anormalmente altos

SELECT * FROM active_trades;

-- =============================================================================
-- RESUMEN DE CAMBIOS
-- =============================================================================
-- active_trades:
--   - open_price: NUMERIC(10,5) → NUMERIC(12,2)  [Soporta hasta $9,999,999.99]
--   - stop_loss: NUMERIC(10,5) → NUMERIC(12,2)
--   - take_profit: NUMERIC(10,5) → NUMERIC(12,2)
--   - current_profit: NUMERIC(10,5) → NUMERIC(12,2)
--
-- trade_history:
--   - open_price: NUMERIC(10,5) → NUMERIC(12,2)
--   - close_price: NUMERIC(10,5) → NUMERIC(12,2)
--   - stop_loss: NUMERIC(10,5) → NUMERIC(12,2)
--   - take_profit: NUMERIC(10,5) → NUMERIC(12,2)
--   - profit: NUMERIC(10,5) → NUMERIC(12,2)
--
-- price_data:
--   - open: NUMERIC(10,5) → NUMERIC(12,5)
--   - high: NUMERIC(10,5) → NUMERIC(12,5)
--   - low: NUMERIC(10,5) → NUMERIC(12,5)
--   - close: NUMERIC(10,5) → NUMERIC(12,5)
-- =============================================================================

\echo 'Database schema fixed successfully!'
\echo 'Next step: Restart the bridge to sync data correctly'
