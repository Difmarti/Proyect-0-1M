# MetaTrader5 Integration for Linux

## Official MT5 Linux Support

MetaQuotes provides **official native Linux support** for MetaTrader 5. This project uses the official installation method.

### Official Installation Script

```bash
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh
chmod +x mt5linux.sh
./mt5linux.sh
```

## Docker Architecture

This project runs MT5 in a separate Docker container using Wine, and the Python bridge communicates with it:

### Container Structure
- **metatrader5**: Runs MT5 terminal via Wine with Xvfb (virtual display)
- **python_bridge**: Runs Python with MetaTrader5 library, connects to MT5 container

### MetaTrader5 Python Library

The `MetaTrader5` Python package works on Linux when connecting to a running MT5 terminal. It's now included in the Docker image.

## Installation Methods

### Method 1: Docker (Recommended for Production)

The entire stack runs in Docker:

```bash
# Start all services including MT5
docker-compose up -d

# Check MT5 container
docker logs trading_mt5

# Check Python bridge connection
docker logs trading_bridge
```

### Method 2: Local Development (Linux)

Install MT5 locally using the official script:

```bash
# Download and install MT5
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh
chmod +x mt5linux.sh
./mt5linux.sh

# Install Python dependencies
pip install -r python-bridge/requirements.txt
pip install MetaTrader5

# Run the bridge
python python-bridge/main.py
```

### Method 3: Windows Development

For Windows development:

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r python-bridge/requirements.txt
pip install MetaTrader5

# Run the bridge
python python-bridge/main.py
```

## Configuration

MT5 credentials are configured via environment variables (`.env`):

```bash
MT5_ACCOUNT=20264646
MT5_PASSWORD=your_password
MT5_SERVER=Tickmill-Demo
```

## Troubleshooting

### MT5 Container Won't Start
```bash
# Check logs
docker logs trading_mt5

# Verify Wine installation
docker exec trading_mt5 wine --version

# Check X server
docker exec trading_mt5 ps aux | grep Xvfb
```

### Python Bridge Can't Connect
```bash
# Verify MT5 is running
docker exec trading_mt5 pgrep -f terminal64.exe

# Check Python bridge logs
docker logs trading_bridge

# Test MT5 initialization
docker exec trading_bridge python -c "import MetaTrader5 as mt5; print(mt5.initialize())"
```

### Connection Issues

The MetaTrader5 Python library connects to the MT5 terminal process. Ensure:
1. MT5 terminal is running
2. Correct credentials in `.env`
3. Network connectivity between containers
4. DLL imports enabled in MT5 settings

