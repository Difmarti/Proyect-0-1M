# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is an automated trading bot system for MetaTrader 5 with a microservices architecture. The system supports two deployment modes:

1. **Docker Mode**: MT5 runs in a Wine container alongside other services
2. **Windows Bridge Mode**: MT5 runs natively on Windows, connects remotely to Linux services

**Core Architecture Components:**
- **python-bridge** OR **windows-mt5-bridge**: MT5 connection service that fetches prices, syncs trades, and updates account metrics
- **api**: FastAPI REST service providing endpoints for trade data, metrics, and performance analytics
- **dashboard**: Streamlit real-time monitoring interface
- **timescaledb**: Time-series database optimized for OHLCV data and trading metrics (PostgreSQL with hypertables)
- **redis**: High-speed caching layer for real-time metrics
- **metatrader5** (Docker only): MT5 terminal running in Wine with Xvfb virtual display

**Network Architecture (Windows Bridge Mode):**
```
Windows Machine (MT5 Native)     →  TCP/IP  →    Linux Server (Docker)
├─ MetaTrader 5 Terminal                         ├─ TimescaleDB (5432)
└─ mt5_bridge.py                                 ├─ Redis (6379)
   (Standalone Python)                            ├─ API (8080)
                                                  └─ Dashboard (8501)
```

## Essential Commands

### Initial Setup
```bash
# Complete installation with validation (recommended for first setup)
./install.sh
# This script will:
# - Verify system requirements (Ubuntu, RAM, Docker)
# - Check port availability
# - Create .env from .env.example
# - Generate secure PostgreSQL password
# - Build Docker images
# - Start services
# - Perform health checks
```

### Starting and Stopping
```bash
# Start all services
./start_bot.sh

# Stop all services
./stop_bot.sh

# Check system health
./check_health.sh

# Create backup
./backup.sh

# Restore from backup
./restore.sh backups/full_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Docker Operations
```bash
# Start services
docker-compose up -d

# View logs for specific service
docker-compose logs -f [trading_bridge|api|dashboard|timescaledb|redis]

# Restart specific service
docker-compose restart [service_name]

# Rebuild service after code changes
docker-compose up -d --build [service_name]

# Stop and remove all containers
docker-compose down
```

### Development
```bash
# Access database directly
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

# Access Redis CLI
docker exec -it trading_redis redis-cli

