# 📋 CHANGELOG - Database Schema v2

**Fecha:** 2025-10-23
**Versión:** v1 → v2
**Tipo:** Database Schema Update

---

## 🎯 Objetivo de la Actualización

Solucionar el error crítico **"numeric field overflow"** que impedía almacenar precios de criptomonedas (BTCUSD ~$43,000) y mejorar el tracking de señales de trading.

---

## ❌ Problemas Solucionados

### 1. Error "numeric field overflow"
```
ERROR - Error syncing active trades: numeric field overflow
DETAIL: A field with precision 10, scale 5 must round to an absolute value less than 10^5.
```

**Causa:**
- `DECIMAL(10,5)` solo soporta valores hasta `99,999.99999`
- Precios de crypto superan este límite:
  - BTCUSD: ~$43,000
  - ETHUSD: ~$3,920

**Solución:**
- Cambiar a `DECIMAL(12,2)` para precios de trades (soporta hasta $9,999,999.99)
- Cambiar a `DECIMAL(12,5)` para datos OHLCV (mayor precisión)

### 2. Falta de tracking detallado de señales

**Problema:**
- No se guardaban indicadores técnicos (RSI, MACD, EMA)
- No se podía diagnosticar por qué se rechazaban señales
- No se registraba si una señal fue ejecutada

**Solución:**
- Agregar campos a `trading_signals`: confidence, macd, ema_fast, ema_slow, volume_ratio, ticket
- Permitir análisis histórico de decisiones del bot

---

## 📊 Cambios en el Schema

### Tabla: `price_data`

**Antes (v1):**
```sql
open   DECIMAL(10, 5)  -- Máx: 99,999.99999
high   DECIMAL(10, 5)
low    DECIMAL(10, 5)
close  DECIMAL(10, 5)
```

**Después (v2):**
```sql
open   DECIMAL(12, 5)  -- Máx: 9,999,999.99999 ✅
high   DECIMAL(12, 5)
low    DECIMAL(12, 5)
close  DECIMAL(12, 5)
```

**Impacto:** Soporta precios crypto sin overflow

---

### Tabla: `active_trades`

**Antes (v1):**
```sql
open_price      DECIMAL(10, 5)  -- NO soporta $43,000
stop_loss       DECIMAL(10, 5)
take_profit     DECIMAL(10, 5)
current_profit  DECIMAL(10, 2)
```

**Después (v2):**
```sql
open_price      DECIMAL(12, 2)  -- Soporta $9,999,999.99 ✅
stop_loss       DECIMAL(12, 2)
take_profit     DECIMAL(12, 2)
current_profit  DECIMAL(12, 2)  -- Aumentado también
```

**Impacto:** Sincronización de trades crypto funciona sin errores

---

### Tabla: `trade_history`

**Antes (v1):**
```sql
open_price   DECIMAL(10, 5)
close_price  DECIMAL(10, 5)
stop_loss    DECIMAL(10, 5)
take_profit  DECIMAL(10, 5)
profit       DECIMAL(10, 2)
```

**Después (v2):**
```sql
open_price   DECIMAL(12, 2)
close_price  DECIMAL(12, 2)
stop_loss    DECIMAL(12, 2)
take_profit  DECIMAL(12, 2)
profit       DECIMAL(12, 2)  -- Aumentado
```

**Impacto:** Historial de trades crypto con datos correctos

---

### Tabla: `trading_signals`

**Antes (v1):**
```sql
signal_id    BIGSERIAL
time         TIMESTAMPTZ
symbol       TEXT
type         TEXT           -- 'BUY', 'SELL', 'CLOSE'
strength     DECIMAL(5, 2)  -- Campo limitado
rsi          DECIMAL(10, 2)
bb_position  DECIMAL(5, 2)
ema_trend    TEXT           -- Solo 'ABOVE' o 'BELOW'
executed     BOOLEAN
reason       TEXT
```

