# Automated Trading Bot System

A complete trading bot system for algorithmic trading using MetaTrader 4, with a modern microservices architecture and real-time monitoring dashboard.

## System Architecture

The system consists of several containerized services:

- **TimescaleDB**: Time-series database for storing trading data
- **Redis**: In-memory database for caching and message queue
- **Python Bridge**: Connects to MT4 and processes trading signals
- **FastAPI**: REST API for data access and bot control
- **Streamlit Dashboard**: Real-time monitoring interface
- **Portainer**: Container management UI

## Prerequisites

- Ubuntu 22.04 LTS
- Docker and Docker Compose
- 8GB RAM minimum
- MetaTrader 4 installed via Wine
- Available ports: 5432, 6379, 8000, 8501, 9000

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trading-bot.git
   cd trading-bot
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Run the installation script:
   ```bash
   chmod +x *.sh
   ./install.sh
   ```

4. Access the services:
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8000/docs
   - Portainer: http://localhost:9000

## Configuration

### Environment Variables

Key environment variables in `.env`:

- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `MT4_ACCOUNT`: MetaTrader account number
- `MT4_PASSWORD`: MetaTrader password
- `MT4_SERVER`: Broker server name
- `TRADING_PAIRS`: Comma-separated list of currency pairs
- `MAX_DAILY_DRAWDOWN`: Maximum allowed daily drawdown (%)
- `RISK_PER_TRADE`: Risk per trade (% of balance)

### Trading Parameters

The trading strategy parameters are configured in the Python bridge service:

- Timeframe: M15
- Indicators:
  * Bollinger Bands (20, 2)
  * RSI (14)
  * EMA (200)
  * ATR (14)
- Risk Management:
  * Max daily drawdown: 6%
  * Risk per trade: 2%
  * Max simultaneous trades: 3
  * Trading hours: 3:00 AM - 5:00 PM (Colombia)

## Management Scripts

- `start_bot.sh`: Start all services
- `stop_bot.sh`: Stop all services gracefully
- `check_health.sh`: Check system health
- `backup.sh`: Create system backup
- `restore.sh`: Restore from backup

## Project Structure

```
trading-bot/
├── docker-compose.yml      # Service definitions
├── .env.example           # Environment variables template
├── postgres/
│   └── init.sql          # Database initialization
├── python-bridge/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py           # MT4 bridge logic
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py           # FastAPI application
└── dashboard/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py            # Streamlit dashboard
```

## Monitoring

The Streamlit dashboard provides real-time monitoring of:

- Account balance and equity
- Active trades
- Win rate and profit factor
- Performance by currency pair
- Trading hours heat map
- Equity curve

## Backup and Recovery

Create a backup:
```bash
./backup.sh
```

Restore from backup:
```bash
./restore.sh backups/full_backup_20231021_120000.tar.gz
```

## Troubleshooting

Common issues and solutions:

1. **Services not starting**
   - Check logs: `docker-compose logs -f [service_name]`
   - Verify port availability
   - Check system resources

2. **MT4 connection issues**
   - Verify MT4 is running in Wine
   - Check account credentials
   - Ensure DLL imports are allowed

3. **Database errors**
   - Check PostgreSQL logs
   - Verify credentials in .env
   - Check disk space

4. **Performance issues**
   - Monitor resource usage with `check_health.sh`
   - Consider reducing the number of currency pairs
   - Optimize database queries

## Adding New Features

### Adding New Currency Pairs

1. Update `TRADING_PAIRS` in `.env`
2. Restart the Python bridge service:
   ```bash
   docker-compose restart trading_bridge
   ```

### Modifying Risk Parameters

1. Update risk settings in `.env`
2. Restart the Python bridge service
3. Verify changes in the dashboard

### Adding New Indicators

1. Modify `python-bridge/main.py`
2. Add new columns to the database schema
3. Update the dashboard visualizations

## Safety Features

- Automatic trade closure on high drawdown
- Broker connection monitoring
- Data persistence and recovery
- Regular automated backups
- Health monitoring and alerts

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

## Support

For issues and feature requests, please create an issue in the GitHub repository.
