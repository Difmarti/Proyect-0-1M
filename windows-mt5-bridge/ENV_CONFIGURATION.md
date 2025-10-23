# 📘 Guía Completa de Configuración (.env)

Esta guía explica cada parámetro del archivo `.env` y cómo modificarlo para optimizar el bot de trading.

---

## 🔐 MT5 Configuration (Windows)

### `MT5_ACCOUNT`
**Descripción:** Número de cuenta de MetaTrader 5
**Tipo:** Número entero
**Ejemplo:** `MT5_ACCOUNT=25251142`
**¿Cómo obtenerlo?**
1. Abre MT5
2. Ve a Herramientas → Opciones → Servidor
3. Copia el número de cuenta

**⚠️ Importante:** Este es tu identificador único de cuenta.

---

### `MT5_PASSWORD`
**Descripción:** Contraseña de tu cuenta MT5
**Tipo:** Texto (puede incluir caracteres especiales)
**Ejemplo:** `MT5_PASSWORD=sW2ik=6z*=c|`
**¿Dónde encontrarla?** Es la contraseña que usas para iniciar sesión en MT5

**🔒 Seguridad:**
- NUNCA compartas este archivo
- NUNCA lo subas a repositorios públicos
- Usa contraseñas fuertes

---

### `MT5_SERVER`
**Descripción:** Servidor del broker
**Tipo:** Texto
**Valores comunes:**
- `Tickmill-Demo` (cuenta demo)
- `Tickmill-Live` (cuenta real)
- `Tickmill-Pro` (cuenta profesional)

**Ejemplo:** `MT5_SERVER=Tickmill-Demo`

**¿Cómo saberlo?**
1. Abre MT5
2. Ve a Herramientas → Opciones → Servidor
3. Copia el nombre exacto del servidor

---

### `MT5_PATH`
**Descripción:** Ruta completa al ejecutable de MT5 (opcional)
**Tipo:** Ruta de archivo
**Ejemplo:** `MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe`

**¿Cuándo usarlo?**
- Si MT5 está en una ubicación no estándar
- Si tienes múltiples instalaciones de MT5
- Si el script no detecta MT5 automáticamente

**¿Cómo encontrar la ruta?**
1. Click derecho en el ícono de MT5
2. Propiedades → Buscar destino
3. Copia la ruta completa

**Nota:** Si está vacío, el script intentará auto-detectar MT5

---

## 💾 Linux Server Database (PostgreSQL)

### `POSTGRES_HOST`
**Descripción:** Dirección IP del servidor PostgreSQL
**Tipo:** IP o hostname
**Ejemplo:** `POSTGRES_HOST=10.30.90.102`

**Valores posibles:**
- `localhost` - Si está en la misma máquina
- `192.168.1.100` - IP local en red
- `10.30.90.102` - IP específica de servidor

**¿Cómo obtenerla?**
```powershell
# En Windows:
ipconfig

# En Linux:
ip addr show
```

---

### `POSTGRES_PORT`
**Descripción:** Puerto de PostgreSQL
**Tipo:** Número entero
**Valor por defecto:** `5432`
**Ejemplo:** `POSTGRES_PORT=5432`

**¿Cuándo cambiar?**
- Si configuraste PostgreSQL en otro puerto
- Si hay conflicto de puertos

---

### `POSTGRES_DB`
**Descripción:** Nombre de la base de datos
**Tipo:** Texto
**Valor por defecto:** `trading_db`
**Ejemplo:** `POSTGRES_DB=trading_db`

**No cambiar** a menos que hayas creado una base de datos con otro nombre.

---

### `POSTGRES_USER`
**Descripción:** Usuario de PostgreSQL
**Tipo:** Texto
**Valor por defecto:** `trading_user`
**Ejemplo:** `POSTGRES_USER=trading_user`

---

### `POSTGRES_PASSWORD`
**Descripción:** Contraseña de PostgreSQL
**Tipo:** Texto
**Ejemplo:** `POSTGRES_PASSWORD=Secure7319`

**🔒 Seguridad:** Usa una contraseña fuerte generada aleatoriamente.

---

## 🔴 Linux Server Cache (Redis)

### `REDIS_HOST`
**Descripción:** Dirección IP del servidor Redis
**Tipo:** IP o hostname
**Ejemplo:** `REDIS_HOST=10.30.90.102`

**Nota:** Generalmente es la misma IP que PostgreSQL.

---

