# ⚠️ AUTOMATIC TRADING - CONFIGURACIÓN Y USO

## 🚨 ESTADO ACTUAL: EJECUCIÓN AUTOMÁTICA HABILITADA

El archivo `bridge_v3/main.py` ha sido **modificado** para ejecutar trades automáticamente.

---

## 📍 ¿QUÉ SE MODIFICÓ?

### **Archivo: `bridge_v3/main.py`**

#### **1. Importación del ExecutionController (Línea 28)**
```python
from bridge_v3.controllers import (
    PriceController,
    TradeController,
    RiskController,
    StrategyController,
    ExecutionController  # ← NUEVO: Controller para ejecutar trades
)
```

#### **2. Inicialización del ExecutionController (Línea 102)**
```python
self.execution_ctrl = ExecutionController(self.mt5)
```

#### **3. HABILITACIÓN DE EJECUCIÓN AUTOMÁTICA (Línea 123)** ⚠️
```python
self.execution_ctrl.enable_execution()  # ← AUTOMATIC TRADING ENABLED
```

**🔴 ESTA LÍNEA HABILITA LA EJECUCIÓN AUTOMÁTICA DE TRADES**

#### **4. Lógica de Ejecución (Líneas 285-311)**
```python
if self.execution_ctrl.execution_enabled:
    # Ejecuta el trade
    result = self.execution_ctrl.execute_signal(signal, risk_pct=2.0)

    if result['success']:
        logger.info(f"✅ Trade OPENED: Ticket {result['ticket']}")
        self.trade_ctrl.sync_active_trades()
    else:
        logger.error(f"❌ Trade FAILED: {result['reason']}")
```

---

## 🛑 CÓMO DESACTIVAR LA EJECUCIÓN AUTOMÁTICA

### **Opción 1: Comentar la Línea de Habilitación (RECOMENDADO)**

Editar `bridge_v3/main.py` línea **123**:

**ANTES (Ejecución HABILITADA):**
```python
self.execution_ctrl.enable_execution()  # ← AUTOMATIC TRADING ENABLED
```

**DESPUÉS (Ejecución DESHABILITADA):**
```python
# self.execution_ctrl.enable_execution()  # ← AUTOMATIC TRADING DISABLED
```

**Agregar `#` al inicio de la línea para desactivarla.**

### **Opción 2: Comentar el Bloque de Ejecución**

Editar `bridge_v3/main.py` líneas **285-311**:

Comentar todo el bloque `if self.execution_ctrl.execution_enabled:`:

```python
# if self.execution_ctrl.execution_enabled:
#     result = self.execution_ctrl.execute_signal(signal, risk_pct=2.0)
#     if result['success']:
#         logger.info(f"✅ Trade OPENED: Ticket {result['ticket']}")
#         self.trade_ctrl.sync_active_trades()
#     else:
#         logger.error(f"❌ Trade FAILED: {result['reason']}")
# else:
#     logger.info(f"ℹ️ Signal detected but NOT executed")
```

**Con esto, las señales se registrarán pero NO se ejecutarán.**

---

## ✅ CÓMO VERIFICAR EL ESTADO ACTUAL

Al iniciar el bot, verás uno de estos mensajes:

### **SI ESTÁ HABILITADO:**
```
======================================================================
⚠️  AUTOMATIC TRADING MODE ENABLED  ⚠️
======================================================================
The bot WILL open positions automatically!
Trades will be executed based on detected signals
Risk per trade: 2.0%
Max daily loss: 10.0%
Max positions: 5

To DISABLE automatic trading:
1. Stop the bot (Ctrl+C)
2. Edit bridge_v3/main.py
3. Comment line 123: # self.execution_ctrl.enable_execution()
4. Restart the bot
======================================================================
```

### **SI ESTÁ DESHABILITADO:**
```
Mode: SAFETY MODE (signals logged, NOT executed)
Automatic trading is DISABLED
```

---

## 📊 CÓMO FUNCIONA LA EJECUCIÓN

### **Flujo Completo:**

