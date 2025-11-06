"""GPU dispatcher for intelligent CPU/GPU routing.

Automatically selects CPU or GPU based on data size, availability,
and performance characteristics.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

from python_optimizer.gpu.device import is_gpu_available


class GPUDispatcher:
    """Dispatches computations between CPU and GPU.

    Features:
    - Automatic GPU/CPU selection based on data size
    - Configurable size thresholds
    - Performance tracking and adaptation
    - Seamless numpy/cupy interoperability
    """

    def __init__(
        self,
        min_size_threshold: int = 10000,
        max_size_threshold: Optional[int] = None,
        force_gpu: bool = False,
        force_cpu: bool = False,
    ):
        """Initialize GPU dispatcher.

        Args:
            min_size_threshold: Minimum data size to use GPU (in elements).
            max_size_threshold: Maximum data size for GPU (None = no limit).
            force_gpu: Force GPU execution even if not optimal.
            force_cpu: Force CPU execution (disables GPU).
        """
        self.min_size_threshold = min_size_threshold
        self.max_size_threshold = max_size_threshold
        self.force_gpu = force_gpu
        self.force_cpu = force_cpu
        self._gpu_available = is_gpu_available() if not force_cpu else False

        # Performance tracking
        self._gpu_calls = 0
        self._cpu_calls = 0
        self._gpu_fallbacks = 0

    def should_use_gpu(self, *args, **kwargs) -> bool:
        """Determine if GPU should be used for given inputs.

        Args:
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            True if GPU should be used, False for CPU.
        """
        # Check if GPU is forced/disabled
        if self.force_cpu:
            return False
        if self.force_gpu:
            return self._gpu_available

        # Check GPU availability
        if not self._gpu_available:
            return False

        # Analyze input sizes
        total_size = 0
        for arg in args:
            if isinstance(arg, (np.ndarray, list, tuple)):
                if isinstance(arg, np.ndarray):
                    total_size += arg.size
                else:
                    total_size += len(arg)

        for value in kwargs.values():
            if isinstance(value, (np.ndarray, list, tuple)):
                if isinstance(value, np.ndarray):
                    total_size += value.size
                else:
                    total_size += len(value)

        # Check thresholds
        if total_size < self.min_size_threshold:
            return False

        if self.max_size_threshold and total_size > self.max_size_threshold:
            return False

        return True

    def to_gpu(self, data: Any) -> Any:
        """Transfer data to GPU.

        Args:
            data: Data to transfer (numpy array, list, tuple, or scalar).

        Returns:
            CuPy array or original data if not array-like.
        """
        if not CUPY_AVAILABLE:
            return data

        if isinstance(data, np.ndarray):
            return cp.asarray(data)
        elif isinstance(data, (list, tuple)):
            return cp.asarray(data)
        elif isinstance(data, cp.ndarray):
            return data  # Already on GPU
        else:
            return data  # Scalar or unsupported type

    def to_cpu(self, data: Any) -> Any:
        """Transfer data to CPU.

        Args:
            data: Data to transfer (CuPy array or other).

        Returns:
            Numpy array or original data.
        """
        if CUPY_AVAILABLE and isinstance(data, cp.ndarray):
            return cp.asnumpy(data)
        return data

    def dispatch(
        self, cpu_func: Callable, gpu_func: Optional[Callable], *args, **kwargs
    ) -> Any:
        """Dispatch function to CPU or GPU.

        Args:
            cpu_func: CPU implementation of function.
            gpu_func: GPU implementation of function (None = use cpu_func).
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            Function result (on CPU).
        """
        use_gpu = self.should_use_gpu(*args, **kwargs)

        if use_gpu and gpu_func is not None:
            try:
                # Transfer data to GPU
                gpu_args = [self.to_gpu(arg) for arg in args]
                gpu_kwargs = {k: self.to_gpu(v) for k, v in kwargs.items()}

                # Execute on GPU
                result = gpu_func(*gpu_args, **gpu_kwargs)

                # Transfer result back to CPU
                result = self.to_cpu(result)

                self._gpu_calls += 1
                return result

            except Exception as e:
                logger.warning(f"GPU execution failed, falling back to CPU: {e}")
                self._gpu_fallbacks += 1
                use_gpu = False

        # Execute on CPU
        self._cpu_calls += 1
        return cpu_func(*args, **kwargs)

    def wrap(
        self, cpu_func: Optional[Callable] = None, gpu_func: Optional[Callable] = None
    ):
        """Decorator to wrap a function with GPU dispatching.

        Args:
            cpu_func: CPU implementation (if None, uses decorated function).
            gpu_func: GPU implementation (if None, attempts to use cpu_func on GPU).

        Returns:
            Wrapped function with automatic dispatching.

        Example:
            dispatcher = GPUDispatcher()

            @dispatcher.wrap()
            def my_function(x):
                return x ** 2
        """

        def decorator(func):
            nonlocal cpu_func

            if cpu_func is None:
                cpu_func = func

            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.dispatch(cpu_func, gpu_func, *args, **kwargs)

            return wrapper

        # Handle both @wrap and @wrap() syntax
        if cpu_func is not None and callable(cpu_func) and gpu_func is None:
            # @wrap without parentheses
            func = cpu_func
            cpu_func = None
            return decorator(func)
        else:
            # @wrap() with parentheses
            return decorator

    def get_stats(self) -> dict:
        """Get dispatcher statistics.

        Returns:
            Dictionary with usage statistics.
        """
        total_calls = self._gpu_calls + self._cpu_calls
        gpu_percent = (self._gpu_calls / total_calls * 100) if total_calls > 0 else 0

        return {
            "gpu_available": self._gpu_available,
            "total_calls": total_calls,
            "gpu_calls": self._gpu_calls,
            "cpu_calls": self._cpu_calls,
            "gpu_fallbacks": self._gpu_fallbacks,
            "gpu_usage_percent": round(gpu_percent, 1),
            "force_gpu": self.force_gpu,
            "force_cpu": self.force_cpu,
            "min_size_threshold": self.min_size_threshold,
        }

    def reset_stats(self):
        """Reset dispatcher statistics."""
        self._gpu_calls = 0
        self._cpu_calls = 0
        self._gpu_fallbacks = 0


# Convenience function for quick GPU dispatching
def dispatch_to_gpu(
    func: Callable,
    *args,
    min_size: int = 10000,
    force_gpu: bool = False,
    **kwargs,
) -> Any:
    """Quick dispatch a function to GPU if beneficial.

    Args:
        func: Function to execute.
        *args: Function arguments.
        min_size: Minimum data size to use GPU.
        force_gpu: Force GPU execution.
        **kwargs: Function keyword arguments.

    Returns:
        Function result.

    Example:
        result = dispatch_to_gpu(np.sum, large_array)
    """
    dispatcher = GPUDispatcher(min_size_threshold=min_size, force_gpu=force_gpu)
    return dispatcher.dispatch(func, None, *args, **kwargs)
