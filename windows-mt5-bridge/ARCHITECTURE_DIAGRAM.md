# MT5 Bridge V3 - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MT5 Bridge V3 - Main Orchestrator           │
│                         (main.py)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Services   │      │ Controllers  │     │   Workers    │
│              │      │              │     │              │
│ • MT5        │      │ • Price      │     │ • TaskWorker │
│ • Database   │◄────►│ • Trade      │◄───►│ • Scheduler  │
│ • Redis      │      │ • Risk       │     │              │
│ • Logger     │      │ • Strategy   │     │              │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Models                                 │
│                                                                 │
│  • Trade        • Position       • TradeSignal                  │
│  • AccountMetrics • RiskMetrics  • PriceData • OHLCV           │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Architecture (MVC Pattern)

```
┌───────────────────────────────────────────────────────────────┐
│                      Presentation Layer                        │
│                   (Logs, Console Output)                       │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    Controller Layer                            │
│                                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Price     │  │    Trade    │  │    Risk     │           │
│  │ Controller  │  │ Controller  │  │ Controller  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                │
│  ┌─────────────┐                                              │
│  │  Strategy   │                                              │
│  │ Controller  │                                              │
│  └─────────────┘                                              │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                      Model Layer                               │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Trade   │  │ Account  │  │  Price   │  │  Signal  │     │
│  │  Model   │  │  Model   │  │  Model   │  │  Model   │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                     Service Layer                              │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   MT5    │  │ Database │  │  Redis   │  │  Logger  │     │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                  External Dependencies                         │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │   MT5    │  │PostgreSQL│  │  Redis   │                    │
│  │ Terminal │  │(TimescaleDB)│ Server   │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
└───────────────────────────────────────────────────────────────┘
```

## Parallel Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Task Scheduler                             │
│                   (Triggers jobs periodically)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Creates Tasks
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Priority Task Queue                         │
│                                                                 │
│  Priority 0 (CRITICAL):  [Risk Check] [Emergency Stop]         │
│  Priority 1 (HIGH):      [Trade Sync] [Metrics Sync]           │
│  Priority 2 (NORMAL):    [Price Fetch] [Strategy Analysis]     │
│  Priority 3 (LOW):       [History Sync] [Analytics]            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Distributed to Workers
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ThreadPoolExecutor                            │
│                   (MAX_WORKERS threads)                         │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │       │
│  │          │  │          │  │          │  │          │       │
│  │ Forex    │  │ Crypto   │  │ Metrics  │  │  Risk    │       │
│  │ Prices   │  │ Prices   │  │ Sync     │  │ Check    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Results
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Controllers                              │
│                   (Process results)                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────┐
│     MT5     │
│  Terminal   │
└──────┬──────┘
       │
       │ Price Data, Positions, Account Info
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MT5 Service                               │
│                  (Connection Management)                        │
└─────────────────────────────────────────────────────────────────┘
       │
       │ Fetched Data
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Price Controller                             │
│               (Parallel Fetch & Process)                        │
└─────────────────────────────────────────────────────────────────┘
       │
       ├────────────────┬────────────────┐
       │                │                │
       ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Database   │  │    Redis     │  │   Logger     │
│   Service    │  │   Service    │  │   Service    │
│              │  │              │  │              │
│ • Price Data │  │ • Cache      │  │ • Logs       │
│ • Trades     │  │ • Metrics    │  │ • Stats      │
│ • Metrics    │  │ • Counters   │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
       │                │
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │    Redis     │
│ (TimescaleDB)│  │    Server    │
└──────────────┘  └──────────────┘
```

## Task Execution Timeline

```
Time    Scheduler               Workers
────────────────────────────────────────────────────────────────
00:00   [Fetch Prices]  ─────►  Worker1: Forex Prices
                                Worker2: Crypto Prices
                                Worker3: Idle
                                Worker4: Idle

00:30   [Sync Trades]   ─────►  Worker1: Forex Prices (running)
                                Worker2: Crypto Prices (running)
                                Worker3: Trade Sync ◄─── Assigned
                                Worker4: Idle

00:60   [Sync Metrics]  ─────►  Worker1: Complete ✓
        [Fetch Prices]          Worker2: Complete ✓
                                Worker3: Trade Sync (running)
                                Worker4: Metrics Sync ◄─── Assigned

                        ─────►  Worker1: Forex Prices ◄─── Reassigned
                                Worker2: Crypto Prices ◄─── Reassigned

