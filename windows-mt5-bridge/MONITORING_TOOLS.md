# Herramientas de Monitoreo - Bridge V3

## Descripción General

El sistema ahora incluye dos herramientas de monitoreo en tiempo real:

1. **Monitor de Trades** (`monitor_trades.py`): Analiza el log y muestra alertas de señales y operaciones
2. **Dashboard en Consola** (`dashboard_console.py`): Muestra estadísticas en vivo desde la base de datos

## 1. Monitor de Trades (Análisis de Log)

### Qué hace
- Lee el archivo `mt5_bridge_v3.log` en tiempo real
- Detecta señales de trading (LONG/SHORT)
- Alerta cuando se abren operaciones exitosamente
- Alerta cuando fallan las operaciones
- Alerta cuando se cierran posiciones
- Muestra advertencias de riesgo

### Cómo usar

#### Método 1: Script Batch (Recomendado)
```bash
monitor_live.bat
```

#### Método 2: Comando directo
```bash
python monitor_trades.py
```

### Ejemplo de salida

Cuando se detecta una **señal**:
```
════════════════════════════════════════════════════════════════════════════════
🔔 [09:15:30] SEÑAL DETECTADA - BTCUSD
════════════════════════════════════════════════════════════════════════════════
  🎯 Símbolo: BTCUSD
  📊 Tipo: SHORT
  ✓ Condiciones: 3/4
  ⏰ Tiempo: 2024-01-20 09:15:30
════════════════════════════════════════════════════════════════════════════════
```

Cuando se **abre una operación**:
```
════════════════════════════════════════════════════════════════════════════════
✅ [09:15:31] OPERACIÓN ABIERTA - BTCUSD
════════════════════════════════════════════════════════════════════════════════
  🎫 Ticket: 987654321
  🎯 Símbolo: BTCUSD
  📊 Tipo: SHORT
  💰 Entrada: $43,250.50
  🛑 Stop Loss: $44,115.01 (-864.51)
  🎯 Take Profit: $41,737.00 (+1,513.50)
  📐 R:R Ratio: 1:1.75
  📦 Lotes: 0.01
  💵 Riesgo: $20.00
════════════════════════════════════════════════════════════════════════════════
```

Cuando **falla una operación**:
```
════════════════════════════════════════════════════════════════════════════════
❌ [09:15:31] OPERACIÓN FALLIDA - BTCUSD
════════════════════════════════════════════════════════════════════════════════
  🎯 Símbolo: BTCUSD
  ❌ Razón: AutoTrading disabled by client
  🔢 Retcode: 10027
  💡 Solución: Habilita AutoTrading en MT5 (botón debe estar VERDE)
════════════════════════════════════════════════════════════════════════════════
```

Cuando se **cierra una operación**:
```
════════════════════════════════════════════════════════════════════════════════
🔒 [10:45:12] OPERACIÓN CERRADA - BTCUSD
════════════════════════════════════════════════════════════════════════════════
  🎫 Ticket: 987654321
  ⏱️ Duración: 89 minutos
════════════════════════════════════════════════════════════════════════════════
```

### Detener el monitor
Presiona `Ctrl+C` para detener. El monitor mostrará un resumen de trades activos al salir.

---

## 2. Dashboard en Consola (Estadísticas de Base de Datos)

### Qué hace
- Conecta a PostgreSQL y Redis
- Muestra métricas de cuenta en tiempo real (balance, equity, profit)
- Lista trades activos con profit actual
- Estadísticas del día (win rate, profit total, avg profit)
- Rendimiento por símbolo (últimos 7 días)
- Se actualiza automáticamente cada 5 segundos

### Requisitos
- PostgreSQL debe estar corriendo (TimescaleDB)
- Configuración `.env` correcta con credenciales de base de datos
- Bridge v3 debe estar sincronizando datos

### Cómo usar

#### Método 1: Script Batch (Recomendado)
```bash
dashboard_live.bat
```

#### Método 2: Comando directo
```bash
python dashboard_console.py
```

