# Windows MT5 Bridge V3

**Production-ready MetaTrader 5 bridge with modular architecture**

Connects MetaTrader 5 (Windows) to Linux-based trading infrastructure (PostgreSQL + Redis).

---

## Quick Start

```powershell
# 1. Configure (first time only)
copy .env.example .env
# Edit .env with your credentials

# 2. Run
run_bridge_v3.bat

# Or directly with Python
python -m bridge_v3.main
```

---

## Features

- ✅ **Modular MVC Architecture** - Clean, maintainable code
- ✅ **Parallel Execution** - 3-4x faster with ThreadPoolExecutor
- ✅ **Connection Pooling** - Efficient PostgreSQL connections
- ✅ **Automatic Trading** - Executes crypto strategy signals
- ✅ **Multi-Asset Support** - Forex + Cryptocurrency
- ✅ **Production Ready** - Error handling, logging, graceful shutdown
- ✅ **UTF-8 Compatible** - Works perfectly on Windows console

---

## Architecture

```
bridge_v3/
├── config/       # Configuration management
├── models/       # Data models (Trade, Account, Price)
├── services/     # External services (MT5, Database, Redis)
├── controllers/  # Business logic (Price, Trade, Risk, Strategy)
├── workers/      # Task management (Parallel execution)
└── main.py       # Main orchestrator
```

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for detailed diagrams.

---

## Configuration

Edit `.env` file:

```env
# MT5 Credentials
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=your_server

# Linux Server
POSTGRES_HOST=10.30.90.102
REDIS_HOST=10.30.90.102

# Trading Pairs
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD
FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD

# Risk Management
MAX_DAILY_LOSS_PCT=10.0
CRYPTO_STOP_LOSS_PCT=2.0
CRYPTO_TAKE_PROFIT_PCT=3.5
```

See [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md) for all parameters.

---

## Trading Strategy

Uses **relaxed crypto strategy** with technical indicators:

- **RSI(14)** - Oversold < 40, Overbought > 60
- **EMA(9/21)** - Fast/Slow crossover
- **MACD(12/26/9)** - Histogram direction
- **Bollinger Bands(20,2)** - Price extremes
- **VWAP** - Volume-weighted average

**Signal Rules:**
- **LONG:** 3 of 4 conditions met
- **SHORT:** 3 of 4 conditions met

**Risk Management:**
- Stop Loss: 2%
- Take Profit: 3.5%
- Risk/Reward: 1:1.75
- Daily Loss Limit: 10%

---

## Documentation

| Document | Description |
|----------|-------------|
| [BRIDGE_V3_README.md](BRIDGE_V3_README.md) | Complete V3 guide |
| [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) | System architecture |
| [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md) | Enable/disable trading |
| [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md) | Configuration reference |

---

## Monitoring

```powershell
# View live logs
Get-Content mt5_bridge_v3.log -Wait -Tail 50

# Check for errors
Get-Content mt5_bridge_v3.log | Select-String "ERROR"
```

---

## Files

- **`bridge_v3/`** - Main bridge code (modular)
- **`run_bridge_v3.bat`** - Launcher script
- **`crypto_strategy_relaxed.py`** - Trading strategy
- **`.env`** - Configuration (create from .env.example)
- **`mt5_bridge_v3.log`** - Activity log (generated)

---

## Support

See documentation files for detailed guides:
- Installation issues → BRIDGE_V3_README.md
- Trading execution → EXECUTION_GUIDE.md
- Configuration → ENV_CONFIGURATION.md
- Architecture → ARCHITECTURE_DIAGRAM.md

---

**Version:** 3.0.0
**Status:** Production Ready
**Last Updated:** 2025-10-23
