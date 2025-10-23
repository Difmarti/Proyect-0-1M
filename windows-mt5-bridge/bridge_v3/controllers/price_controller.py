"""
Price data controller - handles fetching and storing price data
"""

from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from bridge_v3.config import Settings
from bridge_v3.services import MT5Service, DatabaseService, LoggerService
from bridge_v3.models import PriceData


logger = LoggerService.get_logger(__name__)


class PriceController:
    """Controller for price data operations"""

    def __init__(self, mt5_service: MT5Service, db_service: DatabaseService):
        self.mt5 = mt5_service
        self.db = db_service

    def fetch_and_store_forex_prices(self) -> dict:
        """Fetch and store all Forex price data"""
        results = {'success': 0, 'failed': 0, 'symbols': []}

        for symbol in Settings.FOREX_PAIRS:
            symbol = symbol.strip()
            try:
                price_data = self.mt5.fetch_price_data(
                    symbol,
                    Settings.FOREX_TIMEFRAME,
                    bars=1000
                )

                if price_data:
                    inserted = self.db.store_price_data(price_data)
                    results['success'] += 1
                    results['symbols'].append(symbol)
                else:
                    results['failed'] += 1
                    logger.warning(f"No price data for {symbol}")

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results['failed'] += 1

        logger.info(f"Forex prices: {results['success']} success, {results['failed']} failed")
        return results

    def fetch_and_store_crypto_prices(self) -> dict:
        """Fetch and store all Crypto price data"""
        if not Settings.CRYPTO_ENABLED:
            return {'success': 0, 'failed': 0, 'symbols': []}

        results = {'success': 0, 'failed': 0, 'symbols': []}

        for symbol in Settings.CRYPTO_PAIRS:
            symbol = symbol.strip()
            try:
                price_data = self.mt5.fetch_crypto_data(
                    symbol,
                    Settings.CRYPTO_TIMEFRAME,
                    bars=200
                )

                if price_data:
                    inserted = self.db.store_price_data(price_data)
                    results['success'] += 1
                    results['symbols'].append(symbol)
                else:
                    results['failed'] += 1
                    logger.warning(f"No crypto data for {symbol}")

            except Exception as e:
                logger.error(f"Error processing crypto {symbol}: {e}")
                results['failed'] += 1

        logger.info(f"Crypto prices: {results['success']} success, {results['failed']} failed")
        return results

    def fetch_and_store_all_prices_parallel(self) -> dict:
        """Fetch and store all price data using parallel execution"""
        all_symbols = []

        # Prepare Forex symbols
        for symbol in Settings.FOREX_PAIRS:
            all_symbols.append({
                'symbol': symbol.strip(),
                'type': 'forex',
                'timeframe': Settings.FOREX_TIMEFRAME,
                'bars': 1000
            })

        # Prepare Crypto symbols
        if Settings.CRYPTO_ENABLED:
            for symbol in Settings.CRYPTO_PAIRS:
                all_symbols.append({
                    'symbol': symbol.strip(),
                    'type': 'crypto',
                    'timeframe': Settings.CRYPTO_TIMEFRAME,
                    'bars': 200
                })

        results = {
            'success': 0,
            'failed': 0,
            'forex_symbols': [],
            'crypto_symbols': []
        }

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=Settings.MAX_WORKERS) as executor:
            future_to_symbol = {
                executor.submit(self._fetch_and_store_single, item): item
                for item in all_symbols
            }

            for future in as_completed(future_to_symbol):
                item = future_to_symbol[future]
                try:
                    success = future.result()
                    if success:
                        results['success'] += 1
                        if item['type'] == 'forex':
                            results['forex_symbols'].append(item['symbol'])
                        else:
                            results['crypto_symbols'].append(item['symbol'])
                    else:
                        results['failed'] += 1
                except Exception as e:
                    logger.error(f"Error in parallel fetch for {item['symbol']}: {e}")
                    results['failed'] += 1

        logger.info(
            f"Parallel price fetch: {results['success']} success, {results['failed']} failed "
            f"(Forex: {len(results['forex_symbols'])}, Crypto: {len(results['crypto_symbols'])})"
        )
        return results

    def _fetch_and_store_single(self, item: dict) -> bool:
        """Fetch and store a single symbol (helper for parallel execution)"""
        try:
            if item['type'] == 'forex':
                price_data = self.mt5.fetch_price_data(
                    item['symbol'],
                    item['timeframe'],
                    bars=item['bars']
                )
            else:  # crypto
                price_data = self.mt5.fetch_crypto_data(
                    item['symbol'],
                    item['timeframe'],
                    bars=item['bars']
                )

            if price_data:
                self.db.store_price_data(price_data)
                return True
            else:
                logger.warning(f"No data for {item['symbol']}")
                return False

        except Exception as e:
            logger.error(f"Error fetching/storing {item['symbol']}: {e}")
            return False

    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for a symbol"""
        try:
            tick = self.mt5.get_symbol_info_tick(symbol)
            if tick:
                return tick.last
            return 0.0
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return 0.0