### Ejemplo de salida

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 TRADING BOT DASHBOARD - BRIDGE V3                     ║
║                          2024-01-20 09:30:15                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ 💰 CUENTA ────────────────────────────────────────────────────────────────┐
│ Balance:      $10,000.00         │ Margen:       $150.00                  │
│ Equity:       $10,125.50         │ Margen Libre: $9,975.50                │
│ Profit:       $125.50            │ Margen Nivel: 6750.33%                 │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 📊 TRADES ACTIVOS ────────────────────────────────────────────────────────┐
│ Ticket    │ Símbolo   │ Tipo  │ Lotes │ Entrada    │ Actual     │ Profit     │
├───────────┼───────────┼───────┼───────┼────────────┼────────────┼────────────┤
│ 987654321 │ BTCUSD    │ SHORT │ 0.01  │ 43250.50   │ 42800.25   │ $45.00     │
│ 987654322 │ ETHUSD    │ LONG  │ 0.02  │ 2350.00    │ 2390.50    │ $80.50     │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 📈 ESTADÍSTICAS HOY ──────────────────────────────────────────────────────┐
│ Trades:       12         │ Ganadas:      8          │ Perdidas:     4          │
│ Win Rate:     66.67%     │ Profit Total: $320.50                               │
│ Avg Profit:   $26.71     │ Max Profit:   $125.00    │ Min Profit:   -$45.00    │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 🎯 RENDIMIENTO POR SÍMBOLO (7 días) ─────────────────────────────────────┐
│ Símbolo   │ Trades │ Ganadas │ Win Rate │ Profit Total │ Avg Profit   │
├───────────┼────────┼─────────┼──────────┼──────────────┼──────────────┤
│ BTCUSD    │ 45     │ 32      │ 71.11%   │ $1,250.00    │ $27.78       │
│ ETHUSD    │ 38     │ 24      │ 63.16%   │ $820.50      │ $21.59       │
│ LTCUSD    │ 22     │ 14      │ 63.64%   │ $450.00      │ $20.45       │
│ XRPUSD    │ 18     │ 10      │ 55.56%   │ $180.00      │ $10.00       │
└────────────────────────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────────────────────────
⟳ Actualizando cada 5 segundos... Presiona Ctrl+C para salir
────────────────────────────────────────────────────────────────────────────────
```

### Colores
- **Verde**: Profit positivo
- **Rojo**: Profit negativo
- **Blanco**: Valores neutrales

### Detener el dashboard
Presiona `Ctrl+C` para detener.

---

## Uso Recomendado

### Escenario 1: Monitorear señales y operaciones
**Usar**: `monitor_live.bat`

Ideal cuando:
- Quieres ver las señales en tiempo real
- Necesitas saber cuándo se abren/cierran operaciones
- Quieres diagnosticar errores de ejecución
- Estás probando la estrategia

### Escenario 2: Monitorear rendimiento
**Usar**: `dashboard_live.bat`

Ideal cuando:
- Quieres ver el balance y equity actual
- Necesitas saber cuánto profit llevas hoy
- Quieres ver estadísticas de win rate
- Quieres analizar qué símbolos son más rentables

### Escenario 3: Monitoreo completo
**Usar**: Ambos (dos ventanas de terminal)

Abre dos ventanas:
- **Ventana 1**: `monitor_live.bat` (alertas de operaciones)
- **Ventana 2**: `dashboard_live.bat` (estadísticas)
- **Ventana 3** (opcional): `run_bridge_v3.bat` (el bridge mismo)

---

## Solución de Problemas

### Monitor de Trades

**Error: "Esperando que se cree el archivo mt5_bridge_v3.log..."**
- El bridge no está corriendo
- Inicia `run_bridge_v3.bat` primero

**No muestra alertas**
- Verifica que el archivo de log se esté actualizando
- Revisa que el bridge esté detectando señales

### Dashboard en Consola

**Error: "No se pudo conectar a la base de datos"**
- Verifica que PostgreSQL esté corriendo
- Revisa las credenciales en `.env`:
  ```
  POSTGRES_HOST=10.30.90.102
  POSTGRES_PORT=5432
  POSTGRES_DB=trading_db
  POSTGRES_USER=trading_user
  POSTGRES_PASSWORD=tu_password
  ```

**Error: "Falta instalar dependencias"**
```bash
pip install psycopg2-binary redis python-dotenv
```

**No muestra datos**
- Verifica que el bridge esté corriendo y sincronizando
- Revisa el log del bridge: `mt5_bridge_v3.log`
- Ejecuta una consulta manual a PostgreSQL para verificar datos

---

## Archivos Creados

```
windows-mt5-bridge/
├── monitor_trades.py          # Monitor de log (señales y operaciones)
├── monitor_live.bat           # Launcher para monitor de trades
├── dashboard_console.py       # Dashboard con estadísticas
├── dashboard_live.bat         # Launcher para dashboard
└── MONITORING_TOOLS.md        # Esta documentación
```

---

## Próximas Mejoras

Posibles mejoras futuras:
- [ ] Dashboard web (HTML/CSS/JavaScript)
- [ ] Notificaciones por Telegram/Email
- [ ] Gráficos de equity curve en consola
- [ ] Exportar estadísticas a CSV/Excel
- [ ] Alarmas sonoras para señales importantes
- [ ] Integración con TradingView webhooks

---

## Notas de Seguridad

⚠️ **IMPORTANTE**:
- Estos monitores son de **solo lectura** (no modifican operaciones)
- El monitor de trades solo lee el log, no interactúa con MT5
- El dashboard solo consulta la base de datos, no ejecuta trades
- Ambos son seguros para usar en producción

---

## Soporte

Si encuentras problemas:
1. Revisa que el bridge v3 esté corriendo
2. Verifica la conexión a PostgreSQL
3. Revisa el archivo `.env`
4. Consulta los logs: `mt5_bridge_v3.log`
