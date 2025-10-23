# MT5 Bridge V2 - Integrated Forex + Crypto Trading System

## 🎯 Overview

**mt5_bridge_v2.py** is the enhanced version of the MT5 Windows Bridge that integrates cryptocurrency trading alongside the existing Forex strategy. This new version features:

- ✅ **Dual-Asset Support**: Trade Forex and Crypto simultaneously
- ✅ **Integrated Risk Management**: 10% daily loss limit shared between both asset types
- ✅ **Multi-Timeframe Analysis**: Independent timeframes for Forex (M15) and Crypto (5m/15m/30m/1h)
- ✅ **Advanced Crypto Strategy**: RSI + EMA + MACD + Bollinger Bands + VWAP indicators
- ✅ **24/7 Crypto Operation**: Automated signal detection with optimal trading hours
- ✅ **Safety Mode**: Signals logged but not executed until you enable it
- ✅ **Position Tracking**: Separate tracking for Forex and Crypto positions

## 📋 What Changed from V1

| Feature | V1 (mt5_bridge.py) | V2 (mt5_bridge_v2.py) |
|---------|-------------------|----------------------|
| Asset Types | Forex only | Forex + Crypto |
| Risk Management | Basic | Integrated (shared 10% limit) |
| Strategy Modules | None | crypto_strategy.py + risk_manager.py |
| Position Tracking | Basic | Asset-type aware |
| Trade Execution | Not implemented | Crypto: Logging mode (expandable) |
| Timeframes | Single (M15) | Dual (Forex: M15, Crypto: configurable) |

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have:
- ✅ Python 3.11+ installed
- ✅ MT5 installed and closed (script will open it)
- ✅ Dependencies installed: `pip install -r requirements.txt`
- ✅ `.env` file configured (see ENV_CONFIGURATION.md)
- ✅ Network access to Linux server (10.30.90.102)

### 2. Stop Current Bridge

If you're running the old bridge (mt5_bridge.py), stop it first:

```powershell
# Press Ctrl+C in the terminal running mt5_bridge.py
```

### 3. Verify Configuration

Check your `.env` file has these crypto settings:

```env
# Crypto Configuration
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD
CRYPTO_TIMEFRAME=15  # 5, 15, 30, or 60 minutes
CRYPTO_ENABLED=true

# Risk Management
MAX_DAILY_LOSS_PCT=10.0
MAX_FOREX_POSITIONS=3
MAX_CRYPTO_POSITIONS=3
MAX_TOTAL_POSITIONS=5

CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=3.5
```

### 4. Run Bridge V2

```powershell
cd c:\Repositorio\Proyect-0-1M\windows-mt5-bridge
python mt5_bridge_v2.py
```

### 5. Monitor Logs

The bridge will output detailed logs to:
- **Console**: Real-time activity
- **mt5_bridge_v2.log**: Persistent log file

## 📊 What to Expect

### Startup Output

```
======================================================================
MT5 Windows Bridge V2 - Forex + Crypto Integration
======================================================================
Forex Pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD
Forex Timeframe: M15
Crypto Pairs: BTCUSD, ETHUSD, LTCUSD, XRPUSD
Crypto Timeframe: 15 minutes
Crypto Strategy: ENABLED ✓
Max Daily Loss: 10.0% (shared between Forex and Crypto)
======================================================================
MT5 logged in successfully to Tickmill-Demo with account 25251142
Connected to PostgreSQL at 10.30.90.102:5432
Connected to Redis at 10.30.90.102:6379
Risk Manager initialized
======================================================================
MT5 Windows Bridge V2 Running!
Scheduled tasks:
  - Fetch prices: Every 1 minute (Forex + Crypto)
  - Sync metrics: Every 1 minute
  - Sync trades: Every 30 seconds
  - Analyze crypto signals: Every 1 minute
======================================================================

⚠️  CRYPTO TRADING IN SAFETY MODE ⚠️
Signals will be logged but NOT executed automatically.
======================================================================
```

### When a Crypto Signal is Detected

