# Guía de Ejecución de Trades - Bridge V3

## 🎯 Capacidades de Trading

Bridge V3 tiene **CAPACIDADES COMPLETAS** para abrir y cerrar operaciones:

### ✅ **Funcionalidades Implementadas**

| Funcionalidad | Estado | Ubicación |
|---------------|--------|-----------|
| **Cerrar posiciones** | ✅ **Funcional** | `TradeController.close_trade()` |
| **Cerrar todas las posiciones** | ✅ **Funcional** | `TradeController.close_all_trades()` |
| **Analizar señales** | ✅ **Funcional** | `StrategyController.analyze_crypto_signals()` |
| **Validar riesgos** | ✅ **Funcional** | `RiskController.can_open_position()` |
| **Abrir posiciones** | ✅ **Funcional** | `ExecutionController.execute_signal()` |
| **Calcular tamaño de posición** | ✅ **Funcional** | `ExecutionController._calculate_position_size()` |

---

## 🔐 **Modo de Seguridad (Actual)**

Por defecto, Bridge V3 está en **MODO SEGURIDAD**:
- ✅ Analiza señales
- ✅ Valida riesgos
- ✅ Registra señales en logs
- ❌ **NO ejecuta trades automáticamente**

Esto es **INTENCIONAL** para prevenir pérdidas accidentales.

---

## 🚀 **Cómo Habilitar Ejecución Automática**

### **Opción 1: Modificar main.py (Para Ejecución Permanente)**

Edita `bridge_v3/main.py` para agregar el ExecutionController:

```python
# En la clase MT5BridgeV3.__init__
from bridge_v3.controllers import (
    PriceController,
    TradeController,
    RiskController,
    StrategyController,
    ExecutionController  # ← Agregar
)

def __init__(self):
    # ... código existente ...

    # Controllers
    self.price_ctrl = None
    self.trade_ctrl = None
    self.risk_ctrl = None
    self.strategy_ctrl = None
    self.execution_ctrl = None  # ← Agregar

def initialize(self):
    # ... después de inicializar otros controllers ...

    self.execution_ctrl = ExecutionController(self.mt5)

    # ⚠️ PELIGRO: Habilitar ejecución automática
    # self.execution_ctrl.enable_execution()  # Descomentar para activar

    logger.info("Execution controller initialized (safety mode)")

def job_analyze_crypto(self):
    """Job: Analyze crypto signals"""
    logger.info("Running job: Analyze crypto signals")

    def analyze_and_execute():  # ← Renombrar
        signals = self.strategy_ctrl.analyze_crypto_signals()

        for signal in signals:
            # Check if can trade
            can_trade, reason = self.risk_ctrl.can_open_position('crypto')

            if can_trade:
                # Log signal
                self.strategy_ctrl.log_signal(signal)

                # ⚠️ EJECUTAR TRADE (si está habilitado)
                if self.execution_ctrl.execution_enabled:
                    result = self.execution_ctrl.execute_signal(signal, risk_pct=2.0)
                    if result['success']:
                        logger.info(f"✅ Trade opened: Ticket {result['ticket']}")
                    else:
                        logger.error(f"❌ Trade failed: {result['reason']}")
            else:
                logger.warning(f"Cannot trade {signal.symbol}: {reason}")

    task = Task(
        name='analyze_crypto',
        function=analyze_and_execute,  # ← Actualizar
        priority=TaskPriority.NORMAL
    )

    self.worker.submit_task(task)
```

### **Opción 2: Crear Script de Ejecución Manual**

Crear `windows-mt5-bridge/execute_signal_manual.py`:

```python
"""
Script manual para ejecutar señales específicas
Usar con precaución en cuenta DEMO primero
"""

import sys
sys.path.append('.')

from bridge_v3.config import Settings
from bridge_v3.services import MT5Service, LoggerService
from bridge_v3.controllers import ExecutionController
from bridge_v3.models import TradeSignal, SignalType
from datetime import datetime

# Setup logging
LoggerService.setup()
logger = LoggerService.get_logger(__name__)

def main():
    # Inicializar MT5
    mt5 = MT5Service()
    if not mt5.initialize():
        logger.error("Failed to initialize MT5")
        return

    # Crear execution controller
    execution = ExecutionController(mt5)

    # ⚠️ HABILITAR EJECUCIÓN
    execution.enable_execution()

    # Crear señal manual (EJEMPLO)
    signal = TradeSignal(
        symbol='EURUSD',
        signal_type=SignalType.LONG,
        strategy='manual',
        price=1.10000,
        stop_loss=1.09800,  # 20 pips SL
        take_profit=1.10400,  # 40 pips TP
        timestamp=datetime.now(),
        confidence=0.9,
        reason='Manual test signal'
    )

    # Ejecutar señal
    logger.info("Executing manual signal...")
    result = execution.execute_signal(signal, risk_pct=1.0)  # 1% risk

    if result['success']:
        logger.info(f"✅ Success! Ticket: {result['ticket']}")
    else:
        logger.error(f"❌ Failed: {result['reason']}")

    # Cleanup
    mt5.shutdown()

if __name__ == "__main__":
    main()
```

Ejecutar:
```powershell
python execute_signal_manual.py
```

---

## 📊 **Cómo Funciona la Ejecución**

### **1. Análisis de Señal**
```python
StrategyController.analyze_crypto_signals()
# → Retorna lista de TradeSignal con:
#    - symbol: BTCUSD
#    - signal_type: LONG/SHORT
#    - price: 45000.00
#    - stop_loss: 44100.00 (2% SL)
#    - take_profit: 46575.00 (3.5% TP)
#    - confidence: 0.8
```

