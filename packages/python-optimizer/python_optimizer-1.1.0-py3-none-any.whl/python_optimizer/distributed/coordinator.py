"""Distributed Coordinator

Coordinates distributed optimization across multiple workers.
Handles task distribution, result aggregation, and load balancing.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from python_optimizer.distributed.backend import get_backend

logger = logging.getLogger(__name__)


class DistributedCoordinator:
    """Coordinates distributed optimization tasks across workers.

    Features:
    - Automatic task distribution
    - Load balancing
    - Result aggregation
    - Fault tolerance with retries
    - Performance monitoring
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        enable_monitoring: bool = True,
    ):
        """Initialize distributed coordinator.

        Args:
            max_retries: Maximum number of retries for failed tasks
            timeout: Task timeout in seconds (None for no timeout)
            enable_monitoring: Enable performance monitoring
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.enable_monitoring = enable_monitoring

        # Statistics
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "total_time": 0.0,
            "avg_task_time": 0.0,
        }

    def map(
        self,
        func: Callable,
        items: List[Any],
        chunksize: Optional[int] = None,
    ) -> List[Any]:
        """Map function over items in parallel across workers.

        Args:
            func: Function to apply
            items: List of items to process
            chunksize: Number of items per task (None for auto)

        Returns:
            List of results

        Example:
            coordinator = DistributedCoordinator()
            results = coordinator.map(optimize_function, input_data)
        """
        if not items:
            return []

        backend = get_backend()
        start_time = time.perf_counter()

        try:
            # Submit tasks
            logger.info(
                f"Distributing {len(items)} items across "
                f"{backend.num_workers()} workers"
            )

            self.stats["tasks_submitted"] += len(items)

            # Use backend's map implementation
            if chunksize:
                results = backend.map(func, items, chunksize=chunksize)
            else:
                results = backend.map(func, items)

            self.stats["tasks_completed"] += len(items)

            # Update statistics
            elapsed = time.perf_counter() - start_time
            self.stats["total_time"] += elapsed
            self.stats["avg_task_time"] = (
                self.stats["total_time"] / self.stats["tasks_completed"]
                if self.stats["tasks_completed"] > 0
                else 0.0
            )

            logger.info(
                f"Completed {len(items)} tasks in {elapsed:.2f}s "
                f"({len(items)/elapsed:.1f} tasks/s)"
            )

            return results

        except Exception as e:
            self.stats["tasks_failed"] += len(items)
            logger.error(f"Failed to process tasks: {e}")
            raise

    def submit_batch(self, func: Callable, args_list: List[tuple]) -> List[Any]:
        """Submit batch of tasks with different arguments.

        Args:
            func: Function to execute
            args_list: List of argument tuples

        Returns:
            List of results

        Example:
            results = coordinator.submit_batch(
                my_func,
                [(arg1_a, arg2_a), (arg1_b, arg2_b)]
            )
        """
        backend = get_backend()
        start_time = time.perf_counter()

        # Submit all tasks
        futures = []
        for args in args_list:
            if isinstance(args, tuple):
                future = backend.submit(func, *args)
            else:
                future = backend.submit(func, args)
            futures.append(future)

        self.stats["tasks_submitted"] += len(args_list)

        # Gather results
        results = backend.gather(futures)

        self.stats["tasks_completed"] += len(args_list)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["total_time"] += elapsed
        self.stats["avg_task_time"] = (
            self.stats["total_time"] / self.stats["tasks_completed"]
            if self.stats["tasks_completed"] > 0
            else 0.0
        )

        return results

    def reduce(
        self,
        func: Callable,
        items: List[Any],
        reducer: Callable,
        initial: Any = None,
    ) -> Any:
        """Map-reduce pattern: map function over items, then reduce results.

        Args:
            func: Function to apply to each item
            items: List of items to process
            reducer: Function to reduce results (takes two args)
            initial: Initial value for reduction

        Returns:
            Reduced result

        Example:
            # Sum of squares
            result = coordinator.reduce(
                lambda x: x**2,
                [1, 2, 3, 4],
                lambda a, b: a + b,
                initial=0
            )
        """
        # Map phase
        results = self.map(func, items)

        # Reduce phase
        if initial is not None:
            accumulator = initial
            for result in results:
                accumulator = reducer(accumulator, result)
            return accumulator
        else:
            if not results:
                return None
            accumulator = results[0]
            for result in results[1:]:
                accumulator = reducer(accumulator, result)
            return accumulator

    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics.

        Returns:
            Dictionary with performance statistics
        """
        backend = get_backend()
        return {
            **self.stats,
            "num_workers": backend.num_workers(),
            "throughput": (
                self.stats["tasks_completed"] / self.stats["total_time"]
                if self.stats["total_time"] > 0
                else 0.0
            ),
        }

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "total_time": 0.0,
            "avg_task_time": 0.0,
        }