# View real-time logs
docker-compose logs -f trading_bridge
```

## Key Architecture Details

### Data Flow
1. **python_bridge** (python-bridge/main.py) runs scheduled tasks:
   - Every 1 minute: fetches price data from MT4/5 and stores in TimescaleDB
   - Every 1 minute: updates account metrics (balance, equity, margin)
   - Every 30 seconds: syncs active trades and moves closed trades to history

2. **API** (api/main.py) provides REST endpoints consumed by dashboard:
   - `/metrics` - Current account metrics
   - `/trades/open` - Active trades
   - `/trades/history` - Historical trades
   - `/performance/by_pair` - Performance grouped by currency pair
   - `/equity/curve` - Equity curve data

3. **Dashboard** (dashboard/app.py) auto-refreshes every 5 seconds displaying:
   - Account overview metrics
   - Active trades table
   - Equity curve chart
   - Performance by currency pair
   - Trading hours heatmap

### Database Schema (postgres/init.sql)
- `price_data` (hypertable): OHLCV data partitioned by time
- `active_trades`: Currently open positions (synced with MT4/5)
- `trade_history`: Closed trades with profit/loss
- `trading_signals`: Bot decisions and signals (hypertable)
- `account_metrics` (hypertable): Balance, equity, margin snapshots
- `trade_stats` (view): Aggregated statistics (win rate, profit factor)

### MetaTrader5 Integration
**MT5 Linux Support**: MetaQuotes provides official Linux support for MetaTrader 5. This system runs MT5 natively in a Docker container using Wine.

**Architecture**:
- `metatrader5` container: Runs MT5 terminal via Wine with Xvfb (virtual display)
- `python_bridge` container: Connects to MT5 using the MetaTrader5 Python library
- Communication happens over the shared Docker network

**Official Installation**:
```bash
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh
chmod +x mt5linux.sh
./mt5linux.sh
```

**Container Details**:
- MT5 runs headless (no GUI) via Xvfb on DISPLAY :99
- Wine 64-bit environment for Windows compatibility
- Shared volume for MT5 data persistence
- Auto-login with credentials from .env

See python-bridge/README_MT5.md for detailed troubleshooting.

### Configuration
All configuration is in `.env` (copy from `.env.example`):

**MT5 Credentials:**
- MT5_ACCOUNT: Account number
- MT5_PASSWORD: Account password
- MT5_SERVER: Broker server (e.g., "Tickmill-Demo")

**Trading Parameters:**
- TRADING_PAIRS: Comma-separated pairs (e.g., "EURUSD,GBPUSD,USDJPY")
- TRADING_TIMEFRAME: Default M15
- MAX_DAILY_DRAWDOWN: Default 6%
- RISK_PER_TRADE: Default 2%
- MAX_SIMULTANEOUS_TRADES: Default 3
- TRADING_START_TIME / TRADING_END_TIME: Colombia timezone (UTC-5)

**Strategy Parameters (Bollinger Bands Mean Reversion):**
- BB_PERIOD: Bollinger Bands period (default: 20)
- BB_DEVIATION: Standard deviations (default: 2)
- RSI_PERIOD: RSI period (default: 14)
- EMA_PERIOD: EMA trend filter (default: 200)
- ATR_PERIOD: ATR for stop loss (default: 14)
- SL_ATR_MULTIPLIER: Stop loss multiplier (default: 1.5)

**Database & Services:**
- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- API_PORT (default: 8080), DASHBOARD_PORT (default: 8501)
- REDIS_PORT (default: 6379)

**Windows Bridge Only:**
- POSTGRES_HOST: Linux server IP (e.g., "192.168.1.100")
- REDIS_HOST: Linux server IP

### Service Ports
- TimescaleDB: 5432
- Redis: 6379
- API: 8080 (http://localhost:8080/docs for Swagger UI)
- Dashboard: 8501 (http://localhost:8501)
- Portainer: 9000

## Key Technical Details

### Hypertables (TimescaleDB)
The system uses TimescaleDB's hypertables for automatic time-based partitioning:
- **price_data**: Partitioned by day, stores millions of OHLCV bars
- **trading_signals**: Partitioned by day, records strategy decisions
- **account_metrics**: Partitioned by day, equity curve snapshots

Hypertables enable:
- Fast queries on large datasets (automatic indexing)
- Automatic data retention (drop old partitions)
- Compression for data older than 7 days

### Timezone Handling
All times are converted to Colombia timezone (UTC-5):
```python
self.colombia_tz = pytz.timezone('America/Bogota')
```
This affects TRADING_START_TIME and TRADING_END_TIME enforcement.

### Redis Caching Pattern
```python
# Latest metrics cached with 60-second TTL
redis.set('account:metrics', json.dumps(metrics), ex=60)
```
Dashboard queries Redis first, falls back to PostgreSQL. Reduces database load.

### Connection Architecture
- **API**: Creates fresh PostgreSQL connection per request (no pooling)
- **Bridge**: Persistent connections with automatic reconnection on failure
- **Docker restart policy**: `unless-stopped` ensures services recover from crashes

## Common Development Tasks

### Adding New Currency Pairs
1. Edit `.env`: `TRADING_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD`
2. Restart bridge: `docker-compose restart trading_bridge` (or restart Windows bridge)
3. Verify in dashboard after ~1 minute

### Modifying Trading Strategy
Strategy logic is in python-bridge/main.py or windows-mt5-bridge/mt5_bridge.py. The `trading_signals` table exists for storing strategy decisions, but trade execution logic must be implemented separately.

### Rebuilding Services After Code Changes
```bash
# Rebuild specific service
docker-compose up -d --build api
docker-compose up -d --build dashboard
docker-compose up -d --build trading_bridge

# Rebuild all services
docker-compose build --no-cache
docker-compose up -d
```

### Database Operations
```bash
# Access database directly
docker exec -it trading_timescaledb psql -U trading_user -d trading_db

# Useful queries
SELECT * FROM price_data ORDER BY time DESC LIMIT 10;
SELECT * FROM account_metrics ORDER BY time DESC LIMIT 1;
SELECT * FROM active_trades;
SELECT * FROM trade_stats;