### `REDIS_PORT`
**Descripción:** Puerto de Redis
**Tipo:** Número entero
**Valor por defecto:** `6379`
**Ejemplo:** `REDIS_PORT=6379`

---

### `REDIS_DB`
**Descripción:** Número de base de datos Redis
**Tipo:** Número entero (0-15)
**Valor por defecto:** `0`
**Ejemplo:** `REDIS_DB=0`

**¿Cuándo cambiar?** Si quieres separar los datos de diferentes bots.

---

## 📈 Trading Configuration - FOREX

### `FOREX_PAIRS`
**Descripción:** Pares de divisas a tradear (separados por comas)
**Tipo:** Lista de símbolos
**Ejemplo:** `FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD`

**Pares disponibles en Tickmill:**
- EURUSD - Euro vs Dólar
- GBPUSD - Libra vs Dólar
- USDJPY - Dólar vs Yen
- AUDUSD - Dólar Australiano vs Dólar
- USDCAD - Dólar vs Dólar Canadiense
- EURJPY, EURGBP, etc.

**¿Cómo agregar/quitar pares?**
```env
# Solo EURUSD y GBPUSD:
FOREX_PAIRS=EURUSD,GBPUSD

# Agregar más:
FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,EURJPY,AUDUSD
```

**⚠️ Recomendación:** Comienza con 3-5 pares para evitar sobre-operación.

---

### `FOREX_TIMEFRAME`
**Descripción:** Marco temporal para análisis de Forex
**Tipo:** Texto
**Valores:** `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`
**Ejemplo:** `FOREX_TIMEFRAME=M15`

**Significado:**
- `M1` = 1 minuto (scalping ultra rápido)
- `M5` = 5 minutos (scalping)
- `M15` = 15 minutos (day trading)
- `M30` = 30 minutos
- `H1` = 1 hora (swing trading)
- `H4` = 4 horas
- `D1` = 1 día (position trading)

**¿Cuál elegir?**
- **Scalping**: M1, M5 (requiere mucha atención)
- **Day Trading**: M15, M30 (equilibrio)
- **Swing Trading**: H1, H4 (menos operaciones)

---

## 🪙 Trading Configuration - CRYPTO

### `CRYPTO_PAIRS`
**Descripción:** Pares de criptomonedas a tradear
**Tipo:** Lista de símbolos
**Ejemplo:** `CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD`

**Disponibles en Tickmill:**
- BTCUSD - Bitcoin
- ETHUSD - Ethereum
- LTCUSD - Litecoin
- XRPUSD - Ripple
- BCHUSD - Bitcoin Cash
- Otros (verificar en MT5)

**Modificar:**
```env
# Solo Bitcoin y Ethereum:
CRYPTO_PAIRS=BTCUSD,ETHUSD

# Agregar más:
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD,BCHUSD
```

---

### `CRYPTO_TIMEFRAME`
**Descripción:** Marco temporal para crypto (en minutos)
**Tipo:** Número entero
**Valores:** `5`, `15`, `30`, `60`
**Ejemplo:** `CRYPTO_TIMEFRAME=15`

**¿Cuál usar?**
- `5` - Scalping muy rápido (muchas operaciones)
- `15` - **Recomendado** (equilibrio)
- `30` - Menos señales, más tiempo
- `60` - Swing trading

---

### `CRYPTO_ENABLED`
**Descripción:** Activar/desactivar trading de crypto
**Tipo:** Booleano
**Valores:** `true` o `false`
**Ejemplo:** `CRYPTO_ENABLED=true`

**Uso:**
```env
CRYPTO_ENABLED=true   # Activar crypto
CRYPTO_ENABLED=false  # Solo Forex
```

**⚠️ Importante:** Empieza con `false` para probar solo Forex, luego activa crypto.

---

## ⚠️ Risk Management

### `MAX_DAILY_LOSS_PCT`
**Descripción:** Pérdida máxima permitida por día (%)
**Tipo:** Número decimal
**Rango:** 1.0 - 20.0
**Valor por defecto:** `10.0`
**Ejemplo:** `MAX_DAILY_LOSS_PCT=10.0`

**¿Qué hace?**
Si pierdes este porcentaje de tu capital en un día, el bot **DETIENE** todas las operaciones hasta el día siguiente.

**Ejemplos:**
```env
MAX_DAILY_LOSS_PCT=5.0   # Conservador (detiene al 5%)
MAX_DAILY_LOSS_PCT=10.0  # Moderado (recomendado)
MAX_DAILY_LOSS_PCT=15.0  # Agresivo (más riesgo)
```