```
1. SCHEDULER (cada 60 segundos)
   └─► job_analyze_crypto()

2. ANÁLISIS DE SEÑALES
   └─► StrategyController.analyze_crypto_signals()
       └─► Retorna lista de TradeSignal

3. VALIDACIÓN DE RIESGO
   └─► RiskController.can_open_position('crypto')
       ├─► ✅ OK: Continúa
       └─► ❌ BLOQUEADO: Registra warning

4. LOG DE SEÑAL
   └─► StrategyController.log_signal(signal)
       └─► Muestra señal en logs

5. EJECUCIÓN (SI ESTÁ HABILITADO) ← NUEVO
   └─► ExecutionController.execute_signal(signal, risk_pct=2.0)
       ├─► Calcula tamaño de posición
       ├─► Prepara orden MT5
       ├─► Envía orden
       └─► Retorna resultado
           ├─► ✅ SUCCESS: Ticket creado
           └─► ❌ FAILED: Error registrado

6. SINCRONIZACIÓN
   └─► TradeController.sync_active_trades()
       └─► Actualiza base de datos
```

---

## ⚠️ CONFIGURACIÓN DE RIESGO

### **Parámetros Actuales (en código):**

```python
# En job_analyze_crypto() - Línea 289
risk_pct=2.0  # 2% de riesgo por trade
```

### **Límites Globales (en .env):**

```ini
MAX_DAILY_LOSS_PCT=10.0          # Pérdida máxima diaria: 10%
MAX_SIMULTANEOUS_TRADES=5        # Máximo 5 posiciones simultáneas
RISK_PER_TRADE=2.0               # 2% por trade (informativo)
```

### **Límites por Tipo de Activo (hardcoded):**

- **Crypto**: Máximo 3 posiciones
- **Forex**: Máximo 3 posiciones
- **Total**: Máximo 5 posiciones

---

## 📝 LOGS DE EJECUCIÓN

### **Cuando se Ejecuta un Trade:**

```
2025-10-23 00:15:32 - Running job: Analyze crypto signals
2025-10-23 00:15:35 - Crypto signal: BTCUSD - LONG at $45000.00

╔══════════════════════════════════════════════════════════╗
║  Signal Detected: CRYPTO                                 ║
╠══════════════════════════════════════════════════════════╣
║  Symbol: BTCUSD                                          ║
║  Type: LONG                                              ║
║  Price: $45000.00                                        ║
║  Stop Loss: $44100.00                                    ║
║  Take Profit: $46575.00                                  ║
║  R/R: 1:1.75                                             ║
║  Confidence: 80.0%                                       ║
╚══════════════════════════════════════════════════════════╝

2025-10-23 00:15:36 - Position size calculated: 0.22 lots (Risk: $200.00)

╔══════════════════════════════════════════════════════════╗
║  ✅ TRADE EXECUTED SUCCESSFULLY                          ║
╠══════════════════════════════════════════════════════════╣
║  Ticket: 123456789                                       ║
║  Symbol: BTCUSD                                          ║
║  Type: LONG                                              ║
║  Volume: 0.22                                            ║
║  Price: $45010.00                                        ║
║  Stop Loss: $44100.00                                    ║
║  Take Profit: $46575.00                                  ║
║  Strategy: crypto                                        ║
╚══════════════════════════════════════════════════════════╝

2025-10-23 00:15:37 - ✅ Trade OPENED successfully: Ticket 123456789, BTCUSD LONG, Volume 0.22
```

### **Cuando Falla un Trade:**

```
2025-10-23 00:15:37 - ❌ Trade FAILED for ETHUSD: Insufficient margin
```

### **Cuando se Bloquea por Riesgo:**

```
2025-10-23 00:15:37 - ⚠️ Cannot trade LTCUSD: Daily loss limit reached: 10.2%
```

---

## 🔧 MODIFICAR PARÁMETROS DE EJECUCIÓN

### **Cambiar el Riesgo por Trade:**

Editar `bridge_v3/main.py` línea **289**:

```python
# De:
result = self.execution_ctrl.execute_signal(signal, risk_pct=2.0)

# A (ejemplo 1% de riesgo):
result = self.execution_ctrl.execute_signal(signal, risk_pct=1.0)

# A (ejemplo 3% de riesgo - MÁS AGRESIVO):
result = self.execution_ctrl.execute_signal(signal, risk_pct=3.0)
```

### **Cambiar Límites Globales:**

Editar `.env`:

