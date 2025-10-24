# 🔴 DIAGNÓSTICO DE PROBLEMAS CRÍTICOS

**Fecha:** 2025-10-23
**Análisis realizado por:** Claude Code

---

## ❌ PROBLEMAS IDENTIFICADOS

### 1. **NO SE ESTÁN DETECTANDO SEÑALES DE TRADING**

#### Evidencia:
```sql
SELECT * FROM trading_signals WHERE time >= NOW() - INTERVAL '24 hours'
-- Resultado: 0 señales en las últimas 24 horas
```

#### Análisis del Log:
```
2025-10-23 16:01:14,778 - __main__ - INFO - Running job: Analyze crypto signals
2025-10-23 16:01:14,886 - bridge_v3.workers.task_worker - INFO - Task completed: analyze_crypto (duration: 0.08s)
```

**El job se ejecuta pero NO genera señales.**

#### Razones:
1. **El job `analyze_crypto` NO está guardando señales en la base de datos**
2. **La estrategia relaxada puede estar rechazando todas las condiciones**
3. **NO hay logging de por qué se rechazan las señales**

---

### 2. **PÉRDIDAS ACUMULADAS - NO RENTABLE**

#### Estado Actual de la Cuenta:
```
Balance Inicial: $1,000.00 (asumido)
Balance Actual:  $997.67
Pérdida:         -$2.33 (-0.23%)
Equity:          $1,003.41
Profit Hoy:      +$5.74
```

#### Trades Activos (PERDIENDO):
1. **ETHUSD BUY** - Ticket 128062933
   - Abierto: 2025-10-23 14:59:20
   - Precio entrada: $3,920.75
   - SL: $3,840.72 / TP: $4,056.27
   - **Profit actual: -$0.34**
   - Pips: -343,500 (ERROR DE CÁLCULO)

2. **LTCUSD SELL** - Ticket 128021341
   - Abierto: 2025-10-23 12:25:38
   - Precio entrada: $93.30
   - SL: $95.17 / TP: $90.03
   - **Profit actual: -$0.06**
   - Pips: -6,000 (ERROR DE CÁLCULO)

⚠️ **AMBOS TRADES ESTÁN EN PÉRDIDA**

#### Historial:
```
Total trades cerrados: 2
Trades ganadores: 2 (100% win rate)
Profit total histórico: +$2,000.00
```

**NOTA:** El profit de $2,000 parece anómalo (probablemente trades de prueba con valores erróneos).

---

### 3. **ERROR CRÍTICO EN BASE DE DATOS**

```
ERROR - Error syncing active trades: numeric field overflow
DETAIL: A field with precision 10, scale 5 must round to an absolute value less than 10^5.
```

#### Explicación:
- **NUMERIC(10,5)** permite valores hasta **99,999.99999**
- **BTCUSD** cotiza alrededor de **$43,000**
- **ETHUSD** cotiza alrededor de **$3,920**
- Estos valores NO caben en NUMERIC(10,5)

#### Impacto:
- Los precios de crypto NO se están guardando correctamente
- Los trades de crypto tienen datos corruptos
- El cálculo de pips es INCORRECTO (muestra -343,500 pips en ETHUSD)

---

### 4. **MONITOR DE LOGS NO FUNCIONA**

#### Razón:
El monitor busca patrones específicos en el log que **NO existen** porque:

1. **NO hay señales siendo detectadas** (0 señales en 24h)
2. **NO hay operaciones siendo abiertas** (solo sync de trades manuales)
3. **El formato del log NO coincide** con los regex del monitor

El log solo muestra:
```
INFO - Running job: Analyze crypto signals
INFO - Task completed: analyze_crypto (duration: 0.08s)
```

NO muestra:
```
INFO - BTCUSD - SEÑAL SHORT detectada (3/4 condiciones)  ← ESPERADO
INFO - Position size calculated: 0.01 lots                ← ESPERADO
INFO - Trade OPENED successfully: Ticket 123456          ← ESPERADO
```

---

## 🔍 ANÁLISIS PROFUNDO

### ¿Por qué NO se detectan señales?

Revisando el código de `bridge_v3/main.py`:

```python
def job_analyze_crypto(self):
    """Analiza señales de crypto y ejecuta automáticamente"""
    logger.info("🔍 CRYPTO ANALYSIS STARTING")

    signals = self.strategy_ctrl.analyze_all_crypto()  # ← Obtiene señales

    if not signals:
        logger.info("No crypto signals detected")
        return

    # ... código de ejecución ...
```

**El problema:**
- `analyze_all_crypto()` está retornando lista vacía `[]`
- **NO hay logging de POR QUÉ se rechazan las señales**
- **NO se guardan señales rechazadas en la base de datos**

### ¿Qué está pasando en la estrategia?

Archivo: `crypto_strategy_relaxed.py`

La estrategia requiere:
- RSI < 40 (oversold) o RSI > 60 (overbought)
- 3 de 4 condiciones técnicas
- Precio actual válido

**Posibles problemas:**
1. Los indicadores técnicos NO se están calculando correctamente
2. Los datos de precios están corruptos (por el error NUMERIC)
3. La lógica de 3/4 condiciones es MUY estricta todavía
4. NO hay logging para debug