**⚠️ NO pongas más de 15%** - Protección de capital es crucial.

---

### `MAX_FOREX_POSITIONS`
**Descripción:** Máximo de posiciones Forex abiertas simultáneamente
**Tipo:** Número entero
**Rango:** 1 - 10
**Valor por defecto:** `3`
**Ejemplo:** `MAX_FOREX_POSITIONS=3`

**¿Cómo ajustar?**
```env
MAX_FOREX_POSITIONS=1   # Muy conservador
MAX_FOREX_POSITIONS=3   # Recomendado
MAX_FOREX_POSITIONS=5   # Agresivo
```

---

### `MAX_CRYPTO_POSITIONS`
**Descripción:** Máximo de posiciones Crypto abiertas simultáneamente
**Tipo:** Número entero
**Rango:** 1 - 5
**Valor por defecto:** `3`
**Ejemplo:** `MAX_CRYPTO_POSITIONS=3`

---

### `MAX_TOTAL_POSITIONS`
**Descripción:** Máximo total de posiciones (Forex + Crypto)
**Tipo:** Número entero
**Valor por defecto:** `5`
**Ejemplo:** `MAX_TOTAL_POSITIONS=5`

**Lógica:**
```
Si tienes 2 Forex abiertos y 3 Crypto abiertos = 5 total
No podrás abrir más aunque no hayas llegado al límite individual
```

**Configuración segura:**
```env
MAX_FOREX_POSITIONS=3
MAX_CRYPTO_POSITIONS=3
MAX_TOTAL_POSITIONS=5  # Nunca más de 5 en total
```

---

### `CRYPTO_STOP_LOSS_PCT`
**Descripción:** Stop Loss para crypto (%)
**Tipo:** Número decimal
**Rango:** 1.0 - 5.0
**Valor por defecto:** `2.0`
**Ejemplo:** `CRYPTO_STOP_LOSS_PCT=2.0`

**¿Qué significa?**
Si el precio va 2% en contra, cierra automáticamente la posición.

**Ejemplos:**
```env
CRYPTO_STOP_LOSS_PCT=1.5  # Muy ajustado (más operaciones perdedoras cortas)
CRYPTO_STOP_LOSS_PCT=2.0  # Equilibrado (recomendado)
CRYPTO_STOP_LOSS_PCT=3.0  # Más amplio (menos falsos stops)
```

**Para BTC a $100,000:**
- SL 1.5% = $98,500
- SL 2.0% = $98,000
- SL 3.0% = $97,000

---

### `CRYPTO_TAKE_PROFIT_PCT`
**Descripción:** Take Profit para crypto (%)
**Tipo:** Número decimal
**Rango:** 2.0 - 10.0
**Valor por defecto:** `3.5`
**Ejemplo:** `CRYPTO_TAKE_PROFIT_PCT=3.5`

**¿Qué hace?**
Cierra automáticamente cuando la ganancia alcanza este porcentaje.

**Relación con Stop Loss:**
```env
# Risk/Reward 1:1.5 (conservador)
CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=3.0

# Risk/Reward 1:1.75 (equilibrado) - RECOMENDADO
CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=3.5

# Risk/Reward 1:2 (agresivo)
CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=4.0
```

---

### `CRYPTO_TRAILING_STOP_ACTIVATION`
**Descripción:** % de ganancia para activar trailing stop
**Tipo:** Número decimal
**Valor por defecto:** `2.0`
**Ejemplo:** `CRYPTO_TRAILING_STOP_ACTIVATION=2.0`

**¿Qué hace?**
Cuando la posición está ganando 2%, activa el trailing stop que sigue el precio.

**Ejemplo:**
1. Compras BTC a $100,000
2. Sube a $102,000 (+2%) → **Trailing stop se activa**
3. Sube a $104,000 → Trailing stop sube a $103,000 (-1%)
4. Sube a $105,000 → Trailing stop sube a $104,000 (-1%)
5. Cae a $104,000 → **Se cierra automáticamente** protegiendo $4,000 de ganancia

---

### `CRYPTO_TRAILING_STOP_DISTANCE`
**Descripción:** Distancia del trailing stop (%)
**Tipo:** Número decimal
**Valor por defecto:** `1.0`
**Ejemplo:** `CRYPTO_TRAILING_STOP_DISTANCE=1.0`

**Ajuste:**
```env
CRYPTO_TRAILING_STOP_DISTANCE=0.5  # Muy ajustado (protege más)
CRYPTO_TRAILING_STOP_DISTANCE=1.0  # Equilibrado
CRYPTO_TRAILING_STOP_DISTANCE=1.5  # Más amplio (da más espacio)
```