```
🪙 BTCUSD: Señal LONG detectada a $107635.84

BTCUSD - SEÑAL LONG detectada:
  RSI: 28.45 < 30
  EMA9: 107640.12 > EMA21: 107580.34
  MACD Histogram: 0.00234 > 0
  Precio: 107635.84 > VWAP: 107500.20
  Volumen: 1250.0 > Avg: 980.0

╔══════════════════════════════════════════════════════════╗
║  🪙 SEÑAL DE CRYPTO DETECTADA                            ║
╠══════════════════════════════════════════════════════════╣
║  Símbolo: BTCUSD                                         ║
║  Tipo: LONG                                              ║
║  Precio: $107635.84                                      ║
║  Stop Loss: $105482.92                                   ║
║  Take Profit: $111413.39                                 ║
║  Risk/Reward: 1:1.75                                     ║
╚══════════════════════════════════════════════════════════╝
```

### No Signal Output

```
Running job: Analyze crypto signals
📊 Analizando BTCUSD...
   ✓ Datos obtenidos: 200 barras
   Último precio: $107635.84
   Volumen actual: 850
   ℹ️  Sin señal en este momento

📊 Analizando ETHUSD...
   ✓ Datos obtenidos: 200 barras
   Último precio: $3807.25
   Volumen actual: 1120
   ⚠️  Fuera de horario óptimo (hora 5)
```

## 🔒 Safety Features

### 1. Logging Mode (Default)

By default, Bridge V2 runs in **Safety Mode**:
- ✅ Signals are detected and logged
- ✅ All calculations are performed
- ❌ **NO trades are executed automatically**

This allows you to:
- Monitor signal quality
- Verify strategy performance
- Review trading opportunities
- Gain confidence before enabling execution

### 2. Risk Limits

The integrated Risk Manager enforces:

| Limit Type | Value | Scope |
|-----------|-------|-------|
| Daily Loss | 10% | Shared (Forex + Crypto) |
| Max Forex Positions | 3 | Forex only |
| Max Crypto Positions | 3 | Crypto only |
| Max Total Positions | 5 | Combined |
| Stop Loss | 2% | Per crypto trade |
| Take Profit | 3.5% | Per crypto trade |

### 3. Progressive Alerts

The Risk Manager sends alerts at:
- **5% loss**: 🟡 PRECAUCIÓN - Warning
- **8% loss**: 🔴 ALERTA CRÍTICA - Critical alert
- **10% loss**: ⛔ LÍMITE ALCANZADO - Trading stopped

## 🎯 Enabling Real Crypto Trading

Once you're confident with the signals, you can enable real execution:

### Step 1: Review Logged Signals

Let the bridge run in logging mode for 24-48 hours. Review:
- Signal frequency
- Entry/exit prices
- Risk/reward ratios
- Timing accuracy

### Step 2: Enable Execution Code

In `mt5_bridge_v2.py`, find the `execute_crypto_trade()` method (around line 477) and uncomment the execution block:

```python
def execute_crypto_trade(self, symbol, signal_type, current_price):
    """Execute crypto trade"""

    # ... logging code ...

    # UNCOMMENT THE BLOCK BELOW TO ENABLE REAL TRADING:
    try:
        # Determine order type
        order_type = mt5.ORDER_TYPE_BUY if signal_type == 'LONG' else mt5.ORDER_TYPE_SELL

        # Calculate position size
        account_info = mt5.account_info()
        position_size = self.crypto_strategy.calculate_position_size(
            account_info.balance,
            2.0,  # 2% risk per trade
            2.0   # 2% stop loss
        )

        # ... rest of the code ...
```

### Step 3: Add Execution Flag (Optional - Recommended)

For extra safety, add an environment variable:

In `.env`:
```env
CRYPTO_TRADE_EXECUTION=false  # Set to true when ready
```

Then modify the code to check this flag before executing.

### Step 4: Test with Small Capital

- Start with minimum position sizes
- Monitor for 1-2 days
- Gradually increase position sizes

## 📈 Monitoring and Analytics

### Dashboard Integration

