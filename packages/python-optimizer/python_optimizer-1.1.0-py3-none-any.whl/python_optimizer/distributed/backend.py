"""Distributed Computing Backend Abstraction

Provides unified interface for different distributed computing backends:
- multiprocessing (local multi-core)
- Ray (multi-node, recommended)
- Dask (alternative distributed framework)
"""

import logging
import multiprocessing as mp
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Supported distributed computing backends."""

    MULTIPROCESSING = "multiprocessing"
    RAY = "ray"
    DASK = "dask"


class DistributedBackend(ABC):
    """Abstract base class for distributed computing backends."""

    @abstractmethod
    def initialize(self, **kwargs):
        """Initialize the backend with configuration."""
        pass

    @abstractmethod
    def shutdown(self):
        """Shutdown the backend and cleanup resources."""
        pass

    @abstractmethod
    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """Submit a task for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future/task handle
        """
        pass

    @abstractmethod
    def gather(self, futures: List[Any]) -> List[Any]:
        """Gather results from multiple futures.

        Args:
            futures: List of future/task handles

        Returns:
            List of results
        """
        pass

    @abstractmethod
    def map(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """Map function over list of items in parallel.

        Args:
            func: Function to apply
            items: List of items to process
            **kwargs: Additional arguments

        Returns:
            List of results
        """
        pass

    @abstractmethod
    def num_workers(self) -> int:
        """Get number of available workers."""
        pass


class MultiprocessingBackend(DistributedBackend):
    """Multiprocessing backend for local multi-core execution."""

    def __init__(self):
        self.pool: Optional[mp.Pool] = None
        self._num_workers = 0

    def initialize(self, num_workers: Optional[int] = None, **kwargs):
        """Initialize multiprocessing pool.

        Args:
            num_workers: Number of worker processes (default: CPU count)
            **kwargs: Additional arguments (ignored)
        """
        self._num_workers = num_workers or mp.cpu_count()
        self.pool = mp.Pool(processes=self._num_workers)
        logger.info(
            f"Initialized multiprocessing backend with {self._num_workers} workers"
        )

    def shutdown(self):
        """Shutdown multiprocessing pool."""
        if self.pool:
            self.pool.close()
            self.pool.join()
            self.pool = None
            logger.info("Shutdown multiprocessing backend")

    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """Submit task to pool."""
        if not self.pool:
            raise RuntimeError("Backend not initialized")
        return self.pool.apply_async(func, args, kwargs)

    def gather(self, futures: List[Any]) -> List[Any]:
        """Gather results from async results."""
        return [future.get() for future in futures]

    def map(self, func: Callable, items: List[Any], chunksize: int = 1) -> List[Any]:
        """Map function over items using pool.map."""
        if not self.pool:
            raise RuntimeError("Backend not initialized")
        return self.pool.map(func, items, chunksize=chunksize)

    def num_workers(self) -> int:
        """Get number of workers."""
        return self._num_workers


class RayBackend(DistributedBackend):
    """Ray backend for multi-node distributed execution."""

    def __init__(self):
        self._initialized = False
        self._num_workers = 0

    def initialize(
        self,
        address: Optional[str] = None,
        num_cpus: Optional[int] = None,
        **kwargs,
    ):
        """Initialize Ray cluster.

        Args:
            address: Ray cluster address (None for local)
            num_cpus: Number of CPUs to use
            **kwargs: Additional Ray init arguments
        """
        try:
            import ray
        except ImportError:
            raise RuntimeError("Ray is not installed. Install with: pip install ray")

        if not ray.is_initialized():
            ray.init(address=address, num_cpus=num_cpus, **kwargs)

        self._initialized = True
        self._num_workers = int(ray.available_resources().get("CPU", 0))
        logger.info(f"Initialized Ray backend with {self._num_workers} workers")

    def shutdown(self):
        """Shutdown Ray cluster."""
        try:
            import ray

            if ray.is_initialized():
                ray.shutdown()
                logger.info("Shutdown Ray backend")
        except ImportError:
            pass
        self._initialized = False

    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """Submit task to Ray."""
        import ray

        if not self._initialized:
            raise RuntimeError("Backend not initialized")

        # Convert function to Ray remote if not already
        if not hasattr(func, "remote"):
            func = ray.remote(func)

        return func.remote(*args, **kwargs)

    def gather(self, futures: List[Any]) -> List[Any]:
        """Gather results from Ray futures."""
        import ray

        return ray.get(futures)

    def map(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """Map function over items using Ray."""
        import ray

        if not self._initialized:
            raise RuntimeError("Backend not initialized")

        # Convert function to Ray remote if not already
        if not hasattr(func, "remote"):
            func = ray.remote(func)

        futures = [func.remote(item) for item in items]
        return ray.get(futures)

    def num_workers(self) -> int:
        """Get number of workers."""
        return self._num_workers


class DaskBackend(DistributedBackend):
    """Dask backend for distributed execution."""

    def __init__(self):
        self.client: Optional[Any] = None
        self._num_workers = 0

    def initialize(
        self, address: Optional[str] = None, n_workers: Optional[int] = None, **kwargs
    ):
        """Initialize Dask client.

        Args:
            address: Dask scheduler address (None for local cluster)
            n_workers: Number of workers for local cluster
            **kwargs: Additional Dask client arguments
        """
        try:
            from dask.distributed import Client, LocalCluster
        except ImportError:
            raise RuntimeError(
                "Dask is not installed. Install with: pip install dask distributed"
            )

        if address:
            self.client = Client(address, **kwargs)
        else:
            cluster = LocalCluster(n_workers=n_workers, **kwargs)
            self.client = Client(cluster)

        self._num_workers = len(self.client.scheduler_info()["workers"])
        logger.info(f"Initialized Dask backend with {self._num_workers} workers")

    def shutdown(self):
        """Shutdown Dask client."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Shutdown Dask backend")

    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """Submit task to Dask."""
        if not self.client:
            raise RuntimeError("Backend not initialized")
        return self.client.submit(func, *args, **kwargs)

    def gather(self, futures: List[Any]) -> List[Any]:
        """Gather results from Dask futures."""
        if not self.client:
            raise RuntimeError("Backend not initialized")
        return self.client.gather(futures)

    def map(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """Map function over items using Dask."""
        if not self.client:
            raise RuntimeError("Backend not initialized")
        futures = self.client.map(func, items, **kwargs)
        return self.client.gather(futures)

    def num_workers(self) -> int:
        """Get number of workers."""
        return self._num_workers


# Global backend instance
_current_backend: Optional[DistributedBackend] = None
_backend_type: BackendType = BackendType.MULTIPROCESSING


def get_backend() -> DistributedBackend:
    """Get current distributed backend.

    Returns:
        Current backend instance
    """
    if _current_backend is None:
        # Auto-initialize with default backend
        set_backend(BackendType.MULTIPROCESSING)
    return _current_backend


def set_backend(
    backend_type: BackendType,
    initialize: bool = True,
    **init_kwargs,
) -> DistributedBackend:
    """Set distributed computing backend.

    Args:
        backend_type: Type of backend to use
        initialize: Whether to initialize the backend
        **init_kwargs: Initialization arguments for backend

    Returns:
        Backend instance

    Example:
        # Use multiprocessing with 4 workers
        backend = set_backend(BackendType.MULTIPROCESSING, num_workers=4)

        # Use Ray cluster
        backend = set_backend(BackendType.RAY, address="ray://cluster:10001")
    """
    global _current_backend, _backend_type

    # Shutdown existing backend if any
    if _current_backend is not None:
        _current_backend.shutdown()

    # Create new backend
    if backend_type == BackendType.MULTIPROCESSING:
        _current_backend = MultiprocessingBackend()
    elif backend_type == BackendType.RAY:
        _current_backend = RayBackend()
    elif backend_type == BackendType.DASK:
        _current_backend = DaskBackend()
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    _backend_type = backend_type

    # Initialize if requested
    if initialize:
        _current_backend.initialize(**init_kwargs)

    return _current_backend