---

## ✅ SOLUCIONES REQUERIDAS

### PRIORIDAD CRÍTICA

#### 1. **Arreglar Schema de Base de Datos** (URGENTE)

Modificar columnas para soportar precios de crypto:

```sql
-- Aumentar precisión para precios crypto
ALTER TABLE active_trades ALTER COLUMN open_price TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN stop_loss TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN take_profit TYPE NUMERIC(12,2);
ALTER TABLE active_trades ALTER COLUMN current_profit TYPE NUMERIC(12,2);

ALTER TABLE trade_history ALTER COLUMN open_price TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN close_price TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN stop_loss TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN take_profit TYPE NUMERIC(12,2);
ALTER TABLE trade_history ALTER COLUMN profit TYPE NUMERIC(12,2);

ALTER TABLE price_data ALTER COLUMN open TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN high TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN low TYPE NUMERIC(12,5);
ALTER TABLE price_data ALTER COLUMN close TYPE NUMERIC(12,5);
```

#### 2. **Agregar Logging Detallado a la Estrategia**

Modificar `crypto_strategy_relaxed.py` para mostrar:
- Valores actuales de cada indicador
- Qué condiciones se cumplen y cuáles no
- Por qué se rechaza una señal
- Guardar señales rechazadas en DB con razón

#### 3. **Modificar `analyze_all_crypto()` para Logging**

En `bridge_v3/controllers/strategy_controller.py`:

```python
def analyze_all_crypto(self) -> List[TradeSignal]:
    signals = []

    for symbol in self.crypto_pairs:
        logger.info(f"📊 Analyzing {symbol}...")

        # Obtener datos
        df = self.db.get_price_data(symbol, self.crypto_timeframe, limit=100)

        if df is None or len(df) < 50:
            logger.warning(f"⚠️ {symbol}: Insufficient data ({len(df) if df is not None else 0} bars)")
            continue

        # Analizar
        signal_type = self.crypto_strategy.analyze_signal(df, symbol)

        if signal_type == 'LONG' or signal_type == 'SHORT':
            logger.info(f"🔔 {symbol} - SEÑAL {signal_type} detectada!")
            # Crear señal...
        else:
            logger.debug(f"❌ {symbol} - No signal (conditions not met)")

    return signals
```

#### 4. **Cerrar Trades Perdedores Actuales**

Los 2 trades activos están en pérdida y probablemente NO van a recuperar:
- ETHUSD BUY: -$0.34
- LTCUSD SELL: -$0.06

**Recomendación:** Cerrar manualmente en MT5 y empezar de cero.

---

## 📊 SIGUIENTE PASO INMEDIATO

### Crear Script de Diagnóstico Completo

Un script que muestre:
1. ✅ Datos de precios disponibles por símbolo
2. ✅ Indicadores técnicos calculados (RSI, EMA, MACD, etc.)
3. ✅ Condiciones que se cumplen/no cumplen
4. ✅ Por qué NO se genera señal

Esto nos dirá exactamente por qué la estrategia no genera señales.

---

## 🎯 PLAN DE ACCIÓN

```
PASO 1: Arreglar base de datos (schema NUMERIC) ← CRÍTICO
  ├─ Ejecutar ALTER TABLE para columnas de precios
  └─ Verificar que los datos se guarden correctamente

PASO 2: Agregar logging detallado
  ├─ Modificar crypto_strategy_relaxed.py
  ├─ Modificar strategy_controller.py
  └─ Ver EXACTAMENTE por qué no hay señales

PASO 3: Ajustar estrategia según datos
  ├─ Revisar condiciones con datos reales
  ├─ Afinar parámetros (RSI, MACD, etc.)
  └─ Probar con datos históricos

PASO 4: Validar ejecución de trades
  ├─ Verificar que AutoTrading esté ON
  ├─ Probar con 1 señal manual
  └─ Confirmar que se ejecuta correctamente

PASO 5: Monitorear rentabilidad
  ├─ Dejar correr 24-48 horas
  ├─ Analizar win rate y profit
  └─ Ajustar según resultados
```

---

## ⚠️ ADVERTENCIAS

1. **NO ejecutar trading automático hasta arreglar el schema**
   - Los precios corruptos causarán órdenes con valores erróneos
   - Riesgo de pérdidas significativas

2. **NO confiar en las estadísticas actuales**
   - El profit de $2,000 es anómalo
   - Los pips calculados están COMPLETAMENTE MAL

3. **Cerrar trades actuales primero**
   - Ambos están en pérdida
   - Los datos están corruptos (pips negativos enormes)

---

## 📝 CONCLUSIÓN

**Estado actual:** 🔴 SISTEMA NO OPERATIVO

**Problemas críticos:**
1. ❌ NO se detectan señales (0 en 24h)
2. ❌ Base de datos con schema incorrecto
3. ❌ Trades actuales con datos corruptos
4. ❌ NO es rentable (balance -$2.33)
5. ❌ Monitor de logs no funciona (no hay señales que monitorear)

**Acción inmediata requerida:**
1. Arreglar schema de base de datos
2. Agregar logging detallado
3. Diagnosticar por qué no hay señales
4. Cerrar trades actuales

**Tiempo estimado de reparación:** 2-4 horas