The bridge syncs data to the dashboard at http://localhost:8501 (on Linux server):
- Active positions (Forex + Crypto)
- Performance by asset type
- Risk metrics
- Daily P/L breakdown

### Redis Metrics

Real-time metrics are cached in Redis:

```bash
# On Linux server
docker exec -it trading_redis redis-cli

# View account metrics
HGETALL account:metrics

# View risk stats
GET risk:daily_stats

# View alerts
LRANGE alerts 0 10
```

### Database Queries

```sql
-- Check crypto positions
SELECT * FROM active_trades WHERE strategy = 'crypto';

-- Check crypto performance
SELECT
    symbol,
    COUNT(*) as trades,
    SUM(profit) as total_profit,
    AVG(profit) as avg_profit
FROM trade_history
WHERE strategy = 'crypto'
GROUP BY symbol;

-- Daily risk stats
SELECT
    DATE(time) as date,
    MIN(balance) as min_balance,
    MAX(balance) as max_balance,
    (MAX(balance) - MIN(balance)) / MAX(balance) * 100 as daily_drawdown
FROM account_metrics
GROUP BY DATE(time)
ORDER BY date DESC
LIMIT 7;
```

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'crypto_strategy'"

**Solution**: Ensure these files exist in the same directory:
- crypto_strategy.py
- risk_manager.py
- mt5_bridge_v2.py

```powershell
ls crypto_strategy.py
ls risk_manager.py
```

### Issue: "No crypto data received for BTCUSD"

**Cause**: Symbol not available in your Tickmill account

**Solution**: Verify crypto symbols in MT5:
1. Open MT5
2. Go to Market Watch (Ctrl+M)
3. Right-click → Symbols
4. Search for "BTC", "ETH", etc.
5. Update CRYPTO_PAIRS in .env with available symbols

### Issue: "Fuera de horario óptimo"

**Cause**: Crypto strategy avoids low-volume hours (3-6 UTC)

**Solution**: This is normal. The strategy will resume during optimal hours:
- 0-2 UTC (US close)
- 7-9 UTC (Europe open)
- 8-10 UTC (Asia)
- 13-16 UTC (Wall Street open)

**To disable this filter**: In `crypto_strategy.py`, modify:
```python
self.avoid_hours = []  # Empty list = trade 24/7
```

### Issue: "Límite de pérdida diaria alcanzado"

**Cause**: Daily loss limit (10%) reached

**Solution**: Trading will automatically resume tomorrow (00:00 UTC). This is a safety feature.

**Manual override** (use with caution):
```bash
# On Linux server
docker exec -it trading_redis redis-cli
DEL risk:daily_stats
```

### Issue: Bridge crashes or disconnects

**Cause**: Network interruption or MT5 connection loss

**Solution**: The bridge includes reconnection logic. Restart:
```powershell
python mt5_bridge_v2.py
```

**For automatic restart** (Windows Service): See section below.

## 🔄 Running as Windows Service

To keep the bridge running 24/7, even after reboots:

### Option 1: NSSM (Recommended)

1. Download NSSM: https://nssm.cc/download
2. Extract to C:\nssm
3. Open PowerShell as Administrator:

```powershell
cd C:\nssm\win64
.\nssm install MT5BridgeV2
```

4. Configure:
   - Path: `C:\Users\[YourUser]\AppData\Local\Programs\Python\Python311\python.exe`
   - Startup directory: `C:\Repositorio\Proyect-0-1M\windows-mt5-bridge`
   - Arguments: `mt5_bridge_v2.py`

5. Start service:
```powershell
.\nssm start MT5BridgeV2
```

### Option 2: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Name: "MT5 Bridge V2"
3. Trigger: At startup
4. Action: Start a program
   - Program: `C:\Users\[YourUser]\AppData\Local\Programs\Python\Python311\python.exe`
   - Arguments: `mt5_bridge_v2.py`
   - Start in: `C:\Repositorio\Proyect-0-1M\windows-mt5-bridge`
5. Settings:
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
   - ✅ If task fails, restart every 1 minute

