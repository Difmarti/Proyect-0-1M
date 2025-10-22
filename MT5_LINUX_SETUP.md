# MT5 Linux Setup Guide

## Overview

This trading bot system now supports **native MT5 execution on Linux** using the official MetaQuotes installation method. The system runs MT5 in a Docker container with Wine, providing a completely containerized solution.

## What Changed

### ✅ MT5 Linux Support Added
- **New Service**: `metatrader5` Docker container running MT5 via Wine
- **Official Method**: Uses MetaQuotes' official Linux installer
- **Headless Execution**: MT5 runs without GUI using Xvfb virtual display
- **Auto-Login**: Automatically connects to your broker using credentials from `.env`

### ✅ Updated Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   MT5        │◄─────┤ Python       │                │
│  │  (Wine)      │      │  Bridge      │                │
│  │              │      │ (MT5 API)    │                │
│  └──────────────┘      └───────┬──────┘                │
│                                 │                        │
│                        ┌────────▼────────┐              │
│                        │  TimescaleDB    │              │
│                        │  (Trading Data) │              │
│                        └────────┬────────┘              │
│                                 │                        │
│                        ┌────────▼────────┐              │
│                        │   FastAPI       │              │
│                        │   (REST API)    │              │
│                        └────────┬────────┘              │
│                                 │                        │
│                        ┌────────▼────────┐              │
│                        │   Streamlit     │              │
│                        │  (Dashboard)    │              │
│                        └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Ubuntu 22.04 LTS (recommended)
- Docker and Docker Compose installed
- 8GB RAM minimum (recommended)
- 10GB free disk space
- Available ports: 5432, 6379, 8080, 8501, 9000

### Quick Start

```bash
# 1. Clone the repository (if not already)
git clone <repository-url>
cd Proyect-0-1M

# 2. Make scripts executable
chmod +x *.sh

# 3. Run installation
./install.sh
```

The installation script will:
1. ✅ Verify system requirements (Ubuntu, Docker, RAM, ports)
2. ✅ Create project structure
3. ✅ Generate secure passwords
4. ✅ Build Docker images (including MT5)
5. ✅ Start all services
6. ✅ Perform health checks
7. ✅ Verify database setup

### Post-Installation

After installation completes, you need to:

1. **Update MT5 Credentials** in `.env`:
   ```bash
   MT5_ACCOUNT=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=your_broker_server
   ```

2. **Restart MT5 Container**:
   ```bash
   docker compose restart metatrader5 trading_bridge
   ```

3. **Verify MT5 Connection**:
   ```bash
   # Check if MT5 is running
   docker logs trading_mt5

   # Check Python bridge connection
   docker logs trading_bridge
   ```

4. **Access Services**:
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8080/docs
   - Portainer: http://localhost:9000

## Configuration

### MT5 Credentials

Edit `.env` file with your MetaTrader 5 account details:

```bash
# For Tickmill Demo Account (example)
MT5_ACCOUNT=20264646
MT5_PASSWORD=your_password
MT5_SERVER=Tickmill-Demo

# For other brokers
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Live  # or YourBroker-Demo
```

### Trading Strategy Parameters

The system implements a **Bollinger Bands Mean Reversion** strategy. Configure in `.env`:

```bash
# Technical Indicators
BB_PERIOD=20                    # Bollinger Bands period
BB_DEVIATION=2                  # Standard deviations
RSI_PERIOD=14                   # RSI period
EMA_PERIOD=200                  # EMA trend filter
ATR_PERIOD=14                   # ATR for stop loss

# Entry Conditions
RSI_OVERSOLD=30                 # RSI buy threshold
RSI_OVERBOUGHT=70               # RSI sell threshold

# Risk Management
RISK_PER_TRADE=2                # Risk 2% per trade
MAX_DAILY_DRAWDOWN=6            # Stop trading at 6% daily loss
MAX_SIMULTANEOUS_TRADES=3       # Max 3 concurrent positions
SL_ATR_MULTIPLIER=1.5           # Stop loss = 1.5 * ATR
TRAILING_STOP_PERCENT=50        # Move SL to BE at 50% TP

# Trading Hours (Colombia time UTC-5)
TRADING_START_TIME=08:00
TRADING_END_TIME=22:00
```

## Management

### Start/Stop Services

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
./restore.sh backups/backup_file.tar.gz
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker logs -f trading_mt5
docker logs -f trading_bridge
docker logs -f trading_api
docker logs -f trading_dashboard
```

### Restart Specific Service

```bash
# Restart MT5
docker compose restart metatrader5

