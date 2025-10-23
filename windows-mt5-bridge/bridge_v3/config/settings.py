"""
Centralized configuration management for MT5 Bridge V3
Loads all settings from environment variables
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Centralized settings configuration"""

    # MT5 Configuration
    MT5_ACCOUNT: int = int(os.getenv('MT5_ACCOUNT', '0'))
    MT5_PASSWORD: str = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER: str = os.getenv('MT5_SERVER', '')
    MT5_PATH: str = os.getenv('MT5_PATH', '')  # Optional: path to terminal64.exe

    # Database Configuration (Linux server)
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'trading_db')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'trading_user')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', '')

    # Redis Configuration (Linux server)
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))

    # Forex Configuration
    FOREX_PAIRS: List[str] = os.getenv('FOREX_PAIRS', 'EURUSD,GBPUSD,USDJPY').split(',')
    FOREX_TIMEFRAME: str = os.getenv('FOREX_TIMEFRAME', 'M15')

    # Crypto Configuration
    CRYPTO_ENABLED: bool = os.getenv('CRYPTO_ENABLED', 'false').lower() == 'true'
    CRYPTO_PAIRS: List[str] = (
        os.getenv('CRYPTO_PAIRS', 'BTCUSD,ETHUSD,LTCUSD,XRPUSD').split(',')
        if os.getenv('CRYPTO_ENABLED', 'false').lower() == 'true'
        else []
    )
    CRYPTO_TIMEFRAME: int = int(os.getenv('CRYPTO_TIMEFRAME', '15'))

    # Risk Management
    MAX_DAILY_LOSS_PCT: float = float(os.getenv('MAX_DAILY_LOSS_PCT', '10.0'))
    RISK_PER_TRADE: float = float(os.getenv('RISK_PER_TRADE', '2.0'))
    MAX_SIMULTANEOUS_TRADES: int = int(os.getenv('MAX_SIMULTANEOUS_TRADES', '5'))

    # Scheduling Configuration
    PRICE_FETCH_INTERVAL: int = int(os.getenv('PRICE_FETCH_INTERVAL', '60'))  # seconds
    METRICS_SYNC_INTERVAL: int = int(os.getenv('METRICS_SYNC_INTERVAL', '60'))  # seconds
    TRADES_SYNC_INTERVAL: int = int(os.getenv('TRADES_SYNC_INTERVAL', '30'))  # seconds
    CRYPTO_ANALYSIS_INTERVAL: int = int(os.getenv('CRYPTO_ANALYSIS_INTERVAL', '60'))  # seconds

    # Parallel Execution Settings
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))  # Number of parallel workers
    WORKER_TIMEOUT: int = int(os.getenv('WORKER_TIMEOUT', '300'))  # Worker timeout in seconds

    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'mt5_bridge_v3.log')
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))

    @classmethod
    def get_db_connection_string(cls) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        required_fields = [
            ('MT5_ACCOUNT', cls.MT5_ACCOUNT),
            ('MT5_PASSWORD', cls.MT5_PASSWORD),
            ('MT5_SERVER', cls.MT5_SERVER),
            ('POSTGRES_PASSWORD', cls.POSTGRES_PASSWORD),
        ]

        missing = []
        for field_name, field_value in required_fields:
            if not field_value or (isinstance(field_value, int) and field_value == 0):
                missing.append(field_name)

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True

    @classmethod
    def display_config(cls) -> str:
        """Display current configuration (without sensitive data)"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║  MT5 Bridge V3 - Configuration                                   ║
╠══════════════════════════════════════════════════════════════════╣
║  MT5 Account: {cls.MT5_ACCOUNT:<50} ║
║  MT5 Server: {cls.MT5_SERVER:<51} ║
║  PostgreSQL: {cls.POSTGRES_HOST}:{cls.POSTGRES_PORT:<45} ║
║  Redis: {cls.REDIS_HOST}:{cls.REDIS_PORT:<55} ║
║                                                                  ║
║  Forex Pairs: {', '.join(cls.FOREX_PAIRS):<50} ║
║  Forex Timeframe: {cls.FOREX_TIMEFRAME:<48} ║
║                                                                  ║
║  Crypto Enabled: {str(cls.CRYPTO_ENABLED):<49} ║
║  Crypto Pairs: {', '.join(cls.CRYPTO_PAIRS) if cls.CRYPTO_ENABLED else 'N/A':<49} ║
║  Crypto Timeframe: {cls.CRYPTO_TIMEFRAME if cls.CRYPTO_ENABLED else 'N/A':<47} ║
║                                                                  ║
║  Max Daily Loss: {cls.MAX_DAILY_LOSS_PCT}%{' ' * 48} ║
║  Risk Per Trade: {cls.RISK_PER_TRADE}%{' ' * 48} ║
║  Max Parallel Workers: {cls.MAX_WORKERS:<43} ║
╚══════════════════════════════════════════════════════════════════╝
        """
