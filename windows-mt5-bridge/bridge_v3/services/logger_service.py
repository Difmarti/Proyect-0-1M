"""
Centralized logging service with UTF-8 support for Windows
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from bridge_v3.config import Settings


class LoggerService:
    """Centralized logging service"""

    _loggers = {}

    @classmethod
    def setup(cls):
        """Setup root logger with UTF-8 encoding"""
        # Configure stdout for UTF-8 on Windows
        if sys.platform == 'win32':
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except AttributeError:
                # Python < 3.7
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

        # Create logs directory
        log_path = Path(Settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, Settings.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    Settings.LOG_FILE,
                    maxBytes=Settings.LOG_MAX_BYTES,
                    backupCount=Settings.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                ),
                logging.StreamHandler(sys.stdout)
            ]
        )

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger for a module"""
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]

    @classmethod
    def log_banner(cls, logger: logging.Logger, title: str, width: int = 70):
        """Log a formatted banner"""
        logger.info("=" * width)
        logger.info(f"{title:^{width}}")
        logger.info("=" * width)

    @classmethod
    def log_section(cls, logger: logging.Logger, title: str, data: dict, width: int = 70):
        """Log a formatted section with data"""
        logger.info("=" * width)
        logger.info(f"{title:^{width}}")
        logger.info("-" * width)
        for key, value in data.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * width)
