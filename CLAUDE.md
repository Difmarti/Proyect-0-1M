# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is an automated trading bot system for MetaTrader 4/5 with a microservices architecture. The system connects to MT4/5 via a Python bridge, stores trading data in TimescaleDB, and provides real-time monitoring through a Streamlit dashboard.

**Architecture Components:**
- **python_bridge**: MT4/5 connection service that fetches prices, syncs trades, and updates account metrics
- **api**: FastAPI REST service providing endpoints for trade data, metrics, and performance analytics
- **dashboard**: Streamlit real-time monitoring interface
- **timescaledb**: Time-series database for OHLCV data and trading metrics
- **redis**: Caching and message queue
- **portainer**: Container management UI

## Essential Commands

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
- **MT5 credentials**: MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER (e.g., Tickmill-Demo)
- **Trading parameters**:
  - TRADING_PAIRS (comma-separated: EURUSD,GBPUSD,USDJPY)
  - TRADING_TIMEFRAME (default: M15)
  - MAX_DAILY_DRAWDOWN (default: 6%)
  - RISK_PER_TRADE (default: 2%)
  - MAX_SIMULTANEOUS_TRADES (default: 3)
  - TRADING_START_TIME / TRADING_END_TIME (Colombia timezone UTC-5)
- **Database**: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- **Ports**: API_PORT (8080), DASHBOARD_PORT (8501)

### Service Ports
- TimescaleDB: 5432
- Redis: 6379
- API: 8080 (http://localhost:8080/docs for Swagger UI)
- Dashboard: 8501 (http://localhost:8501)
- Portainer: 9000

## Common Development Tasks

### Adding New Currency Pairs
1. Update `TRADING_PAIRS` in `.env` (comma-separated)
2. Restart python_bridge: `docker-compose restart trading_bridge`

### Modifying Trading Strategy
The strategy logic should be added to python-bridge/main.py. Currently, the bridge only syncs data but doesn't execute trades based on signals. The `trading_signals` table exists for storing strategy decisions.

### Database Queries
Key functions in postgres/init.sql:
- `calculate_drawdown()`: Returns current drawdown percentage
- `update_account_metrics(balance, equity, margin, free_margin)`: Inserts account snapshot

### Testing Services
```bash
# Test API health
curl http://localhost:8080/health

# Test database connection
docker exec trading_timescaledb pg_isready -U trading_user

# Test Redis
docker exec trading_redis redis-cli ping
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