01:00   [Analyze Crypto]─────►  Worker3: Complete ✓
                                Worker4: Complete ✓
                                Worker3: Crypto Analysis ◄─── Assigned
                                Worker4: Idle

01:00   [Update Risk]   ─────►  Worker4: Risk Update ◄─── Assigned (CRITICAL)
```

## Configuration Flow

```
┌─────────────┐
│  .env File  │
└──────┬──────┘
       │
       │ Loaded by python-dotenv
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Settings Class                               │
│                 (config/settings.py)                            │
│                                                                 │
│  • MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER                        │
│  • POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB                    │
│  • REDIS_HOST, REDIS_PORT                                       │
│  • FOREX_PAIRS, CRYPTO_PAIRS                                    │
│  • MAX_WORKERS, WORKER_TIMEOUT                                  │
│  • Risk limits, intervals, etc.                                 │
└─────────────────────────────────────────────────────────────────┘
       │
       │ Imported by all modules
       │
       ├───────────┬───────────┬───────────┬───────────┐
       │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼
   Services   Controllers   Workers     Models      Main
```

## Error Handling & Logging

```
┌─────────────────────────────────────────────────────────────────┐
│                  Exception Occurs                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Try/Except Block                              │
│              (In Service/Controller/Worker)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Logger Service                               │
│                 (Centralized Logging)                           │
│                                                                 │
│  • Format: timestamp - module - level - message                 │
│  • UTF-8 encoding (Windows compatible)                          │
│  • Rotating file handler (10MB max, 5 backups)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────┐
                              │                 │
                              ▼                 ▼
                      ┌──────────────┐  ┌──────────────┐
                      │  Log File    │  │   Console    │
                      │ (mt5_bridge  │  │   Output     │
                      │   _v3.log)   │  │              │
                      └──────────────┘  └──────────────┘
```

## Comparison: V2 vs V3

### V2 (Monolithic)
```
main.py (700+ lines)
  ├─ initialize_mt5()
  ├─ connect_database()
  ├─ fetch_prices() ──► Sequential execution
  ├─ sync_trades()
  ├─ analyze_signals()
  └─ run() ──► Single thread, one task at a time
```

### V3 (Modular)
```
main.py (orchestrator)
  │
  ├─ Services Layer
  │   ├─ MT5Service
  │   ├─ DatabaseService (with connection pool)
  │   └─ RedisService
  │
  ├─ Controllers Layer
  │   ├─ PriceController
  │   ├─ TradeController
  │   ├─ RiskController
  │   └─ StrategyController
  │
  └─ Workers Layer
      ├─ TaskWorker ──► Parallel execution
      │   ├─ Worker 1 (Forex prices)
      │   ├─ Worker 2 (Crypto prices)
      │   ├─ Worker 3 (Trade sync)
      │   └─ Worker 4 (Risk check)
      │
      └─ TaskScheduler ──► Cron-like scheduling
```

## Performance Benefits

```
Sequential (V2):
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Task 1 │→│ Task 2 │→│ Task 3 │→│ Task 4 │
└────────┘ └────────┘ └────────┘ └────────┘
  10s       10s       10s       10s

Total Time: 40 seconds

Parallel (V3):
┌────────┐
│ Task 1 │
├────────┤
│ Task 2 │
├────────┤  All running simultaneously
│ Task 3 │
├────────┤
│ Task 4 │
└────────┘
  10s

Total Time: 10 seconds (4x faster!)
```

## Scalability

### Adding New Strategy (V3)

1. Create new controller method:
```python
# controllers/strategy_controller.py
def analyze_custom_signals(self):
    # Your logic here
    pass
```

2. Add to scheduler:
```python
# main.py
self.scheduler.add_job(
    self.strategy_ctrl.analyze_custom_signals,
    interval=60,
    unit='seconds'
)
```

Done! No need to modify 700 lines of monolithic code.

### Adding New Pairs

V2: May slow down due to sequential processing
V3: No performance impact (parallel workers handle load)

```
V2 (4 pairs):  4 × 5s = 20s per cycle
V2 (10 pairs): 10 × 5s = 50s per cycle ⚠️ Slow!

V3 (4 pairs):  max(5s) = 5s per cycle
V3 (10 pairs): max(5s) = 5s per cycle ✓ Same speed!
```
