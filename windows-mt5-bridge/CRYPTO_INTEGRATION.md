# Integración de Estrategia de Criptomonedas

## 📋 Archivos Creados

✅ **crypto_strategy.py** - Estrategia completa de criptomonedas
✅ **risk_manager.py** - Gestión de riesgo integrada
✅ **.env actualizado** - Configuración de cripto y parámetros

## 🚀 Implementación Paso a Paso

### Paso 1: Verificar que los módulos están instalados

Los módulos `crypto_strategy.py` y `risk_manager.py` ya están creados en el directorio actual.

### Paso 2: Detener el bridge actual

```powershell
# En la terminal donde está corriendo mt5_bridge.py, presiona Ctrl+C
```

### Paso 3: Hacer backup del bridge actual

```powershell
copy mt5_bridge.py mt5_bridge_backup.py
```

### Paso 4: Modificar mt5_bridge.py

Agrega estas importaciones al inicio del archivo:

```python
from crypto_strategy import CryptoStrategy
from risk_manager import RiskManager
```

### Paso 5: Actualizar la clase MT5Bridge

En el método `__init__`, agrega:

```python
# En MT5Bridge.__init__ después de las líneas existentes:

# Crypto configuration
self.crypto_enabled = os.getenv('CRYPTO_ENABLED', 'false').lower() == 'true'
self.crypto_pairs = os.getenv('CRYPTO_PAIRS', '').split(',') if self.crypto_enabled else []
self.crypto_timeframe = int(os.getenv('CRYPTO_TIMEFRAME', '15'))

# Forex configuration (renombrar TRADING_PAIRS)
self.forex_pairs = os.getenv('FOREX_PAIRS', 'EURUSD,GBPUSD').split(',')
self.forex_timeframe = os.getenv('FOREX_TIMEFRAME', 'M15')

# Strategies
self.crypto_strategy = CryptoStrategy() if self.crypto_enabled else None
self.risk_manager = None  # Se inicializará después de conectar a Redis
```

### Paso 6: Inicializar Risk Manager

Después de `setup_redis()`, agrega:

```python
def setup_risk_manager(self):
    """Initialize risk manager"""
    if self.redis_client:
        max_loss_pct = float(os.getenv('MAX_DAILY_LOSS_PCT', '10.0'))
        self.risk_manager = RiskManager(self.redis_client, max_loss_pct)
        logger.info("Risk Manager initialized")
```

Y llámalo en el método `run()`:

```python
# En run(), después de setup_redis():
self.setup_risk_manager()
```

### Paso 7: Agregar método para analizar criptomonedas

Agrega este método a la clase `MT5Bridge`:

```python
def analyze_crypto_signals(self):
    """Analyze crypto signals"""
    if not self.crypto_enabled or not self.mt5_initialized:
        return

    try:
        for symbol in self.crypto_pairs:
            symbol = symbol.strip()

            # Fetch data
            tf_mapping = {
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1
            }

            timeframe = tf_mapping.get(self.crypto_timeframe, mt5.TIMEFRAME_M15)
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 200)

            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {symbol}")
                continue

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            # Analyze signal
            signal = self.crypto_strategy.analyze_signal(df, symbol)

            if signal:
                logger.info(f"🪙 {symbol}: Señal {signal} detectada")

                # Check if can open position
                account_info = mt5.account_info()
                can_trade, reason = self.risk_manager.can_open_position('crypto', account_info.balance)

                if can_trade:
                    self.execute_crypto_trade(symbol, signal, df['close'].iloc[-1])
                else:
                    logger.warning(f"No se puede abrir posición en {symbol}: {reason}")

    except Exception as e:
        logger.error(f"Error analyzing crypto signals: {e}")
        import traceback
        traceback.print_exc()
```

### Paso 8: Agregar método para ejecutar trades de crypto

```python
def execute_crypto_trade(self, symbol, signal_type, current_price):
    """Execute crypto trade (DEMO - Solo logging por ahora)"""

    logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║  🪙 SEÑAL DE CRYPTO DETECTADA                            ║
╠══════════════════════════════════════════════════════════╣
║  Símbolo: {symbol:<45} ║
║  Tipo: {signal_type:<48} ║
║  Precio: ${current_price:<45.2f} ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Calculate SL and TP
    sl, tp = self.crypto_strategy.calculate_sl_tp(current_price, signal_type)

    logger.info(f"  Stop Loss: ${sl:.2f}")
    logger.info(f"  Take Profit: ${tp:.2f}")

    # Por seguridad, primero solo registrar señales
    # Descomentar para ejecutar trades reales:
    # self._execute_mt5_order(symbol, signal_type, sl, tp)
```

