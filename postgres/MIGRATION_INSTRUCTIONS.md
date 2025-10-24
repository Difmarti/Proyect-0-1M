# 📋 Instrucciones de Migración - Base de Datos v2

## Resumen de Cambios

Esta migración actualiza el schema de la base de datos para soportar precios de criptomonedas (BTCUSD ~$43,000) y mejora el tracking de señales.

### Cambios Principales:
1. **price_data**: `DECIMAL(10,5)` → `DECIMAL(12,5)` (soporta hasta $9,999,999.99999)
2. **active_trades**: `DECIMAL(10,5)` → `DECIMAL(12,2)` (soporta hasta $9,999,999.99)
3. **trade_history**: `DECIMAL(10,5)` → `DECIMAL(12,2)`
4. **trading_signals**: Nuevos campos para mejor diagnóstico (confidence, macd, ema_fast, ema_slow, etc.)

---

## 🚀 PASOS PARA EJECUTAR EN SERVIDOR LINUX

### Pre-requisitos
- Acceso SSH al servidor Linux (10.30.90.102)
- Usuario con permisos de PostgreSQL
- Base de datos `trading_db` corriendo

---

### Paso 1: Conectarse al Servidor

```bash
# Desde tu máquina local (Windows o Linux)
ssh usuario@10.30.90.102
```

---

### Paso 2: Navegar al Directorio del Proyecto

```bash
cd /ruta/al/proyecto/trading-bot
```

**Nota:** Ajusta la ruta según donde tengas el proyecto. Ejemplos:
- `/home/usuario/trading-bot`
- `/opt/trading-bot`
- `/var/www/trading-bot`

---

### Paso 3: Actualizar el Repositorio (Git Pull)

```bash
# Asegúrate de estar en la rama correcta
git status

# Hacer pull de los últimos cambios
git pull origin main
```

Esto descargará:
- `postgres/migrate_to_v2.sql` (script de migración)
- `postgres/init.sql` (actualizado con nuevo schema)

---

### Paso 4: Detener el Bot (IMPORTANTE)

```bash
# Detener todos los servicios antes de migrar
docker-compose down

# O si usas los scripts:
./stop_bot.sh
```

**⚠️ CRÍTICO:** NO ejecutar la migración con el bot corriendo.

---

### Paso 5: Verificar Backup de Datos (Opcional pero Recomendado)

```bash
# Crear backup manual completo
./backup.sh

# O usar pg_dump directamente
docker exec trading_timescaledb pg_dump -U trading_user trading_db > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql
```

---

### Paso 6: Ejecutar la Migración

#### Opción A: Usando Docker (Recomendado)

```bash
# Asegúrate de que el contenedor de PostgreSQL esté corriendo
docker-compose up -d timescaledb

# Espera 5 segundos a que inicie
sleep 5

# Ejecutar el script de migración
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/migrate_to_v2.sql
```

#### Opción B: Conexión Directa a PostgreSQL

```bash
# Si tienes psql instalado localmente
psql -h localhost -p 5432 -U trading_user -d trading_db -f postgres/migrate_to_v2.sql
```

---

### Paso 7: Verificar Resultados

El script mostrará mensajes como:

```
==================================================
STEP 1: Creating backup tables...
==================================================
Backups created successfully!

==================================================
STEP 2: Updating price_data columns...
==================================================
price_data updated: DECIMAL(10,5) → DECIMAL(12,5)

...

==================================================
MIGRATION COMPLETED SUCCESSFULLY!
==================================================
```

**Busca el mensaje final:** `MIGRATION COMPLETED SUCCESSFULLY!`

---

### Paso 8: Verificar Schema Actualizado

```bash
# Conectarse a PostgreSQL
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

# Dentro de psql, ejecutar:
```

```sql
-- Verificar versión del schema
SELECT * FROM schema_version;

-- Debería mostrar:
-- version | description                                      | applied_at
-- --------+--------------------------------------------------+-------------------------
--      2  | Support for cryptocurrency prices - DECIMAL(12,2)| 2025-10-23 20:00:00

-- Verificar columnas de price_data
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'price_data'
  AND column_name IN ('open', 'high', 'low', 'close');

-- Debería mostrar:
-- column_name | data_type | numeric_precision | numeric_scale
-- ------------+-----------+-------------------+--------------
-- open        | numeric   |                12 |             5
-- high        | numeric   |                12 |             5
-- low         | numeric   |                12 |             5
-- close       | numeric   |                12 |             5

-- Salir de psql
\q
```

---

### Paso 9: Reiniciar el Bot

