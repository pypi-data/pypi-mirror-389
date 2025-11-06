"""
Core optimization engine that coordinates different optimization techniques.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from numba import njit

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

    # Fallback decorator that does nothing
    def njit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


class OptimizationEngine:
    """
    Central optimization engine that manages JIT compilation, specialization,
    and profiling for Python functions.
    """

    def __init__(self):
        self.optimization_level = 1
        self.profiling_enabled = False
        self.cache = {}
        self.stats = {
            "optimized_functions": 0,
            "jit_compilations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_optimization_time": 0.0,
        }

    def optimize_function(self, func: Callable, config: Dict[str, Any]) -> Callable:
        """
        Apply optimizations to a function based on configuration.

        Args:
            func: Function to optimize
            config: Optimization configuration dictionary

        Returns:
            Optimized function
        """
        start_time = time.perf_counter()

        # Check cache first
        func_id = id(func)
        if func_id in self.cache:
            self.stats["cache_hits"] += 1
            logger.debug(f"Using cached optimization for {func.__name__}")
            return self.cache[func_id]

        self.stats["cache_misses"] += 1

        # Apply JIT compilation if requested and available
        optimized_func = func
        if config.get("jit", False) and NUMBA_AVAILABLE:
            optimized_func = self._apply_jit_optimization(optimized_func, config)

        # Apply profiling wrapper if requested
        if config.get("profile", False) or self.profiling_enabled:
            optimized_func = self._apply_profiling_wrapper(
                optimized_func, func.__name__
            )

        # Cache the result
        if config.get("cache", True):
            self.cache[func_id] = optimized_func

        # Update stats
        self.stats["optimized_functions"] += 1
        self.stats["total_optimization_time"] += time.perf_counter() - start_time

        logger.info(f"Optimized function {func.__name__} successfully")
        return optimized_func

    def _apply_jit_optimization(
        self, func: Callable, config: Dict[str, Any]
    ) -> Callable:
        """Apply JIT compilation to a function."""
        try:
            jit_config = {
                "cache": config.get("cache", True),
                "nogil": config.get("nogil", False),
                "fastmath": config.get("fastmath", True),
                "parallel": config.get("parallel", False),
            }

            # Remove parallel if not supported
            if not config.get("parallel", False):
                jit_config.pop("parallel", None)

            optimized_func = njit(**jit_config)(func)
            self.stats["jit_compilations"] += 1

            logger.debug(f"Applied JIT compilation to {func.__name__}")
            return optimized_func

        except Exception as e:
            logger.warning(f"JIT compilation failed for {func.__name__}: {e}")
            logger.warning("Falling back to original function")
            return func

    def _apply_profiling_wrapper(self, func: Callable, func_name: str) -> Callable:
        """Add profiling wrapper to a function."""

        @functools.wraps(func)
        def profiled_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                # Store profiling data
                if not hasattr(profiled_wrapper, "_profile_data"):
                    profiled_wrapper._profile_data = {
                        "call_count": 0,
                        "total_time": 0.0,
                        "avg_time": 0.0,
                        "min_time": float("inf"),
                        "max_time": 0.0,
                    }

                profile_data = profiled_wrapper._profile_data
                profile_data["call_count"] += 1
                profile_data["total_time"] += execution_time
                profile_data["avg_time"] = (
                    profile_data["total_time"] / profile_data["call_count"]
                )
                profile_data["min_time"] = min(profile_data["min_time"], execution_time)
                profile_data["max_time"] = max(profile_data["max_time"], execution_time)

                logger.debug(f"{func_name} executed in {execution_time:.6f}s")
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.error(f"{func_name} failed after {execution_time:.6f}s: {e}")
                raise

        return profiled_wrapper

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization engine statistics."""
        return self.stats.copy()

    def clear_cache(self) -> None:
        """Clear the optimization cache."""
        self.cache.clear()
        logger.info("Optimization cache cleared")

    def set_optimization_level(self, level: int) -> None:
        """Set the optimization level (0-3)."""
        if not 0 <= level <= 3:
            raise ValueError("Optimization level must be between 0 and 3")
        self.optimization_level = level
        logger.info(f"Optimization level set to {level}")

    def enable_profiling(self) -> None:
        """Enable global profiling."""
        self.profiling_enabled = True
        logger.info("Global profiling enabled")

    def disable_profiling(self) -> None:
        """Disable global profiling."""
        self.profiling_enabled = False
        logger.info("Global profiling disabled")