---

### `CRYPTO_CAPITAL_PCT`
**Descripción:** % del capital total asignado a crypto
**Tipo:** Número decimal
**Rango:** 10.0 - 50.0
**Valor por defecto:** `40.0`
**Ejemplo:** `CRYPTO_CAPITAL_PCT=40.0`

**¿Cómo funciona?**
Con $10,000 total:
```env
CRYPTO_CAPITAL_PCT=30.0  # $3,000 para crypto, $7,000 para forex
CRYPTO_CAPITAL_PCT=40.0  # $4,000 para crypto, $6,000 para forex
CRYPTO_CAPITAL_PCT=50.0  # $5,000 para crypto, $5,000 para forex
```

---

## 📝 Logging

### `LOG_LEVEL`
**Descripción:** Nivel de detalle de los logs
**Tipo:** Texto
**Valores:** `DEBUG`, `INFO`, `WARNING`, `ERROR`
**Ejemplo:** `LOG_LEVEL=INFO`

**¿Cuál usar?**
- `DEBUG` - Todo (desarrollo, troubleshooting)
- `INFO` - Normal (recomendado para producción)
- `WARNING` - Solo advertencias y errores
- `ERROR` - Solo errores críticos

---

## 🎯 Configuraciones Recomendadas

### **Principiante Conservador**
```env
# Forex
FOREX_PAIRS=EURUSD,GBPUSD
FOREX_TIMEFRAME=H1

# Crypto
CRYPTO_PAIRS=BTCUSD,ETHUSD
CRYPTO_TIMEFRAME=30
CRYPTO_ENABLED=false  # Empezar solo con Forex

# Risk
MAX_DAILY_LOSS_PCT=5.0
MAX_FOREX_POSITIONS=2
MAX_CRYPTO_POSITIONS=2
MAX_TOTAL_POSITIONS=3

CRYPTO_STOP_LOSS_PCT=2.5
CRYPTO_TAKE_PROFIT_PCT=3.5
CRYPTO_CAPITAL_PCT=30.0
```

### **Intermedio Equilibrado** (RECOMENDADO)
```env
# Forex
FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD
FOREX_TIMEFRAME=M15

# Crypto
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD
CRYPTO_TIMEFRAME=15
CRYPTO_ENABLED=true

# Risk
MAX_DAILY_LOSS_PCT=10.0
MAX_FOREX_POSITIONS=3
MAX_CRYPTO_POSITIONS=3
MAX_TOTAL_POSITIONS=5

CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=3.5
CRYPTO_CAPITAL_PCT=40.0
```

### **Avanzado Agresivo**
```env
# Forex
FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,EURJPY
FOREX_TIMEFRAME=M15

# Crypto
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD
CRYPTO_TIMEFRAME=5
CRYPTO_ENABLED=true

# Risk
MAX_DAILY_LOSS_PCT=15.0
MAX_FOREX_POSITIONS=5
MAX_CRYPTO_POSITIONS=4
MAX_TOTAL_POSITIONS=7

CRYPTO_STOP_LOSS_PCT=1.5
CRYPTO_TAKE_PROFIT_PCT=4.0
CRYPTO_CAPITAL_PCT=50.0
```

---

## ⚙️ Cómo Modificar el .env

1. **Detén el bridge** (Ctrl+C en la terminal)
2. **Edita el archivo:**
   ```powershell
   notepad .env
   ```
3. **Modifica los valores** que necesites
4. **Guarda** (Ctrl+S)
5. **Reinicia el bridge:**
   ```powershell
   python mt5_bridge.py
   ```

---

## 🔍 Troubleshooting

**Error: "invalid literal for int()"**
→ Verifica que los números no tengan espacios o caracteres raros

**Error: "connection refused"**
→ Verifica POSTGRES_HOST y REDIS_HOST

**Bot no abre operaciones**
→ Revisa MAX_DAILY_LOSS_PCT y límites de posiciones

**Demasiadas operaciones**
→ Aumenta CRYPTO_TIMEFRAME o reduce número de pares

---

## 📚 Recursos Adicionales

- **CRYPTO_INTEGRATION.md** - Guía de integración paso a paso
- **test_crypto_live.py** - Script de prueba de señales
- **mt5_bridge.py** - Código principal del bot

---

**¿Dudas?** Revisa los logs en `mt5_bridge.log` para más detalles.