### Paso 9: Programar análisis de crypto

En el método `run()`, después de programar las tareas existentes, agrega:

```python
# Crypto signals analysis (si está habilitado)
if self.crypto_enabled:
    schedule.every(1).minutes.do(self.analyze_crypto_signals)
    logger.info("  - Analyze crypto signals: Every 1 minute")
```

### Paso 10: Actualizar referencias a TRADING_PAIRS

Busca todas las referencias a `TRADING_PAIRS` y cámbialas por `self.forex_pairs`.

Por ejemplo, en `job_fetch_prices`:

```python
def job_fetch_prices(self):
    """Scheduled job: Fetch and store price data"""
    logger.info("Running job: Fetch prices")

    # Forex
    for symbol in self.forex_pairs:
        df = self.fetch_price_data(symbol, self.forex_timeframe)
        if df is not None:
            self.store_price_data(df)

    # Crypto (si está habilitado)
    if self.crypto_enabled:
        for symbol in self.crypto_pairs:
            symbol = symbol.strip()
            tf_mapping = {
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1
            }
            timeframe = tf_mapping.get(self.crypto_timeframe, mt5.TIMEFRAME_M15)
            df = self.fetch_price_data(symbol, f"M{self.crypto_timeframe}")
            if df is not None:
                self.store_price_data(df)
```

## 🧪 Modo de Prueba (Recomendado)

Para probar SIN ejecutar trades reales:

1. En `.env`, asegúrate que `CRYPTO_ENABLED=false` inicialmente
2. Modifica el código para solo registrar señales (ya incluido en `execute_crypto_trade`)
3. Ejecuta el bridge y verifica que las señales se detecten correctamente
4. Una vez validado, activa `CRYPTO_ENABLED=true` y descomenta la línea de ejecución real

## ⚙️ Script de Prueba Rápido

Alternativamente, usa este script para probar solo el análisis:

```python
# test_crypto_live.py
import os
from dotenv import load_dotenv
import MetaTrader5 as mt5
import pandas as pd
from crypto_strategy import CryptoStrategy

load_dotenv()

# Initialize MT5
mt5.initialize()
mt5.login(
    int(os.getenv('MT5_ACCOUNT')),
    os.getenv('MT5_PASSWORD'),
    os.getenv('MT5_SERVER')
)

strategy = CryptoStrategy()

# Test con BTCUSD
rates = mt5.copy_rates_from_pos('BTCUSD', mt5.TIMEFRAME_M15, 0, 200)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

signal = strategy.analyze_signal(df, 'BTCUSD')
print(f"Señal detectada: {signal}")

mt5.shutdown()
```

## 📊 Verificación

Después de implementar:

1. **Sin crypto habilitado**: El sistema debe funcionar exactamente igual que antes
2. **Con crypto habilitado**: Debe ver logs de análisis de crypto cada minuto
3. **Con señal detectada**: Debe ver el cuadro con la información de la señal

## 🔧 Troubleshooting

**Error: ModuleNotFoundError**
```powershell
# Verificar que los archivos existan:
ls crypto_strategy.py
ls risk_manager.py
```

**Error: can_open_position not defined**
```python
# Asegúrate de inicializar risk_manager antes de usarlo
if not self.risk_manager:
    logger.error("Risk manager not initialized")
    return
```

**No se detectan señales**
```python
# Verificar que los símbolos existan en MT5:
import MetaTrader5 as mt5
mt5.initialize()
symbols = mt5.symbols_get()
for s in symbols:
    if 'BTC' in s.name or 'ETH' in s.name:
        print(s.name)
```

## 📝 Checklist Final

- [ ] Backup del mt5_bridge.py actual
- [ ] Módulos crypto_strategy.py y risk_manager.py creados
- [ ] .env actualizado con configuración de crypto
- [ ] Importaciones agregadas
- [ ] Risk Manager inicializado
- [ ] Método analyze_crypto_signals agregado
- [ ] Método execute_crypto_trade agregado
- [ ] Tarea programada para crypto
- [ ] Referencias a TRADING_PAIRS actualizadas
- [ ] Script de prueba ejecutado exitosamente
- [ ] Bridge v2 probado en modo seguro

## 🎯 Próximos Pasos

Una vez que todo funcione:

1. Dejar correr en modo análisis (sin ejecutar) por 24-48 horas
2. Revisar las señales detectadas
3. Ajustar parámetros si es necesario
4. Activar ejecución real con capital pequeño
5. Monitorear durante 1 semana
6. Escalar gradualmente
