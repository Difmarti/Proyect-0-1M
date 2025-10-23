"""
MetaTrader 5 connection and operations service
"""

import MetaTrader5 as mt5
import pandas as pd
from typing import Optional, List
from datetime import datetime

from bridge_v3.config import Settings, TimeFrames
from bridge_v3.models import Position, PriceData
from bridge_v3.services.logger_service import LoggerService


logger = LoggerService.get_logger(__name__)


class MT5Service:
    """MetaTrader 5 connection and operations"""

    def __init__(self):
        self.initialized = False
        self.account_info = None

    def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if Settings.MT5_PATH:
                if not mt5.initialize(Settings.MT5_PATH):
                    logger.error(f"MT5 initialize() failed with path {Settings.MT5_PATH}, error: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    logger.error(f"MT5 initialize() failed, error: {mt5.last_error()}")
                    return False

            # Login if credentials provided
            if Settings.MT5_ACCOUNT and Settings.MT5_PASSWORD and Settings.MT5_SERVER:
                authorized = mt5.login(
                    Settings.MT5_ACCOUNT,
                    password=Settings.MT5_PASSWORD,
                    server=Settings.MT5_SERVER
                )
                if not authorized:
                    logger.error(f"MT5 login failed, error: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
                logger.info(f"MT5 logged in to {Settings.MT5_SERVER} with account {Settings.MT5_ACCOUNT}")
            else:
                logger.info("MT5 initialized without login (using existing session)")

            # Get and store account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get account info")
                return False

            logger.info(
                f"MT5 Account: {self.account_info.login}, "
                f"Balance: {self.account_info.balance}, "
                f"Server: {self.account_info.server}"
            )
            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            logger.info("MT5 connection closed")

    def get_account_info(self):
        """Get current account information"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")
        return mt5.account_info()

    def fetch_price_data(
        self,
        symbol: str,
        timeframe: str,
        bars: int = 1000
    ) -> Optional[PriceData]:
        """Fetch price data for a symbol"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")

        try:
            tf = TimeFrames.get(timeframe)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

            if rates is None or len(rates) == 0:
                logger.warning(f"No data received for {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            return PriceData(
                symbol=symbol,
                timeframe=timeframe,
                data=df,
                last_update=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None

    def fetch_crypto_data(
        self,
        symbol: str,
        timeframe_minutes: int,
        bars: int = 200
    ) -> Optional[PriceData]:
        """Fetch crypto price data"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")

        try:
            tf = TimeFrames.from_minutes(timeframe_minutes)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

            if rates is None or len(rates) == 0:
                logger.warning(f"No crypto data received for {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            # Ensure volume column exists
            if 'volume' not in df.columns and 'tick_volume' in df.columns:
                df['volume'] = df['tick_volume']

            return PriceData(
                symbol=symbol,
                timeframe=f"M{timeframe_minutes}",
                data=df,
                last_update=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
            return None

    def get_positions(self) -> List[Position]:
        """Get all active positions"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            result = []
            for pos in positions:
                position = Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    position_type='BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    volume=pos.volume,
                    price_open=pos.price_open,
                    price_current=pos.price_current,
                    sl=pos.sl,
                    tp=pos.tp,
                    profit=pos.profit,
                    time=datetime.fromtimestamp(pos.time),
                    magic=pos.magic,
                    comment=pos.comment
                )
                result.append(position)

            return result

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_symbol_info(self, symbol: str):
        """Get symbol information"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")
        return mt5.symbol_info(symbol)

    def get_symbol_info_tick(self, symbol: str):
        """Get latest tick for symbol"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")
        return mt5.symbol_info_tick(symbol)

    def send_order(self, request: dict):
        """Send a trade order to MT5"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")

        result = mt5.order_send(request)
        if result is None:
            logger.error(f"Order send failed: {mt5.last_error()}")
        return result

    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not self.initialized:
            raise RuntimeError("MT5 not initialized")

        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.error(f"Position {ticket} not found")
                return False

            pos = position[0]

            # Determine reverse type
            reverse_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            # Get current price
            tick = mt5.symbol_info_tick(pos.symbol)
            price = tick.bid if reverse_type == mt5.ORDER_TYPE_SELL else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": reverse_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": pos.magic,
                "comment": "Close by bridge",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close position {ticket}: {result.comment}")
                return False

            logger.info(f"Position {ticket} closed successfully")
            return True

        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}")
            return False