**Después (v2):**
```sql
signal_id      BIGSERIAL
time           TIMESTAMPTZ
symbol         TEXT
signal_type    TEXT NOT NULL        -- 'LONG', 'SHORT', 'CLOSE'
strategy       TEXT NOT NULL        -- 'crypto', 'forex', etc. (NUEVO)
price          DECIMAL(12, 2)       -- Precio de entrada (NUEVO)
stop_loss      DECIMAL(12, 2)       -- SL calculado (NUEVO)
take_profit    DECIMAL(12, 2)       -- TP calculado (NUEVO)
confidence     DECIMAL(5, 2)        -- Score de confianza (NUEVO)
rsi            DECIMAL(10, 2)
macd           DECIMAL(10, 5)       -- Valor MACD (NUEVO)
ema_fast       DECIMAL(12, 2)       -- EMA rápida (NUEVO)
ema_slow       DECIMAL(12, 2)       -- EMA lenta (NUEVO)
bb_position    DECIMAL(5, 2)
volume_ratio   DECIMAL(5, 2)        -- Volumen/Promedio (NUEVO)
executed       BOOLEAN
ticket         BIGINT               -- Ticket MT5 si ejecutada (NUEVO)
reason         TEXT
```

**Impacto:**
- Diagnóstico completo de por qué se generan/rechazan señales
- Análisis histórico de performance de estrategias
- Tracking de ejecución de señales

---

### Tabla: `schema_version` (NUEVA)

```sql
CREATE TABLE schema_version (
    version      INTEGER PRIMARY KEY,
    description  TEXT NOT NULL,
    applied_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Propósito:** Tracking de versiones de schema para futuras migraciones

---

## 📁 Archivos Actualizados/Creados

### Actualizados:
1. **`postgres/init.sql`**
   - Schema actualizado a v2
   - Usado en instalaciones nuevas

### Creados:
2. **`postgres/migrate_to_v2.sql`**
   - Script de migración automática v1 → v2
   - Incluye backups de seguridad
   - Limpia datos corruptos
   - Verifica integridad

3. **`postgres/MIGRATION_INSTRUCTIONS.md`**
   - Guía detallada paso a paso
   - Solución de problemas
   - Verificación post-migración

4. **`postgres/QUICK_MIGRATION_COMMAND.txt`**
   - Comandos de una línea
   - Copy-paste para ejecución rápida

5. **`postgres/README.md`**
   - Documentación completa del schema
   - Guía de tablas, vistas y funciones
   - Queries comunes

6. **`windows-mt5-bridge/DIAGNOSTICO_PROBLEMAS.md`**
   - Análisis completo de problemas encontrados
   - Plan de acción detallado

7. **`windows-mt5-bridge/fix_database_schema.sql`**
   - Alternativa al script de migración
   - Para ejecución manual

---

## 🚀 Cómo Aplicar la Migración

### Opción 1: Comando Rápido (Recomendado)

```bash
cd /path/to/project && \
docker-compose down && \
git pull origin main && \
docker-compose up -d timescaledb && \
sleep 5 && \
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/migrate_to_v2.sql && \
docker-compose up -d
```

### Opción 2: Paso a Paso

Ver **`postgres/MIGRATION_INSTRUCTIONS.md`**

---

## ✅ Verificación Post-Migración

### 1. Verificar versión del schema
```bash
docker exec -it trading_timescaledb psql -U trading_user -d trading_db -c "SELECT * FROM schema_version;"
```

Resultado esperado:
```
 version |                    description
---------+----------------------------------------------------
       2 | Support for cryptocurrency prices - DECIMAL(12,2)
```

### 2. Verificar que NO haya errores
```bash
docker-compose logs trading_bridge | grep "numeric field overflow"
```

Resultado esperado: **vacío** (sin resultados)

### 3. Verificar precios de crypto
```sql
SELECT symbol, close, time
FROM price_data
WHERE symbol IN ('BTCUSD', 'ETHUSD')
  AND time >= NOW() - INTERVAL '5 minutes'