```bash
# Iniciar todos los servicios
docker-compose up -d

# O usar el script:
./start_bot.sh

# Verificar que todo esté corriendo
docker-compose ps
```

---

### Paso 10: Monitorear Logs

```bash
# Ver logs del bridge
docker-compose logs -f trading_bridge

# Buscar estos mensajes:
# ✅ "Stored 1000/1000 price records for BTCUSD"  (sin errores)
# ✅ "Synced X active trades"  (sin "numeric overflow")
```

---

## ✅ Verificación Post-Migración

### 1. Verificar que NO haya errores de overflow

```bash
# Buscar errores en el log
docker-compose logs trading_bridge | grep "numeric field overflow"

# NO debería retornar nada
```

### 2. Verificar sincronización de precios crypto

```bash
# Conectar a PostgreSQL
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

# Consultar precios recientes
SELECT symbol, close, time
FROM price_data
WHERE symbol IN ('BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD')
  AND time >= NOW() - INTERVAL '5 minutes'
ORDER BY symbol, time DESC
LIMIT 20;

# Deberías ver precios como:
# BTCUSD  | 43250.50  | 2025-10-23 20:05:00
# ETHUSD  | 3920.75   | 2025-10-23 20:05:00
```

### 3. Verificar trades activos (si hay)

```sql
SELECT ticket, symbol, open_price, stop_loss, take_profit, current_profit
FROM active_trades;

-- Los valores deberían ser normales, sin números gigantes
```

---

## 🔧 Solución de Problemas

### Error: "permission denied for schema public"

```bash
# Ejecutar como superusuario postgres
docker exec -it trading_timescaledb psql -U postgres -d trading_db -f /path/to/migrate_to_v2.sql
```

### Error: "relation price_data does not exist"

```bash
# La base de datos no está inicializada, ejecutar init.sql primero
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/init.sql
```

### Error: "migration already applied"

```bash
# Verificar versión del schema
docker exec -it trading_timescaledb psql -U trading_user -d trading_db -c "SELECT * FROM schema_version;"

# Si ya está en v2, la migración ya se aplicó correctamente
```

### El bot sigue mostrando "numeric overflow"

```bash
# Detener el bot
docker-compose down

# Limpiar contenedores y volúmenes
docker-compose down -v

# Volver a ejecutar la migración
docker-compose up -d timescaledb
docker exec -i trading_timescaledb psql -U trading_user -d trading_db < postgres/migrate_to_v2.sql

# Reiniciar el bot
docker-compose up -d
```

---

## 🗑️ Limpieza de Backups (Después de Verificar)

Después de 24-48 horas de operación sin errores, puedes eliminar las tablas de backup:

```sql
-- Conectar a PostgreSQL
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

-- Eliminar backups
DROP TABLE IF EXISTS active_trades_backup;
DROP TABLE IF EXISTS trade_history_backup;
DROP TABLE IF EXISTS trading_signals_backup;

\q
```

---

## 📊 Métricas de Éxito

Después de la migración, deberías ver:

✅ **Logs sin errores:**
```
INFO - Stored 1000/1000 price records for BTCUSD
INFO - Synced 3 active trades
```

✅ **Precios correctos en la base de datos:**
```
BTCUSD: ~$43,000
ETHUSD: ~$3,900
LTCUSD: ~$90
XRPUSD: ~$0.60
```

✅ **Schema version actualizado:**
```
version = 2
```

✅ **Señales detectándose** (en las próximas horas):
```
INFO - BTCUSD - SEÑAL SHORT detectada (3/4 condiciones)
```

---

## 📞 Soporte

Si encuentras problemas durante la migración:

1. **Revisa los logs:**
   ```bash
   docker-compose logs trading_bridge
   docker-compose logs timescaledb
   ```

2. **Verifica el estado de Docker:**
   ```bash
   docker-compose ps
   ```

3. **Restaura desde backup si es necesario:**
   ```bash
   ./restore.sh backups/full_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

---

## ✨ Próximos Pasos Después de la Migración

1. **Ejecutar diagnóstico de señales** (desde Windows):
   ```powershell
   cd c:\Repositorio\Proyect-0-1M\windows-mt5-bridge
   python diagnose_no_signals.py
   ```

2. **Monitorear trading en vivo:**
   ```powershell
   monitor_live.bat
   dashboard_live.bat
   ```

3. **Revisar rentabilidad después de 24 horas**

---

**Fecha de creación:** 2025-10-23
**Versión del schema:** v1 → v2
**Autor:** Claude Code