# Key stored functions
SELECT calculate_drawdown();  -- Current drawdown percentage
```

### Testing Services
```bash
# Test API health
curl http://localhost:8080/health

# Test database connection
docker exec trading_timescaledb pg_isready -U trading_user -d trading_db

# Test Redis
docker exec trading_redis redis-cli ping

# View API documentation
# Open browser: http://localhost:8080/docs
```

## Troubleshooting

### Services Won't Start
1. Check logs: `docker-compose logs -f [service_name]`
2. Verify ports are available: `netstat -tuln | grep -E '5432|6379|8080|8501|9000'`
3. Check Docker resources: `docker system df`

### MT5 Connection Issues

**Check MT5 container**:
```bash
# Verify MT5 is running
docker logs trading_mt5

# Check if MT5 terminal process is alive
docker exec trading_mt5 pgrep -f terminal64.exe

# Verify Wine is working
docker exec trading_mt5 wine --version

# Check Xvfb (virtual display)
docker exec trading_mt5 ps aux | grep Xvfb
```

**Check Python bridge connection**:
```bash
# View connection logs
docker logs -f trading_bridge

# Test MT5 initialization manually
docker exec trading_bridge python -c "import MetaTrader5 as mt5; print(mt5.initialize())"
```

**Common fixes**:
- Verify credentials in `.env` are correct
- Ensure MT5_SERVER matches your broker (e.g., "Tickmill-Demo")
- Restart MT5 container: `docker compose restart metatrader5`
- Check if MT5 needs manual setup: `docker exec -it trading_mt5 bash`

### Database Connection Failures
- Verify TimescaleDB is healthy: `docker ps` (check STATUS column)
- Check credentials match in `.env` and docker-compose.yml
- Test connection: `docker exec trading_timescaledb pg_isready -U trading_user -d trading_db`
- Ensure volume has sufficient space: `docker volume inspect trading_timescale_data`
- Check database logs: `docker logs trading_timescaledb`

### Service Won't Start
```bash
# View detailed service status
docker compose ps

# Check specific service logs
docker logs [service_name]

# Rebuild specific service
docker compose up -d --build [service_name]

# Full system restart
docker compose down && docker compose up -d
```

## Windows Bridge Setup

For running MT5 natively on Windows instead of Docker:

### Installation
1. Copy `windows-mt5-bridge/` directory to Windows machine
2. Install Python 3.11+ (add to PATH)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure:
   - MT5 credentials (same as Docker mode)
   - `POSTGRES_HOST`: IP of Linux server (e.g., "192.168.1.100")
   - `REDIS_HOST`: IP of Linux server

### Linux Server Firewall Configuration
```bash
# Allow PostgreSQL from Windows IP
sudo ufw allow from 192.168.1.XXX to any port 5432

# Allow Redis from Windows IP
sudo ufw allow from 192.168.1.XXX to any port 6379
```

### Running the Bridge
```powershell
# Run manually
python mt5_bridge.py

# View logs
Get-Content mt5_bridge.log -Wait -Tail 50
```

### Running as Windows Service
Use NSSM or Task Scheduler to run mt5_bridge.py automatically at startup. See windows-mt5-bridge/README.md for detailed instructions.

## Project Structure

```
trading-bot/
├── docker-compose.yml              # Service orchestration
├── .env.example                    # Configuration template
├── install.sh                      # Setup wizard
├── start_bot.sh / stop_bot.sh     # Service control
├── check_health.sh / backup.sh    # Maintenance scripts
├── postgres/init.sql              # Database schema and hypertables
├── python-bridge/                 # Docker MT5 bridge
│   ├── main.py                    # Core sync logic
│   └── README_MT5.md              # MT5 integration guide
├── windows-mt5-bridge/            # Windows standalone bridge
│   ├── mt5_bridge.py              # Identical sync logic
│   └── README.md                  # Windows setup guide
├── api/
│   └── main.py                    # FastAPI endpoints
├── dashboard/
│   └── app.py                     # Streamlit UI
└── metatrader5/
    ├── Dockerfile                 # Wine + MT5
    └── start_mt5.sh               # MT5 initialization