### **2. Validación de Riesgo**
```python
RiskController.can_open_position('crypto')
# → Verifica:
#    ✅ Pérdida diaria < 10%
#    ✅ Posiciones totales < 5
#    ✅ Posiciones crypto < 3
# → Retorna: (True, "OK") o (False, "Razón")
```

### **3. Cálculo de Tamaño de Posición**
```python
ExecutionController._calculate_position_size(
    balance=10000,
    entry_price=45000,
    stop_loss=44100,
    risk_pct=2.0
)
# → Calcula volumen en lotes
# → Riesgo = $10,000 × 2% = $200
# → SL distancia = 45000 - 44100 = $900
# → Volumen = $200 / $900 = 0.22 lotes
```

### **4. Ejecución de Orden**
```python
ExecutionController.execute_signal(signal)
# → Prepara request MT5
# → Envía orden via mt5.order_send()
# → Retorna ticket si éxito
```

---

## 🔢 **Ejemplo de Ejecución Real**

```
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

Risk Check: ✅ OK (Daily loss: 2.3%, Positions: 2/5)

Calculating position size...
- Balance: $10,000
- Risk: 2% = $200
- SL distance: $900
- Volume: 0.22 lots

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
```

---

## ⚠️ **ADVERTENCIAS IMPORTANTES**

### **ANTES de Habilitar Ejecución Automática:**

1. **✅ Probar en cuenta DEMO primero**
   ```ini
   # .env
   MT5_ACCOUNT=demo_account_number
   MT5_SERVER=YourBroker-Demo
   ```

2. **✅ Configurar límites de riesgo**
   ```ini
   MAX_DAILY_LOSS_PCT=5.0      # Límite diario 5%
   RISK_PER_TRADE=1.0          # 1% por trade (conservador)
   MAX_SIMULTANEOUS_TRADES=3   # Máx 3 posiciones
   ```

3. **✅ Validar estrategia en backtest**
   - No ejecutar sin backtest previo
   - Verificar winrate y profit factor

4. **✅ Monitorear constantemente**
   ```powershell
   Get-Content mt5_bridge_v3.log -Wait -Tail 50
   ```

5. **✅ Tener plan de emergencia**
   ```python
   # En caso de problemas:
   trade_ctrl.close_all_trades()  # Cierra todo
   ```

---

## 🛡️ **Protecciones Implementadas**

### **1. Límite de Pérdida Diaria**
```python
if daily_loss >= 10%:
    return False, "Daily loss limit reached"
```

### **2. Límite de Posiciones**
```python
if total_positions >= MAX_SIMULTANEOUS_TRADES:
    return False, "Max positions reached"
```

### **3. Límite por Tipo de Activo**
```python
if crypto_positions >= 3:
    return False, "Max crypto positions reached"
```

### **4. Validación de Tamaño**
```python
position_size = max(symbol_info.volume_min, position_size)
position_size = min(symbol_info.volume_max, position_size)
```

### **5. Flag de Seguridad**
```python
if not self.execution_enabled:
    return {'success': False, 'reason': 'Execution disabled'}
```

---

## 📝 **Checklist antes de Activar**

- [ ] Probado en cuenta DEMO
- [ ] Backtest completado con resultados positivos
- [ ] Límites de riesgo configurados
- [ ] Monitoreo configurado (logs, dashboard)
- [ ] Plan de emergencia documentado
- [ ] Capital de prueba definido (no más del que puedas perder)
- [ ] Horarios de trading definidos
- [ ] Pares de trading seleccionados
- [ ] Estrategia validada manualmente
- [ ] Código revisado y entendido

---

## 🔧 **Comandos Útiles**

### **Cerrar Todas las Posiciones (Emergencia)**
```python
from bridge_v3.services import MT5Service
from bridge_v3.controllers import TradeController

mt5 = MT5Service()
mt5.initialize()

trade_ctrl = TradeController(mt5, db, redis)
result = trade_ctrl.close_all_trades()  # Cierra TODAS

print(f"Closed: {result['closed']}, Failed: {result['failed']}")
```

### **Cerrar Solo Crypto**
```python
result = trade_ctrl.close_all_trades(strategy='crypto')
```

### **Cerrar Solo Forex**
```python
result = trade_ctrl.close_all_trades(strategy='forex')
```

### **Cerrar Posición Específica**
```python
trade_ctrl.close_trade(ticket=123456789)
```

---

## 📊 **Monitoreo en Tiempo Real**

### **Ver Ejecuciones en Logs**
```powershell
# Ver todas las ejecuciones
Get-Content mt5_bridge_v3.log | Select-String "TRADE EXECUTED"

# Ver señales detectadas
Get-Content mt5_bridge_v3.log | Select-String "Signal Detected"

# Ver errores
Get-Content mt5_bridge_v3.log | Select-String "ERROR"
```

### **Dashboard (Linux Server)**
```
http://your-server-ip:8501
```

---

## 🎓 **Conclusión**

### **Bridge V3 SÍ puede abrir y cerrar operaciones:**

| Funcionalidad | Estado |
|---------------|--------|
| **Cerrar trades** | ✅ Funcional ahora |
| **Abrir trades** | ✅ Funcional (desactivado por defecto) |
| **Análisis de señales** | ✅ Funcional |
| **Gestión de riesgo** | ✅ Funcional |
| **Cálculo de volumen** | ✅ Funcional |

### **Para Activar:**
1. Importar `ExecutionController` en `main.py`
2. Llamar `execution_ctrl.enable_execution()`
3. Modificar `job_analyze_crypto()` para ejecutar señales
4. **Probar en DEMO primero**

### **Modo Actual:**
- 🛡️ **SAFETY MODE** (solo registra señales)
- Esto es **intencional** para evitar pérdidas accidentales
- Requiere activación manual explícita

---

**¿Listo para activar? Recuerda: DEMO primero! 🎯**