```ini
# Conservador
MAX_DAILY_LOSS_PCT=5.0           # 5% límite diario
MAX_SIMULTANEOUS_TRADES=3        # Máx 3 posiciones

# Estándar (actual)
MAX_DAILY_LOSS_PCT=10.0          # 10% límite diario
MAX_SIMULTANEOUS_TRADES=5        # Máx 5 posiciones

# Agresivo (NO RECOMENDADO para principiantes)
MAX_DAILY_LOSS_PCT=20.0          # 20% límite diario
MAX_SIMULTANEOUS_TRADES=10       # Máx 10 posiciones
```

---

## 🆘 COMANDOS DE EMERGENCIA

### **Cerrar TODAS las Posiciones Inmediatamente:**

```python
# Abrir Python en la terminal
python

# Ejecutar:
from bridge_v3.services import MT5Service, DatabaseService, RedisService
from bridge_v3.controllers import TradeController

mt5 = MT5Service()
mt5.initialize()

db = DatabaseService()
db.connect()

redis = RedisService()
redis.connect()

trade_ctrl = TradeController(mt5, db, redis)

# Cerrar TODAS las posiciones
result = trade_ctrl.close_all_trades()
print(f"Cerradas: {result['closed']}, Fallidas: {result['failed']}")

# Cleanup
mt5.shutdown()
```

### **Cerrar Solo Crypto:**

```python
result = trade_ctrl.close_all_trades(strategy='crypto')
```

### **Cerrar Solo Forex:**

```python
result = trade_ctrl.close_all_trades(strategy='forex')
```

---

## ✅ CHECKLIST ANTES DE USAR

- [ ] **¿Estás usando cuenta DEMO?**
      - ⚠️ **NUNCA uses cuenta REAL sin testing previo**
- [ ] **¿Has validado la estrategia?**
      - Backtest con datos históricos
      - Forward test en DEMO por 1 semana mínimo
- [ ] **¿Has configurado límites de riesgo?**
      - MAX_DAILY_LOSS_PCT razonable (5-10%)
      - RISK_PER_TRADE conservador (1-2%)
- [ ] **¿Tienes plan de monitoreo?**
      - Revisar logs cada hora
      - Dashboard activo
      - Alertas configuradas
- [ ] **¿Tienes plan de emergencia?**
      - Sabes cómo cerrar todas las posiciones
      - Sabes cómo detener el bot
      - Tienes respaldo del capital

---

## 📚 DOCUMENTACIÓN RELACIONADA

- **EXECUTION_GUIDE.md** - Guía completa de ejecución
- **BRIDGE_V3_README.md** - Documentación general V3
- **MIGRATION_GUIDE.md** - Migración desde V2

---

## 🎯 RESUMEN DE CAMBIOS

| Archivo | Línea | Cambio | Estado |
|---------|-------|--------|--------|
| `main.py` | 28 | Import ExecutionController | ✅ Agregado |
| `main.py` | 53 | Declarar execution_ctrl | ✅ Agregado |
| `main.py` | 102 | Inicializar ExecutionController | ✅ Agregado |
| `main.py` | 123 | **enable_execution()** | 🔴 **HABILITADO** |
| `main.py` | 249-318 | Función analyze_and_execute | ✅ Modificado |
| `main.py` | 285-311 | Bloque de ejecución automática | 🔴 **ACTIVO** |
| `main.py` | 394-409 | Mensaje de advertencia en logs | ✅ Agregado |

---

## ⚠️ ADVERTENCIA FINAL

**🚨 LA EJECUCIÓN AUTOMÁTICA ESTÁ HABILITADA 🚨**

Al ejecutar `python -m bridge_v3.main`, el bot:

1. ✅ Analizará señales cada 60 segundos
2. ✅ Validará límites de riesgo
3. 🔴 **EJECUTARÁ TRADES AUTOMÁTICAMENTE**
4. ✅ Registrará todo en logs

**Para DESACTIVAR:**
- Editar `bridge_v3/main.py` línea 123
- Comentar: `# self.execution_ctrl.enable_execution()`
- Reiniciar el bot

**Recuerda:**
- 🎯 Probar en DEMO primero
- 📊 Monitorear constantemente
- 🛡️ Tener plan de emergencia
- 💰 No arriesgar más de lo que puedes perder

---

**Última actualización:** 2025-10-23
**Estado:** EJECUCIÓN AUTOMÁTICA HABILITADA ⚠️
