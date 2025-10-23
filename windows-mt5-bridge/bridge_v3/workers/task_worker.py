"""
Task worker for parallel execution with priority queue
"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from queue import PriorityQueue, Empty
import threading

from bridge_v3.config import Settings
from bridge_v3.config.constants import TaskPriority
from bridge_v3.services.logger_service import LoggerService


logger = LoggerService.get_logger(__name__)


@dataclass
class Task:
    """Represents a task to be executed"""
    name: str
    function: Callable
    priority: TaskPriority = TaskPriority.NORMAL
    args: tuple = ()
    kwargs: dict = None
    created_at: datetime = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now()

    def __lt__(self, other):
        """Compare by priority for priority queue"""
        return self.priority.value < other.priority.value

    def execute(self) -> Any:
        """Execute the task"""
        try:
            logger.info(f"Executing task: {self.name} (priority: {self.priority.name})")
            start_time = datetime.now()

            result = self.function(*self.args, **self.kwargs)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Task completed: {self.name} (duration: {duration:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"Task failed: {self.name} - {e}")
            import traceback
            traceback.print_exc()
            return None


class TaskWorker:
    """Worker pool for parallel task execution"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or Settings.MAX_WORKERS
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.task_queue = PriorityQueue()
        self.running = False
        self.worker_thread = None
        self.active_tasks = {}
        self.completed_tasks = []
        self.failed_tasks = []
        self.lock = threading.Lock()

        logger.info(f"TaskWorker initialized with {self.max_workers} workers")

    def submit_task(self, task: Task) -> Future:
        """Submit a task for execution (returns Future immediately)"""
        future = self.executor.submit(task.execute)

        with self.lock:
            self.active_tasks[task.name] = {
                'task': task,
                'future': future,
                'submitted_at': datetime.now()
            }

        return future

    def submit_task_to_queue(self, task: Task):
        """Add task to priority queue for sequential execution"""
        self.task_queue.put(task)
        logger.debug(f"Task queued: {task.name} (priority: {task.priority.name})")

    def process_queue(self):
        """Process tasks from queue (run in separate thread)"""
        self.running = True

        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)

                # Submit to executor
                future = self.submit_task(task)

                # Wait for completion
                try:
                    result = future.result(timeout=Settings.WORKER_TIMEOUT)
                    with self.lock:
                        self.completed_tasks.append({
                            'name': task.name,
                            'completed_at': datetime.now(),
                            'result': result
                        })
                except Exception as e:
                    logger.error(f"Task timeout or error: {task.name} - {e}")
                    with self.lock:
                        self.failed_tasks.append({
                            'name': task.name,
                            'failed_at': datetime.now(),
                            'error': str(e)
                        })

                # Mark task as done
                self.task_queue.task_done()

                # Remove from active tasks
                with self.lock:
                    if task.name in self.active_tasks:
                        del self.active_tasks[task.name]

            except Empty:
                # No tasks in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing queue: {e}")

    def start_queue_processor(self):
        """Start background thread to process queue"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self.process_queue, daemon=True)
            self.worker_thread.start()
            logger.info("Queue processor started")

    def stop_queue_processor(self):
        """Stop background queue processor"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Queue processor stopped")

    def wait_for_all(self):
        """Wait for all queued tasks to complete"""
        self.task_queue.join()
        logger.info("All queued tasks completed")

    def get_active_count(self) -> int:
        """Get number of active tasks"""
        with self.lock:
            return len(self.active_tasks)

    def get_completed_count(self) -> int:
        """Get number of completed tasks"""
        with self.lock:
            return len(self.completed_tasks)

    def get_failed_count(self) -> int:
        """Get number of failed tasks"""
        with self.lock:
            return len(self.failed_tasks)

    def get_stats(self) -> dict:
        """Get worker statistics"""
        with self.lock:
            return {
                'max_workers': self.max_workers,
                'active_tasks': len(self.active_tasks),
                'queued_tasks': self.task_queue.qsize(),
                'completed_tasks': len(self.completed_tasks),
                'failed_tasks': len(self.failed_tasks),
                'queue_processor_running': self.running
            }

    def shutdown(self, wait: bool = True):
        """Shutdown the worker pool"""
        self.stop_queue_processor()
        self.executor.shutdown(wait=wait)
        logger.info("TaskWorker shutdown complete")