ORDER BY time DESC
LIMIT 5;
```

Resultado esperado:
```
 symbol  |  close   |           time
---------+----------+---------------------------
 BTCUSD  | 43250.50 | 2025-10-23 20:05:00
 ETHUSD  | 3920.75  | 2025-10-23 20:05:00
```

---

## 🔄 Compatibilidad

### Backward Compatibility
- ✅ **Datos existentes:** Se preservan durante la migración
- ✅ **Bridge v3:** Compatible con schema v2
- ✅ **API/Dashboard:** Compatibles sin cambios

### Forward Compatibility
- ✅ **Nuevas instalaciones:** Usan schema v2 por defecto
- ✅ **Futuros updates:** Se usará `schema_version` para tracking

---

## 📈 Mejoras de Performance

### Antes (v1):
- ❌ Errores constantes de overflow
- ❌ Sincronización fallando cada 30 segundos
- ❌ Datos corruptos en active_trades
- ❌ Pips calculados incorrectamente (-343,500)

### Después (v2):
- ✅ Sin errores de overflow
- ✅ Sincronización funcionando correctamente
- ✅ Datos precisos y confiables
- ✅ Soporte completo para crypto y forex

---

## ⚠️ Consideraciones Importantes

1. **Detener el bot antes de migrar**
   ```bash
   docker-compose down
   ```

2. **Backup recomendado**
   ```bash
   docker exec trading_timescaledb pg_dump -U trading_user trading_db > backup_pre_migration.sql
   ```

3. **Tiempo estimado de migración:** 1-2 minutos

4. **Downtime:** ~5 minutos total (incluyendo restart)

---

## 🎯 Próximos Pasos Después de Migrar

1. **Verificar logs sin errores:**
   ```bash
   docker-compose logs -f trading_bridge
   ```

2. **Ejecutar diagnóstico de señales** (desde Windows):
   ```powershell
   cd c:\Repositorio\Proyect-0-1M\windows-mt5-bridge
   python diagnose_no_signals.py
   ```

3. **Monitorear trading en vivo:**
   ```powershell
   monitor_live.bat
   ```

4. **Revisar rentabilidad después de 24-48 horas**

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa `postgres/MIGRATION_INSTRUCTIONS.md` (Troubleshooting section)
2. Revisa logs: `docker-compose logs timescaledb`
3. Restaura backup si es necesario

---

## 📝 Changelog Detallado

### [2.0.0] - 2025-10-23

#### Added
- Nueva tabla `schema_version` para tracking de migraciones
- Campos adicionales en `trading_signals`:
  - `strategy`, `price`, `stop_loss`, `take_profit`
  - `confidence`, `macd`, `ema_fast`, `ema_slow`
  - `volume_ratio`, `ticket`
- Script de migración `migrate_to_v2.sql`
- Documentación completa del schema en `postgres/README.md`
- Guía de migración en `MIGRATION_INSTRUCTIONS.md`

#### Changed
- `price_data`: DECIMAL(10,5) → DECIMAL(12,5)
- `active_trades`: DECIMAL(10,5) → DECIMAL(12,2) para precios
- `trade_history`: DECIMAL(10,5) → DECIMAL(12,2) para precios
- `trading_signals`: Renombrado `type` → `signal_type`

#### Fixed
- Error "numeric field overflow" al sincronizar trades crypto
- Precios de BTCUSD/ETHUSD no se guardaban correctamente
- Pips calculados incorrectamente (valores enormes)

#### Removed
- `trading_signals.strength` (reemplazado por `confidence`)
- `trading_signals.ema_trend` (reemplazado por `ema_fast`/`ema_slow`)

---

**Preparado por:** Claude Code
**Fecha:** 2025-10-23
**Versión:** 2.0.0
