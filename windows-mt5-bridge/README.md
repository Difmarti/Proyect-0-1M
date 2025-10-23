# Windows MT5 Bridge - Trading Bot

Bridges MetaTrader 5 (running natively on Windows) with the Linux-based trading infrastructure.

## Quick Start

### Recommended: Use V3 (Modular Architecture)

```powershell
# 1. Configure (first time only)
copy .env.example .env
# Edit .env with your credentials

# 2. Run
python -m bridge_v3.main

# Or use the launcher
run_bridge_v3.bat
```

## Available Versions

### 🚀 V3 - Modular Architecture (RECOMMENDED)

**Modern, scalable, production-ready**

- ✅ **3-4x faster** than V2 (parallel execution)
- ✅ **Modular MVC architecture** (easy to extend)
- ✅ **Connection pooling** (no database exhaustion)
- ✅ **Priority task queue** (critical tasks first)
- ✅ **Built-in monitoring** (worker statistics)
- ✅ **UTF-8 logging** (Windows console friendly)
- ✅ **Graceful shutdown** (no data loss)

**Documentation:**
- [Complete Guide](BRIDGE_V3_README.md)
- [Architecture Diagrams](ARCHITECTURE_DIAGRAM.md)
- [Migration Guide](MIGRATION_GUIDE.md)

**Run:**
```powershell
python -m bridge_v3.main
```

---

### V2 - Integrated Forex + Crypto (Legacy)

**Monolithic, works but slower**

- Forex + Crypto trading
- 10% daily loss limit
- Safety mode (signals logged, not executed)

**Documentation:**
- [V2 Guide](BRIDGE_V2_README.md)
- [Crypto Integration](CRYPTO_INTEGRATION.md)

**Run:**
```powershell
python mt5_bridge_v2.py
```

---

### V1 - Basic Forex (Legacy)

**Simplest version, Forex only**

- Basic price sync
- Account metrics
- Forex trading only

**Run:**
```powershell
python mt5_bridge.py
```

---

## Feature Comparison

| Feature | V1 | V2 | V3 |
|---------|----|----|-----|
| **Forex Trading** | ✅ | ✅ | ✅ |
| **Crypto Trading** | ❌ | ✅ | ✅ |
| **Parallel Execution** | ❌ | ❌ | ✅ |
| **Connection Pooling** | ❌ | ❌ | ✅ |
| **Modular Architecture** | ❌ | ❌ | ✅ |
| **Priority Tasks** | ❌ | ❌ | ✅ |
| **Performance** | Slow | Medium | **Fast** |
| **Extensibility** | Hard | Medium | **Easy** |
| **Production Ready** | Basic | Good | **Excellent** |

## Documentation Index

| Document | Description |
|----------|-------------|
| [BRIDGE_V3_README.md](BRIDGE_V3_README.md) | Complete V3 documentation |
| [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) | Visual architecture diagrams |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Migrate from V2 to V3 |
| [BRIDGE_V2_README.md](BRIDGE_V2_README.md) | V2 documentation (legacy) |
| [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md) | Environment variable reference |
| [CRYPTO_INTEGRATION.md](CRYPTO_INTEGRATION.md) | Crypto trading guide (V2) |

---

**Ready to start?**

```powershell
python -m bridge_v3.main
```

🚀 **Happy Trading!**
