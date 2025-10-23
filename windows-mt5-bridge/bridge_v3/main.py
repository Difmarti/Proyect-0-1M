#!/usr/bin/env python3
"""
MT5 Windows Bridge V3 - Modular Architecture with Parallel Execution
Main orchestrator that coordinates all services, controllers, and workers
"""

import signal
import sys
from datetime import datetime

# Initialize logging first
from bridge_v3.services import LoggerService
LoggerService.setup()
logger = LoggerService.get_logger(__name__)

# Import configuration
from bridge_v3.config import Settings

# Import services
from bridge_v3.services import MT5Service, DatabaseService, RedisService

# Import controllers
from bridge_v3.controllers import (
    PriceController,
    TradeController,
    RiskController,
    StrategyController,
    ExecutionController  # ← Controller for automatic trade execution
)

# Import workers
from bridge_v3.workers import TaskWorker, Task, TaskScheduler
from bridge_v3.config.constants import TaskPriority


class MT5BridgeV3:
    """
    Main orchestrator for MT5 Bridge V3
    Manages all services, controllers, and parallel workers
    """

    def __init__(self):
        # Services
        self.mt5 = MT5Service()
        self.db = DatabaseService()
        self.redis = RedisService()

        # Controllers
        self.price_ctrl = None
        self.trade_ctrl = None
        self.risk_ctrl = None
        self.strategy_ctrl = None
        self.execution_ctrl = None  # ← Controller for executing trades automatically

        # Workers
        self.worker = TaskWorker(max_workers=Settings.MAX_WORKERS)
        self.scheduler = TaskScheduler()

        # State
        self.running = False

    def initialize(self) -> bool:
        """Initialize all services and controllers"""
        logger.info("=" * 70)
        logger.info("MT5 Bridge V3 - Initializing".center(70))
        logger.info("=" * 70)

        # Validate configuration
        try:
            Settings.validate()
            logger.info("Configuration validated")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return False

        # Display configuration
        logger.info(Settings.display_config())

        # Initialize MT5
        if not self.mt5.initialize():
            logger.error("Failed to initialize MT5")
            return False

        # Initialize Database
        if not self.db.connect():
            logger.error("Failed to connect to database")
            self.mt5.shutdown()
            return False

        # Initialize Redis
        if not self.redis.connect():
            logger.error("Failed to connect to Redis")
            self.db.close()
            self.mt5.shutdown()
            return False

        # Initialize controllers
        self.price_ctrl = PriceController(self.mt5, self.db)
        self.trade_ctrl = TradeController(self.mt5, self.db, self.redis)
        self.risk_ctrl = RiskController(self.mt5, self.redis)
        self.strategy_ctrl = StrategyController(self.mt5, self.db)
        self.execution_ctrl = ExecutionController(self.mt5)

        # Initialize risk manager
        self.risk_ctrl.initialize()

        # ═══════════════════════════════════════════════════════════════════
        # ⚠️ AUTOMATIC TRADE EXECUTION CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════
        #
        # ENABLE AUTOMATIC TRADING: Uncomment the line below to allow the bot
        # to open positions automatically based on detected signals.
        #
        # ⚠️ WARNING: Only enable this after:
        #    1. Testing extensively on a DEMO account
        #    2. Validating your strategy with backtesting
        #    3. Configuring risk limits properly in .env
        #    4. Understanding all risks involved
        #
        # TO ENABLE: Remove the '#' from the line below
        # TO DISABLE: Add '#' at the start of the line below
        #
        self.execution_ctrl.enable_execution()  # ← AUTOMATIC TRADING ENABLED
        #
        # If you want SAFETY MODE (signals logged but NOT executed):
        # Comment the line above by adding '#' at the start:
        # # self.execution_ctrl.enable_execution()  # ← AUTOMATIC TRADING DISABLED
        #
        # ═══════════════════════════════════════════════════════════════════

        logger.info("=" * 70)
        logger.info("Initialization Complete".center(70))
        logger.info("=" * 70)

        return True

    def setup_scheduler(self):
        """Setup scheduled tasks"""
        logger.info("Setting up scheduled tasks...")

        # Price fetching (parallel execution)
        self.scheduler.add_job(
            self.job_fetch_prices,
            interval=Settings.PRICE_FETCH_INTERVAL,
            unit='seconds',
            name='fetch_prices'
        )

        # Account metrics sync
        self.scheduler.add_job(
            self.job_sync_metrics,
            interval=Settings.METRICS_SYNC_INTERVAL,
            unit='seconds',
            name='sync_metrics'
        )

        # Active trades sync
        self.scheduler.add_job(
            self.job_sync_trades,
            interval=Settings.TRADES_SYNC_INTERVAL,
            unit='seconds',
            name='sync_trades'
        )

        # Crypto analysis (if enabled)
        if Settings.CRYPTO_ENABLED:
            self.scheduler.add_job(
                self.job_analyze_crypto,
                interval=Settings.CRYPTO_ANALYSIS_INTERVAL,
                unit='seconds',
                name='analyze_crypto'
            )

        # Risk metrics update
        self.scheduler.add_job(
            self.job_update_risk,
            interval=60,
            unit='seconds',
            name='update_risk'
        )

        logger.info("Scheduled tasks configured:")
        for job in self.scheduler.get_jobs_info():
            logger.info(f"  - {job['name']}: Every {job['interval']} {job['unit']}")

    def job_fetch_prices(self):
        """Job: Fetch all price data (parallel execution)"""
        logger.info("Running job: Fetch prices (parallel)")

        task = Task(
            name='fetch_prices_parallel',
            function=self.price_ctrl.fetch_and_store_all_prices_parallel,
            priority=TaskPriority.NORMAL
        )

        self.worker.submit_task(task)

    def job_sync_metrics(self):
        """Job: Sync account metrics"""
        logger.info("Running job: Sync account metrics")

        def sync_metrics():
            account_info = self.mt5.get_account_info()
            positions = self.mt5.get_positions()

            from bridge_v3.models import AccountMetrics

            metrics = AccountMetrics(
                timestamp=datetime.now(),
                balance=account_info.balance,
                equity=account_info.equity,
                margin=account_info.margin,
                free_margin=account_info.margin_free,
                profit=account_info.profit,
                open_positions=len(positions),
                leverage=account_info.leverage
            )

            # Store in database
            self.db.store_account_metrics(metrics)

            # Cache in Redis
            self.redis.cache_account_metrics(metrics.to_dict())

        task = Task(
            name='sync_metrics',
            function=sync_metrics,
            priority=TaskPriority.HIGH
        )

        self.worker.submit_task(task)

    def job_sync_trades(self):
        """Job: Sync active trades"""
        logger.info("Running job: Sync active trades")

        task = Task(
            name='sync_trades',
            function=self.trade_ctrl.sync_active_trades,
            priority=TaskPriority.HIGH
        )

        self.worker.submit_task(task)

    def job_analyze_crypto(self):
        """Job: Analyze crypto signals and execute trades"""
        logger.info("Running job: Analyze crypto signals")

        def analyze_and_execute():
            """
            Analyzes crypto signals and executes trades automatically

            This function will:
            1. Analyze market data for all crypto pairs
            2. Detect trading signals (LONG/SHORT)
            3. Validate risk limits
            4. Execute trades if conditions are met

            To DISABLE automatic execution:
            - Comment out the execution_ctrl lines below
            - Keep only the log_signal() call
            """
            signals = self.strategy_ctrl.analyze_crypto_signals()

            for signal in signals:
                # Check if can trade (risk validation)
                can_trade, reason = self.risk_ctrl.can_open_position('crypto')

                if can_trade:
                    # Always log the signal for monitoring
                    self.strategy_ctrl.log_signal(signal)

                    # ═══════════════════════════════════════════════════════
                    # ⚠️ AUTOMATIC TRADE EXECUTION
                    # ═══════════════════════════════════════════════════════
                    #
                    # The code below will execute trades automatically.
                    #
                    # TO DISABLE automatic trading:
                    # Comment out the if/else block below (add # at start)
                    #
                    # TO ENABLE automatic trading:
                    # Keep the code uncommented (remove # if present)
                    #
                    if self.execution_ctrl.execution_enabled:
                        # Execute the trade
                        result = self.execution_ctrl.execute_signal(
                            signal,
                            risk_pct=2.0  # ← Risk 2% per trade (configurable)
                        )

                        if result['success']:
                            logger.info(
                                f"✅ Trade OPENED successfully: "
                                f"Ticket {result['ticket']}, "
                                f"{signal.symbol} {signal.signal_type.value}, "
                                f"Volume {result['volume']:.2f}"
                            )

                            # Sync trades immediately after opening
                            self.trade_ctrl.sync_active_trades()
                        else:
                            logger.error(
                                f"❌ Trade FAILED for {signal.symbol}: "
                                f"{result['reason']}"
                            )
                    else:
                        logger.info(
                            f"ℹ️ Signal detected but NOT executed (execution disabled): "
                            f"{signal.symbol} {signal.signal_type.value}"
                        )
                    # ═══════════════════════════════════════════════════════

                else:
                    logger.warning(
                        f"⚠️ Cannot trade {signal.symbol}: {reason}"
                    )

        task = Task(
            name='analyze_crypto',
            function=analyze_and_execute,  # ← Updated function name
            priority=TaskPriority.NORMAL
        )

        self.worker.submit_task(task)

    def job_update_risk(self):
        """Job: Update risk metrics"""
        logger.info("Running job: Update risk metrics")

        task = Task(
            name='update_risk',
            function=self.risk_ctrl.update_cache,
            priority=TaskPriority.CRITICAL
        )

        self.worker.submit_task(task)

    def initial_sync(self):
        """Perform initial data synchronization"""
        logger.info("=" * 70)
        logger.info("Performing Initial Sync".center(70))
        logger.info("=" * 70)

        # Create high-priority tasks for initial sync
        tasks = [
            Task('initial_price_fetch', self.price_ctrl.fetch_and_store_all_prices_parallel, TaskPriority.HIGH),
            Task('initial_metrics', self.job_sync_metrics, TaskPriority.HIGH),
            Task('initial_trades', self.job_sync_trades, TaskPriority.HIGH),
        ]

        # Submit all tasks
        futures = [self.worker.submit_task(task) for task in tasks]

        # Wait for completion
        for future in futures:
            try:
                future.result(timeout=Settings.WORKER_TIMEOUT)
            except Exception as e:
                logger.error(f"Initial sync task failed: {e}")

        logger.info("Initial sync completed")

    def run(self):
        """Main execution loop"""
        # Initialize
        if not self.initialize():
            logger.error("Initialization failed. Exiting.")
            return

        # Perform initial sync
        self.initial_sync()

        # Setup and start scheduler
        self.setup_scheduler()
        self.scheduler.start()

        # Start task worker queue processor
        self.worker.start_queue_processor()

        # Display runtime info
        logger.info("=" * 70)
        logger.info("MT5 Bridge V3 Running!".center(70))
        logger.info("=" * 70)
        logger.info(f"Parallel Workers: {Settings.MAX_WORKERS}")
        logger.info(f"Forex Pairs: {len(Settings.FOREX_PAIRS)}")

        if Settings.CRYPTO_ENABLED:
            logger.info(f"Crypto Pairs: {len(Settings.CRYPTO_PAIRS)}")

            # ═══════════════════════════════════════════════════════════════
            # Display execution mode (CRITICAL INFORMATION)
            # ═══════════════════════════════════════════════════════════════
            if self.execution_ctrl and self.execution_ctrl.execution_enabled:
                logger.warning("=" * 70)
                logger.warning("⚠️  AUTOMATIC TRADING MODE ENABLED  ⚠️".center(70))
                logger.warning("=" * 70)
                logger.warning("The bot WILL open positions automatically!")
                logger.warning("Trades will be executed based on detected signals")
                logger.warning(f"Risk per trade: 2.0%")
                logger.warning(f"Max daily loss: {Settings.MAX_DAILY_LOSS_PCT}%")
                logger.warning(f"Max positions: {Settings.MAX_SIMULTANEOUS_TRADES}")
                logger.warning("")
                logger.warning("To DISABLE automatic trading:")
                logger.warning("1. Stop the bot (Ctrl+C)")
                logger.warning("2. Edit bridge_v3/main.py")
                logger.warning("3. Comment line 123: # self.execution_ctrl.enable_execution()")
                logger.warning("4. Restart the bot")
                logger.warning("=" * 70)
            else:
                logger.info("Mode: SAFETY MODE (signals logged, NOT executed)")
                logger.info("Automatic trading is DISABLED")

        logger.info("=" * 70)

        # Main loop
        self.running = True
        try:
            while self.running:
                # Display stats periodically
                import time
                time.sleep(60)

                stats = self.worker.get_stats()
                logger.info(
                    f"Worker Stats - Active: {stats['active_tasks']}, "
                    f"Queued: {stats['queued_tasks']}, "
                    f"Completed: {stats['completed_tasks']}, "
                    f"Failed: {stats['failed_tasks']}"
                )

        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("=" * 70)
        logger.info("Shutting Down MT5 Bridge V3".center(70))
        logger.info("=" * 70)

        self.running = False

        # Stop scheduler
        self.scheduler.stop()

        # Wait for active tasks
        logger.info("Waiting for active tasks to complete...")
        self.worker.wait_for_all()

        # Shutdown worker
        self.worker.shutdown(wait=True)

        # Close connections
        if self.mt5:
            self.mt5.shutdown()
        if self.db:
            self.db.close()
        if self.redis:
            self.redis.close()

        logger.info("Shutdown complete. Goodbye!")


def signal_handler(sig, frame):
    """Handle system signals"""
    logger.info(f"Received signal {sig}")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run bridge
    bridge = MT5BridgeV3()
    bridge.run()