# Restart Python bridge
docker compose restart trading_bridge

# Rebuild service after code changes
docker compose up -d --build trading_bridge
```

## Troubleshooting

### MT5 Not Connecting

**Problem**: Python bridge can't connect to MT5

**Solution**:
```bash
# 1. Check if MT5 process is running
docker exec trading_mt5 pgrep -f terminal64.exe

# 2. Check Wine installation
docker exec trading_mt5 wine --version

# 3. View MT5 logs
docker logs trading_mt5

# 4. Restart MT5 container
docker compose restart metatrader5

# 5. If still not working, rebuild
docker compose up -d --build metatrader5
```

### Invalid Credentials

**Problem**: "Authorization failed" in logs

**Solution**:
1. Verify credentials in `.env` are correct
2. Test login manually on MT5 desktop app first
3. Ensure server name is exact (case-sensitive)
4. For demo accounts, server usually ends with "-Demo"

### Container Won't Start

**Problem**: Service fails to start

**Solution**:
```bash
# Check detailed error
docker logs [container_name]

# Check resource usage
docker system df

# Remove and recreate
docker compose down
docker compose up -d
```

### No Data in Dashboard

**Problem**: Dashboard shows "No data available"

**Possible Causes**:
1. MT5 not connected → Check `docker logs trading_mt5`
2. Python bridge not running → Check `docker logs trading_bridge`
3. Database connection issue → Check `docker logs trading_timescaledb`
4. No trades executed yet → Wait for trading signals

**Debug Steps**:
```bash
# Test database connection
docker exec trading_timescaledb psql -U trading_user -d trading_db -c "SELECT COUNT(*) FROM price_data;"

# Check if python bridge is writing data
docker exec trading_bridge python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.account_info())"
```

## System Requirements Validation

The `install.sh` script checks:
- ✅ Ubuntu version
- ✅ Docker installation
- ✅ Docker Compose version
- ✅ Available RAM (8GB recommended)
- ✅ Port availability (5432, 6379, 8080, 8501, 9000)
- ✅ Disk space

## File Structure

```
trading-bot/
├── docker-compose.yml           # Service orchestration
├── .env                         # Configuration (created from .env.example)
├── install.sh                   # Installation script ⭐ UPDATED
├── start_bot.sh                 # Start services
├── stop_bot.sh                  # Stop services
├── check_health.sh              # Health monitoring
├── backup.sh                    # Backup database
├── restore.sh                   # Restore from backup
│
├── metatrader5/                 # ⭐ NEW: MT5 Container
│   ├── Dockerfile               # MT5 Wine setup
│   ├── start_mt5.sh             # MT5 startup script
│   └── config/                  # MT5 configuration
│
├── python-bridge/               # ⭐ UPDATED
│   ├── Dockerfile               # Now includes MetaTrader5 library
│   ├── requirements.txt         # Python dependencies
│   ├── main.py                  # MT5 bridge logic
│   └── README_MT5.md            # MT5 integration docs ⭐ UPDATED
│
├── postgres/
│   └── init.sql                 # Database schema
│
├── api/
│   ├── Dockerfile
│   └── main.py                  # FastAPI endpoints
│
├── dashboard/
│   ├── Dockerfile
│   └── app.py                   # Streamlit dashboard
│
└── CLAUDE.md                    # Development guide ⭐ UPDATED
```

## Security Notes

1. **Never commit `.env` file** to version control
2. **Change default passwords** in production
3. **Use strong MT5 passwords** (broker requirement)
4. **Restrict port access** if exposing to internet
5. **Regular backups** using `./backup.sh`

## Next Steps

1. ✅ Verify installation completed successfully
2. ✅ Update MT5 credentials in `.env`
3. ✅ Restart services to apply credentials
4. ✅ Monitor logs for successful MT5 connection
5. ✅ Access dashboard to see real-time data
6. ✅ Wait for first trading signals (based on strategy rules)
7. ✅ Monitor performance and adjust parameters

## Support

For issues:
1. Check logs: `docker compose logs -f [service]`
2. Review CLAUDE.md for development details
3. Read python-bridge/README_MT5.md for MT5 specifics
4. Use `./check_health.sh` for system status

## Official MetaQuotes Resources

- MT5 Linux Installation: https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux
- MT5 Python Documentation: https://www.mql5.com/en/docs/python_metatrader5
- Download MT5 Linux: https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh
