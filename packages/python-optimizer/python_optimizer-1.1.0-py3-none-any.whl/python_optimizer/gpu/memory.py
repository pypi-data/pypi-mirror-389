"""GPU memory management and caching.

Provides memory pooling, allocation tracking, and automatic cache management
for GPU operations.
"""

import logging
import threading
import weakref
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None


@dataclass
class GPUMemoryInfo:
    """GPU memory information."""

    total: int  # Total GPU memory in bytes
    free: int  # Free GPU memory in bytes
    used: int  # Used GPU memory in bytes
    cached: int  # Cached GPU memory in bytes

    @property
    def total_gb(self) -> float:
        """Total memory in GB."""
        return self.total / (1024**3)

    @property
    def free_gb(self) -> float:
        """Free memory in GB."""
        return self.free / (1024**3)

    @property
    def used_gb(self) -> float:
        """Used memory in GB."""
        return self.used / (1024**3)

    @property
    def cached_gb(self) -> float:
        """Cached memory in GB."""
        return self.cached / (1024**3)

    @property
    def utilization_percent(self) -> float:
        """Memory utilization percentage."""
        if self.total == 0:
            return 0.0
        return (self.used / self.total) * 100


class GPUMemoryManager:
    """Manages GPU memory allocation and caching.

    Features:
    - Memory pool management
    - Allocation tracking
    - Automatic cache cleanup
    - Memory usage monitoring
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._allocations: Dict[int, weakref.ref] = {}
        self._allocation_sizes: Dict[int, int] = {}
        self._peak_memory = 0
        self._enable_pool = True

    def get_memory_info(
        self, device_id: Optional[int] = None
    ) -> Optional[GPUMemoryInfo]:
        """Get current GPU memory information.

        Args:
            device_id: GPU device ID. If None, uses current device.

        Returns:
            GPUMemoryInfo object or None if GPU not available.
        """
        if not CUPY_AVAILABLE:
            return None

        try:
            with cp.cuda.Device(device_id or 0):
                mempool = cp.get_default_memory_pool()
                free, total = cp.cuda.runtime.memGetInfo()

                used_bytes = mempool.used_bytes()
                cached_bytes = mempool.total_bytes() - used_bytes

                return GPUMemoryInfo(
                    total=total, free=free, used=total - free, cached=cached_bytes
                )
        except Exception as e:
            logger.error(f"Failed to get GPU memory info: {e}")
            return None

    def clear_cache(self, device_id: Optional[int] = None):
        """Clear GPU memory cache.

        Args:
            device_id: GPU device ID. If None, uses current device.
        """
        if not CUPY_AVAILABLE:
            return

        try:
            with cp.cuda.Device(device_id or 0):
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.info(f"Cleared GPU memory cache for device {device_id or 0}")
        except Exception as e:
            logger.error(f"Failed to clear GPU cache: {e}")

    def allocate(self, size: int, device_id: Optional[int] = None):
        """Allocate GPU memory.

        Args:
            size: Size in bytes to allocate.
            device_id: GPU device ID. If None, uses current device.

        Returns:
            CuPy array or None if allocation failed.
        """
        if not CUPY_AVAILABLE:
            return None

        try:
            with cp.cuda.Device(device_id or 0):
                # Allocate using CuPy's memory pool
                arr = cp.empty(size, dtype=cp.uint8)

                # Track allocation
                with self._lock:
                    arr_id = id(arr)
                    self._allocations[arr_id] = weakref.ref(
                        arr, self._cleanup_callback(arr_id)
                    )
                    self._allocation_sizes[arr_id] = size

                    # Update peak memory
                    current = sum(self._allocation_sizes.values())
                    if current > self._peak_memory:
                        self._peak_memory = current

                return arr
        except Exception as e:
            logger.error(f"Failed to allocate GPU memory: {e}")
            return None

    def _cleanup_callback(self, arr_id: int):
        """Callback for cleaning up deallocated arrays."""

        def callback(ref):
            with self._lock:
                if arr_id in self._allocation_sizes:
                    del self._allocation_sizes[arr_id]
                if arr_id in self._allocations:
                    del self._allocations[arr_id]

        return callback

    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics.

        Returns:
            Dictionary with allocation statistics.
        """
        with self._lock:
            return {
                "active_allocations": len(self._allocations),
                "total_allocated_bytes": sum(self._allocation_sizes.values()),
                "peak_memory_bytes": self._peak_memory,
                "pool_enabled": self._enable_pool,
            }

    def enable_memory_pool(self, enable: bool = True):
        """Enable or disable memory pooling.

        Args:
            enable: True to enable pooling, False to disable.
        """
        self._enable_pool = enable
        if CUPY_AVAILABLE:
            if enable:
                cp.cuda.set_allocator(cp.cuda.MemoryPool().malloc)
                logger.info("Enabled GPU memory pooling")
            else:
                cp.cuda.set_allocator(None)
                logger.info("Disabled GPU memory pooling")

    def set_memory_limit(self, limit_bytes: int, device_id: Optional[int] = None):
        """Set memory limit for GPU device.

        Args:
            limit_bytes: Maximum memory to use in bytes.
            device_id: GPU device ID. If None, uses current device.
        """
        if not CUPY_AVAILABLE:
            return

        try:
            with cp.cuda.Device(device_id or 0):
                mempool = cp.get_default_memory_pool()
                mempool.set_limit(size=limit_bytes)
                logger.info(f"Set GPU memory limit to {limit_bytes / (1024**3):.2f} GB")
        except Exception as e:
            logger.error(f"Failed to set memory limit: {e}")

    def compact(self, device_id: Optional[int] = None):
        """Compact GPU memory by freeing unused blocks.

        Args:
            device_id: GPU device ID. If None, uses current device.
        """
        if not CUPY_AVAILABLE:
            return

        try:
            with cp.cuda.Device(device_id or 0):
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.debug("Compacted GPU memory")
        except Exception as e:
            logger.error(f"Failed to compact GPU memory: {e}")


# Global memory manager instance
_memory_manager = GPUMemoryManager()


# Public API
def get_gpu_memory_info(device_id: Optional[int] = None) -> Optional[GPUMemoryInfo]:
    """Get GPU memory information.

    Args:
        device_id: GPU device ID. If None, uses current device.

    Returns:
        GPUMemoryInfo object or None if GPU not available.

    Example:
        info = get_gpu_memory_info()
        if info:
            print(f"GPU Memory: {info.used_gb:.1f}/{info.total_gb:.1f} GB")
            print(f"Utilization: {info.utilization_percent:.1f}%")
    """
    return _memory_manager.get_memory_info(device_id)


def clear_gpu_cache(device_id: Optional[int] = None):
    """Clear GPU memory cache.

    Args:
        device_id: GPU device ID. If None, uses current device.

    Example:
        clear_gpu_cache()  # Free up unused GPU memory
    """
    _memory_manager.clear_cache(device_id)


def enable_gpu_memory_pool(enable: bool = True):
    """Enable or disable GPU memory pooling.

    Args:
        enable: True to enable pooling (faster allocation), False to disable.

    Example:
        enable_gpu_memory_pool(True)  # Use memory pooling for better performance
    """
    _memory_manager.enable_memory_pool(enable)


def set_gpu_memory_limit(limit_gb: float, device_id: Optional[int] = None):
    """Set GPU memory usage limit.

    Args:
        limit_gb: Maximum memory to use in gigabytes.
        device_id: GPU device ID. If None, uses current device.

    Example:
        set_gpu_memory_limit(4.0)  # Limit GPU memory to 4 GB
    """
    limit_bytes = int(limit_gb * (1024**3))
    _memory_manager.set_memory_limit(limit_bytes, device_id)


def get_gpu_memory_stats() -> Dict[str, Any]:
    """Get GPU memory manager statistics.

    Returns:
        Dictionary with allocation statistics.

    Example:
        stats = get_gpu_memory_stats()
        print(f"Active allocations: {stats['active_allocations']}")
        print(f"Peak memory: {stats['peak_memory_bytes'] / (1024**3):.2f} GB")
    """
    return _memory_manager.get_stats()
