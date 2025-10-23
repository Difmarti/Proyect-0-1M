# MT5 Bridge V3 - Modular Architecture

## Overview

MT5 Bridge V3 is a complete rewrite of the trading bridge with a modern, modular architecture featuring:

- **MVC Pattern**: Clear separation between Models, Views (logs), and Controllers
- **Parallel Execution**: Multi-threaded task execution with priority queues
- **Service-Oriented**: Independent services for MT5, Database, and Redis
- **Scalable**: Easy to add new strategies, controllers, and workers
- **Production-Ready**: Connection pooling, error handling, and graceful shutdown

## Architecture

```
bridge_v3/
├── config/                    # Configuration Management
│   ├── __init__.py
│   ├── settings.py           # Centralized settings from .env
│   └── constants.py          # MT5 constants and enums
│
├── models/                    # Data Models
│   ├── __init__.py
│   ├── trade.py              # Trade, Position, TradeSignal models
│   ├── account.py            # AccountMetrics, RiskMetrics models
│   └── price.py              # PriceData, OHLCV models
│
├── services/                  # Service Layer
│   ├── __init__.py
│   ├── logger_service.py     # Centralized logging with UTF-8 support
│   ├── mt5_service.py        # MT5 connection and operations
│   ├── database_service.py   # PostgreSQL with connection pooling
│   └── redis_service.py      # Redis caching and pub/sub
│
├── controllers/               # Business Logic Layer
│   ├── __init__.py
│   ├── price_controller.py   # Price fetching and storage
│   ├── trade_controller.py   # Trade synchronization
│   ├── risk_controller.py    # Risk management
│   └── strategy_controller.py # Strategy analysis
│
├── workers/                   # Parallel Execution Layer
│   ├── __init__.py
│   ├── task_worker.py        # Task worker with priority queue
│   └── scheduler.py          # Cron-like task scheduler
│
├── utils/                     # Utility Functions
│   └── __init__.py
│
├── main.py                    # Main orchestrator
└── __init__.py               # Package initialization
```

## Key Features

### 1. Parallel Task Execution

The bridge uses `ThreadPoolExecutor` for parallel execution:

```python
# Example: Fetch all prices in parallel
results = price_controller.fetch_and_store_all_prices_parallel()
# Processes all Forex and Crypto pairs simultaneously
```

**Benefits**:
- Faster data fetching (all symbols processed in parallel)
- Better resource utilization
- Configurable worker pool size via `MAX_WORKERS`

### 2. Priority-Based Task Queue

Tasks can be assigned priorities:

```python
task = Task(
    name='critical_risk_check',
    function=risk_controller.check_limits,
    priority=TaskPriority.CRITICAL  # Executed first
)
```

**Priority Levels**:
- `CRITICAL` (0): Risk management, emergency stops
- `HIGH` (1): Trade synchronization, account metrics
- `NORMAL` (2): Price fetching, regular updates
- `LOW` (3): History sync, analytics

### 3. Connection Pooling

Database service uses connection pooling for better performance:

```python
db_service = DatabaseService(pool_min=1, pool_max=10)
# Connections reused across requests
# No connection overhead for each query
```

### 4. Advanced Risk Management

Integrated risk controller with:
- Daily loss limit tracking
- Position count limits (by asset type)
- Real-time risk metrics caching
- Automatic trading halt on limit breach

### 5. Modular Strategy System

Easy to add new strategies:

```python
# controllers/strategy_controller.py
def analyze_custom_signals(self) -> list[TradeSignal]:
    # Your custom strategy logic here
    pass
```

## Installation

### 1. Requirements

```bash
pip install -r requirements.txt
```

Add to `requirements.txt`:
```
MetaTrader5>=5.0.45
psycopg2-binary>=2.9.9
redis>=5.0.0
pandas>=2.1.0
python-dotenv>=1.0.0
schedule>=1.2.0
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```ini
# MT5 Configuration
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=your_broker-server

# Database (Linux server)
POSTGRES_HOST=192.168.1.100
POSTGRES_PORT=5432
POSTGRES_DB=trading_db
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=secure_password

# Redis (Linux server)
REDIS_HOST=192.168.1.100
REDIS_PORT=6379

# Forex Configuration
FOREX_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD
FOREX_TIMEFRAME=M15

# Crypto Configuration
CRYPTO_ENABLED=true
CRYPTO_PAIRS=BTCUSD,ETHUSD,LTCUSD,XRPUSD
CRYPTO_TIMEFRAME=15

# Risk Management
MAX_DAILY_LOSS_PCT=10.0
RISK_PER_TRADE=2.0
MAX_SIMULTANEOUS_TRADES=5

# Performance Tuning
MAX_WORKERS=4              # Number of parallel workers
WORKER_TIMEOUT=300         # Task timeout in seconds
PRICE_FETCH_INTERVAL=60    # Seconds between price fetches
METRICS_SYNC_INTERVAL=60   # Seconds between metric syncs
TRADES_SYNC_INTERVAL=30    # Seconds between trade syncs
```

## Usage

### Running the Bridge

```powershell
# From windows-mt5-bridge directory
python -m bridge_v3.main
```

or

```powershell
# Direct execution
python bridge_v3/main.py
```

### Output Example

```
======================================================================
              MT5 Bridge V3 - Initializing
======================================================================
Configuration validated
Connected to PostgreSQL at 192.168.1.100:5432 (pool: 1-10)
Connected to Redis at 192.168.1.100:6379
MT5 logged in to Broker-Server with account 12345678
Risk manager initialized with balance: 10000.0
======================================================================
              Initialization Complete