## 📊 Performance Optimization

### Timeframe Selection

| Timeframe | Signals per Day | Risk Level | Recommended For |
|-----------|----------------|------------|-----------------|
| 5 minutes | 15-30 | High | Experienced traders |
| 15 minutes | 5-15 | Medium | Most users (default) |
| 30 minutes | 3-8 | Low-Medium | Conservative |
| 1 hour | 1-5 | Low | Long-term holders |

**Change in .env**:
```env
CRYPTO_TIMEFRAME=15  # 5, 15, 30, or 60
```

### Indicator Tuning

To adjust indicator parameters, modify `crypto_strategy.py`:

```python
class CryptoStrategy:
    def __init__(self):
        # More sensitive (more signals)
        self.rsi_oversold = 35  # Default: 30
        self.rsi_overbought = 65  # Default: 70

        # Less sensitive (fewer, higher quality signals)
        self.rsi_oversold = 25
        self.rsi_overbought = 75
```

### Volume Filter

Adjust volume multiplier for signal quality:

```python
# In crypto_strategy.py
self.volume_multiplier = 1.5  # Default: 1.2 (higher = stricter)
```

## 📝 Comparison: V1 vs V2

### When to Use V1 (mt5_bridge.py)

Use the original bridge if:
- ✅ You only trade Forex
- ✅ You don't need crypto functionality
- ✅ You want minimal complexity
- ✅ You're running stable and don't want to change

### When to Use V2 (mt5_bridge_v2.py)

Use the new bridge if:
- ✅ You want to trade cryptocurrencies
- ✅ You need integrated risk management
- ✅ You want 24/7 signal monitoring
- ✅ You want separate tracking for Forex and Crypto
- ✅ You plan to scale to multi-asset trading

## 🎓 Next Steps

1. **✅ Test in Logging Mode** (24-48 hours)
   - Let the bridge run
   - Monitor signal quality
   - Review logs daily

2. **✅ Analyze Signals**
   - How many signals per day?
   - Are entry prices accurate?
   - Do Risk/Reward ratios make sense?

3. **✅ Backtest (Optional)**
   - Export signals from logs
   - Calculate hypothetical performance
   - Adjust parameters if needed

4. **✅ Enable Small Execution**
   - Uncomment execution code
   - Start with minimum sizes
   - Monitor for 1 week

5. **✅ Scale Up**
   - Increase position sizes gradually
   - Add more crypto pairs if needed
   - Optimize timeframes

6. **✅ Automate**
   - Set up as Windows Service
   - Configure alerts (Telegram/Email)
   - Schedule daily reports

## 📞 Support

### Log Files

If you encounter issues:
- **mt5_bridge_v2.log**: Main log file
- **Line numbers**: All errors include file:line references

### Debug Mode

Enable verbose logging:

```python
# At top of mt5_bridge_v2.py
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ... rest of config
)
```

### Common Gotchas

1. **MT5 must be closed** before running the bridge
2. **Crypto symbols** must exist in your broker (check Market Watch)
3. **Network access** required to Linux server (10.30.90.102)
4. **Redis and PostgreSQL** must be running on Linux server
5. **.env file** must be in the same directory as the script

## 🎉 Success Checklist

- [ ] Bridge starts without errors
- [ ] Connects to MT5 successfully
- [ ] Connects to PostgreSQL and Redis
- [ ] Fetches Forex prices every minute
- [ ] Fetches Crypto prices every minute
- [ ] Syncs account metrics
- [ ] Analyzes crypto signals
- [ ] Logs signals when detected
- [ ] Risk Manager initialized
- [ ] Dashboard shows data (http://10.30.90.102:8501)

## 📚 Additional Documentation

- **ENV_CONFIGURATION.md**: Detailed explanation of all .env parameters
- **MT5_TEMPLATE_PROMPT.md**: Creating visual template in MT5
- **CRYPTO_INTEGRATION.md**: Technical integration guide
- **CLAUDE.md**: Project overview and architecture

---

**Made with ❤️ for automated trading**
