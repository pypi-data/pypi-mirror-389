"""Distributed Computing Module

Provides distributed optimization capabilities across multiple workers/nodes:
- Multi-worker optimization with automatic load balancing
- Distributed JIT compilation
- Shared specialization cache across workers
- Distributed genetic algorithm evaluation
- Fault tolerance and checkpointing

Supported Backends:
- multiprocessing (default, local multi-core)
- Ray (recommended for multi-node)
- Dask (alternative distributed framework)
"""

import logging
from typing import Any, Dict

# Import core components first to satisfy import order
from python_optimizer.distributed.backend import (
    BackendType,
    DistributedBackend,
    get_backend,
    set_backend,
)
from python_optimizer.distributed.coordinator import DistributedCoordinator
from python_optimizer.distributed.decorator import distribute
from python_optimizer.distributed.genetic import (
    DistributedGeneticOptimizer,
    optimize_genetic_distributed,
)
from python_optimizer.distributed.jit_cache import (
    DistributedJITCache,
    clear_distributed_jit_cache,
    get_distributed_jit_cache,
)
from python_optimizer.distributed.spec_cache import (
    DistributedSpecializationCache,
    clear_distributed_spec_cache,
    get_distributed_spec_cache,
)
from python_optimizer.distributed.worker import DistributedWorker

logger = logging.getLogger(__name__)

# Check backend availability
RAY_AVAILABLE = False
DASK_AVAILABLE = False

try:
    import ray

    RAY_AVAILABLE = True
    RAY_VERSION = ray.__version__
except ImportError:
    RAY_VERSION = None

try:
    import dask
    import dask.distributed

    DASK_AVAILABLE = True
    DASK_VERSION = dask.__version__
except ImportError:
    DASK_VERSION = None

__all__ = [
    # Backend management
    "BackendType",
    "DistributedBackend",
    "get_backend",
    "set_backend",
    # Core components
    "DistributedCoordinator",
    "DistributedWorker",
    "distribute",
    # Distributed genetic algorithm
    "DistributedGeneticOptimizer",
    "optimize_genetic_distributed",
    # Distributed caches
    "DistributedJITCache",
    "get_distributed_jit_cache",
    "clear_distributed_jit_cache",
    "DistributedSpecializationCache",
    "get_distributed_spec_cache",
    "clear_distributed_spec_cache",
    # Backend availability
    "RAY_AVAILABLE",
    "DASK_AVAILABLE",
    "RAY_VERSION",
    "DASK_VERSION",
]


def check_backend_availability() -> Dict[str, Any]:
    """Check which distributed backends are available.

    Returns:
        Dictionary with backend availability information
    """
    return {
        "ray": {"available": RAY_AVAILABLE, "version": RAY_VERSION},
        "dask": {"available": DASK_AVAILABLE, "version": DASK_VERSION},
        "multiprocessing": {"available": True, "version": "builtin"},
    }
