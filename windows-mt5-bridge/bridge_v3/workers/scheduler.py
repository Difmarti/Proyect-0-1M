"""
Task scheduler with cron-like functionality
"""

import schedule
import time
from typing import Callable
from datetime import datetime
import threading

from bridge_v3.services.logger_service import LoggerService


logger = LoggerService.get_logger(__name__)


class TaskScheduler:
    """Scheduler for periodic tasks"""

    def __init__(self):
        self.jobs = []
        self.running = False
        self.scheduler_thread = None

    def add_job(
        self,
        func: Callable,
        interval: int,
        unit: str = 'seconds',
        name: str = None
    ):
        """Add a scheduled job"""
        job_name = name or func.__name__

        if unit == 'seconds':
            job = schedule.every(interval).seconds.do(func)
        elif unit == 'minutes':
            job = schedule.every(interval).minutes.do(func)
        elif unit == 'hours':
            job = schedule.every(interval).hours.do(func)
        else:
            raise ValueError(f"Invalid unit: {unit}")

        self.jobs.append({
            'name': job_name,
            'job': job,
            'interval': interval,
            'unit': unit,
            'function': func
        })

        logger.info(f"Scheduled job: {job_name} - every {interval} {unit}")

    def run_pending(self):
        """Run all pending jobs"""
        schedule.run_pending()

    def start(self):
        """Start scheduler in background thread"""
        if self.scheduler_thread is None or not self.scheduler_thread.is_alive():
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.scheduler_thread.start()
            logger.info("Scheduler started")

    def _run_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def clear_jobs(self):
        """Clear all scheduled jobs"""
        schedule.clear()
        self.jobs = []
        logger.info("All scheduled jobs cleared")

    def get_jobs_info(self) -> list:
        """Get information about scheduled jobs"""
        return [
            {
                'name': job['name'],
                'interval': job['interval'],
                'unit': job['unit'],
                'next_run': job['job'].next_run.isoformat() if job['job'].next_run else None
            }
            for job in self.jobs
        ]