======================================================================
Performing Initial Sync
Initial sync completed
Scheduled tasks configured:
  - fetch_prices: Every 60 seconds
  - sync_metrics: Every 60 seconds
  - sync_trades: Every 30 seconds
  - analyze_crypto: Every 60 seconds
  - update_risk: Every 60 seconds
======================================================================
                MT5 Bridge V3 Running!
======================================================================
Parallel Workers: 4
Forex Pairs: 4
Crypto Pairs: 4
Mode: SAFETY MODE (signals logged, not executed)
======================================================================
```

## Advanced Usage

### 1. Custom Controllers

Create a new controller:

```python
# controllers/analytics_controller.py
from bridge_v3.services import DatabaseService, LoggerService

logger = LoggerService.get_logger(__name__)

class AnalyticsController:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def generate_daily_report(self):
        # Your analytics logic
        pass
```

Register in `main.py`:

```python
self.analytics_ctrl = AnalyticsController(self.db)

# Add scheduled job
self.scheduler.add_job(
    self.analytics_ctrl.generate_daily_report,
    interval=1,
    unit='hours',
    name='daily_analytics'
)
```

### 2. Adding New Strategies

```python
# controllers/strategy_controller.py
def analyze_forex_signals(self) -> list[TradeSignal]:
    """Analyze Forex signals for all pairs"""
    signals = []

    for symbol in Settings.FOREX_PAIRS:
        # Fetch price data
        price_data = self.mt5.fetch_price_data(symbol, Settings.FOREX_TIMEFRAME)

        # Your strategy logic here
        # ...

        if signal_detected:
            signal = TradeSignal(
                symbol=symbol,
                signal_type=SignalType.LONG,
                strategy='forex_custom',
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                timestamp=datetime.now()
            )
            signals.append(signal)

    return signals
```

### 3. Parallel Task Submission

```python
# Submit multiple tasks in parallel
tasks = [
    Task('fetch_forex', price_ctrl.fetch_and_store_forex_prices, TaskPriority.NORMAL),
    Task('fetch_crypto', price_ctrl.fetch_and_store_crypto_prices, TaskPriority.NORMAL),
    Task('sync_metrics', trade_ctrl.sync_active_trades, TaskPriority.HIGH)
]

futures = [worker.submit_task(task) for task in tasks]

# Wait for all to complete
for future in futures:
    result = future.result(timeout=300)
```

## Performance Tuning

### 1. Database Connection Pool

Adjust pool size based on workload:

```python
# For high-frequency operations
db_service = DatabaseService(pool_min=5, pool_max=20)

# For low-frequency operations
db_service = DatabaseService(pool_min=1, pool_max=5)
```

### 2. Worker Pool Size

```ini
# .env
MAX_WORKERS=8  # Increase for more parallel processing
```

**Guidelines**:
- **4 workers**: Standard (2-4 pairs per asset type)
- **8 workers**: High volume (5+ pairs per asset type)
- **16 workers**: Very high volume (10+ pairs total)

### 3. Task Intervals

Adjust based on trading style:

```ini
# Scalping/Day Trading
PRICE_FETCH_INTERVAL=30
TRADES_SYNC_INTERVAL=15

# Swing Trading
PRICE_FETCH_INTERVAL=300
TRADES_SYNC_INTERVAL=60
```

## Monitoring

### Worker Statistics

The bridge logs worker statistics every minute:

```
Worker Stats - Active: 2, Queued: 0, Completed: 145, Failed: 0
```

### Health Checks

```python
# Database health
if db_service.health_check():
    print("Database OK")

# Redis health
if redis_service.health_check():
    print("Redis OK")
```

## Migration from V2

### Key Differences

| Feature | V2 | V3 |
|---------|----|----|
| Architecture | Monolithic | Modular MVC |
| Execution | Sequential | Parallel |
| Database | Direct connection | Connection pooling |
| Configuration | Global variables | Centralized Settings class |
| Logging | Basic | Service-based with UTF-8 |
| Extensibility | Hard to extend | Easy plugin system |

### Migration Steps

1. **Copy configuration**: `.env` is compatible, just add new variables
2. **Update imports**: Change strategy imports to use new controllers
3. **Test thoroughly**: V3 has different execution flow
4. **Monitor performance**: Adjust worker pool size if needed

## Troubleshooting

### Unicode Errors (Windows)

Fixed in V3 with automatic UTF-8 configuration:

```python
# logger_service.py handles this automatically
sys.stdout.reconfigure(encoding='utf-8')
```

### Database Connection Pool Exhausted

Increase pool size:

```python
db_service = DatabaseService(pool_min=1, pool_max=20)
```

### Tasks Timing Out

Increase timeout:

```ini
WORKER_TIMEOUT=600  # 10 minutes
```

### High CPU Usage

Reduce worker count and increase intervals:

```ini
MAX_WORKERS=2
PRICE_FETCH_INTERVAL=120
```

## Benefits Over V2

1. **Performance**: 3-4x faster price fetching (parallel execution)
2. **Scalability**: Easy to add new pairs without performance degradation
3. **Maintainability**: Clean separation of concerns
4. **Reliability**: Connection pooling prevents resource exhaustion
5. **Extensibility**: Plugin-style architecture for new features
6. **Monitoring**: Built-in statistics and health checks

## Future Enhancements

- [ ] Web dashboard for monitoring
- [ ] REST API for external control
- [ ] Machine learning strategy module
- [ ] Automated backtesting framework
- [ ] Multi-broker support
- [ ] Cloud deployment scripts

## Support

For issues or questions:
1. Check logs in `mt5_bridge_v3.log`
2. Review worker statistics
3. Verify service health checks
4. Check GitHub issues

## License

Same as main project.
