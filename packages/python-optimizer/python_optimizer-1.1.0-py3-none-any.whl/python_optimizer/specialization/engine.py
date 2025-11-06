"""
Specialization Engine

This module coordinates all specialization components and integrates with
the existing @optimize decorator system.
"""

import functools
import time
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .analyzer import TypeAnalyzer
from .cache import SpecializationCache, get_global_cache
from .dispatcher import AdaptiveDispatcher, DispatchResult, RuntimeDispatcher
from .generators import SpecializationCodeGenerator


@dataclass
class SpecializationConfig:
    """Configuration for specialization behavior."""

    enabled: bool = True
    min_calls_for_specialization: int = 5
    min_performance_gain: float = 0.2
    max_specializations_per_function: int = 10
    enable_adaptive_learning: bool = True
    enable_caching: bool = True
    cache_persistence: bool = True
    analysis_mode: str = "auto"  # "auto", "eager", "lazy"

    def __post_init__(self):
        if self.analysis_mode not in {"auto", "eager", "lazy"}:
            self.analysis_mode = "auto"


class SpecializationEngine:
    """Main engine that coordinates variable specialization."""

    def __init__(self, config: Optional[SpecializationConfig] = None):
        self.config = config or SpecializationConfig()

        # Core components
        self.analyzer = TypeAnalyzer()
        self.generator = SpecializationCodeGenerator()
        self.cache = get_global_cache() if self.config.enable_caching else None

        # Dispatcher selection
        if self.config.enable_adaptive_learning:
            self.dispatcher = AdaptiveDispatcher(self.cache)
        else:
            self.dispatcher = RuntimeDispatcher(self.cache)

        # Configure dispatcher
        self.dispatcher.configure(
            min_calls=self.config.min_calls_for_specialization,
            min_gain=self.config.min_performance_gain,
            max_specializations=self.config.max_specializations_per_function,
        )

        # Performance tracking
        self.optimization_stats: Dict[str, Dict[str, Any]] = {}
        self.enabled_functions: Dict[str, bool] = {}

    def optimize_function(self, func: types.FunctionType) -> Callable:
        """Create an optimized wrapper for a function with specialization."""
        if not self.config.enabled:
            return func

        func_name = func.__name__
        self.enabled_functions[func_name] = True

        # Initialize stats
        self.optimization_stats[func_name] = {
            "total_calls": 0,
            "specialized_calls": 0,
            "cache_hits": 0,
            "avg_dispatch_time_us": 0.0,
            "specializations_created": 0,
            "performance_history": [],
        }

        # Analyze function if in eager mode
        if self.config.analysis_mode == "eager":
            self._analyze_function_eagerly(func)

        @functools.wraps(func)
        def specialized_wrapper(*args, **kwargs):
            return self._execute_with_specialization(func, args, kwargs)

        # Attach metadata
        specialized_wrapper.__specialized__ = True
        specialized_wrapper.__original_function__ = func
        specialized_wrapper.__specialization_engine__ = self

        return specialized_wrapper

    def _execute_with_specialization(
        self, func: types.FunctionType, args: Tuple, kwargs: Dict[str, Any]
    ) -> Any:
        """Execute function with specialization logic."""
        func_name = func.__name__
        stats = self.optimization_stats[func_name]
        stats["total_calls"] += 1

        execution_start = time.perf_counter()

        try:
            # Dispatch to best version
            dispatch_result = self.dispatcher.dispatch(func, args, kwargs)

            # Update stats
            stats["avg_dispatch_time_us"] = (
                stats["avg_dispatch_time_us"] * (stats["total_calls"] - 1)
                + dispatch_result.dispatch_time_us
            ) / stats["total_calls"]

            if dispatch_result.is_specialized:
                stats["specialized_calls"] += 1
                if dispatch_result.selection_reason == "cache_hit":
                    stats["cache_hits"] += 1
                elif "new_specialization" in dispatch_result.selection_reason:
                    stats["specializations_created"] += 1

            # Execute the selected function
            result = dispatch_result.selected_function(*args, **kwargs)

            # Record performance if using adaptive dispatcher
            if isinstance(self.dispatcher, AdaptiveDispatcher):
                execution_time = time.perf_counter() - execution_start
                self.dispatcher.record_performance(
                    func_name,
                    dispatch_result.specialization_key,
                    execution_time,
                    dispatch_result.is_specialized,
                )
                stats["performance_history"].append(execution_time)

                # Keep only recent history
                if len(stats["performance_history"]) > 100:
                    stats["performance_history"] = stats["performance_history"][-100:]

            return result

        except Exception as e:
            # Fallback to original function on error
            return func(*args, **kwargs)

    def _analyze_function_eagerly(self, func: types.FunctionType):
        """Analyze function immediately for specialization opportunities."""
        try:
            variable_usage = self.analyzer.analyze_function(func)

            # Pre-generate some common specializations if patterns are clear
            if variable_usage:
                func_name = func.__name__

                # Look for high-value parameters
                for var_name, usage in variable_usage.items():
                    if usage.is_numeric_heavy and usage.usage_count > 10:
                        # Pre-generate numeric specializations
                        for param_type in [int, float]:
                            if param_type in usage.types_seen:
                                try:
                                    specialized_func = (
                                        self.generator.generate_specialized_function(
                                            func,
                                            var_name,
                                            param_type,
                                            {
                                                "is_numeric_heavy": True,
                                                "usage_count": usage.usage_count,
                                            },
                                        )
                                    )

                                    if specialized_func and self.cache:
                                        from .cache import CacheEntry

                                        entry = CacheEntry(
                                            specialized_func=specialized_func,
                                            param_name=var_name,
                                            param_type=param_type,
                                            usage_pattern={"is_numeric_heavy": True},
                                            performance_gain=getattr(
                                                specialized_func,
                                                "__optimization_gain__",
                                                0.3,
                                            ),
                                            creation_time=time.time(),
                                        )
                                        self.cache.put(func_name, entry)

                                except Exception:
                                    continue  # Skip failed specializations

        except Exception:
            pass  # Don't fail if analysis fails

    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific function."""
        if func_name not in self.optimization_stats:
            return {}

        stats = self.optimization_stats[func_name].copy()

        # Add cache stats
        if self.cache:
            cache_stats = self.cache.get_function_stats(func_name)
            stats.update(cache_stats)

        # Add dispatch stats
        dispatch_stats = self.dispatcher.get_dispatch_stats(func_name)
        stats.update(dispatch_stats)

        # Calculate derived metrics
        if stats["total_calls"] > 0:
            stats["specialization_rate"] = (
                stats["specialized_calls"] / stats["total_calls"]
            )
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / stats["specialized_calls"]
                if stats["specialized_calls"] > 0
                else 0
            )
        else:
            stats["specialization_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0

        # Performance summary
        if stats["performance_history"]:
            perf_hist = stats["performance_history"]
            stats["avg_execution_time"] = sum(perf_hist) / len(perf_hist)
            stats["min_execution_time"] = min(perf_hist)
            stats["max_execution_time"] = max(perf_hist)

        return stats

    def get_global_stats(self) -> Dict[str, Any]:
        """Get overall specialization statistics."""
        total_calls = sum(
            stats["total_calls"] for stats in self.optimization_stats.values()
        )
        total_specialized = sum(
            stats["specialized_calls"] for stats in self.optimization_stats.values()
        )
        total_cache_hits = sum(
            stats["cache_hits"] for stats in self.optimization_stats.values()
        )

        global_stats = {
            "functions_optimized": len(self.optimization_stats),
            "total_calls": total_calls,
            "total_specialized_calls": total_specialized,
            "total_cache_hits": total_cache_hits,
            "global_specialization_rate": (
                total_specialized / total_calls if total_calls > 0 else 0
            ),
            "global_cache_hit_rate": (
                total_cache_hits / total_specialized if total_specialized > 0 else 0
            ),
            "config": {
                "enabled": self.config.enabled,
                "min_calls": self.config.min_calls_for_specialization,
                "min_gain": self.config.min_performance_gain,
                "adaptive_learning": self.config.enable_adaptive_learning,
                "caching_enabled": self.config.enable_caching,
            },
        }

        # Add cache stats if available
        if self.cache:
            cache_stats = self.cache.get_stats()
            global_stats["cache_stats"] = cache_stats

        # Add dispatcher stats
        dispatcher_stats = self.dispatcher.get_dispatch_stats()
        global_stats["dispatcher_stats"] = dispatcher_stats

        # Add effectiveness report if using adaptive dispatcher
        if isinstance(self.dispatcher, AdaptiveDispatcher):
            effectiveness = self.dispatcher.get_effectiveness_report()
            global_stats["effectiveness_report"] = effectiveness

        return global_stats

    def clear_function_cache(self, func_name: str):
        """Clear cache for a specific function."""
        if self.cache:
            self.cache.invalidate_function(func_name)

        # Clear analysis data
        self.analyzer.clear_function_data(func_name)

        # Reset stats
        if func_name in self.optimization_stats:
            self.optimization_stats[func_name] = {
                "total_calls": 0,
                "specialized_calls": 0,
                "cache_hits": 0,
                "avg_dispatch_time_us": 0.0,
                "specializations_created": 0,
                "performance_history": [],
            }

    def disable_function(self, func_name: str):
        """Disable specialization for a specific function."""
        self.enabled_functions[func_name] = False
        self.clear_function_cache(func_name)

    def enable_function(self, func_name: str):
        """Re-enable specialization for a specific function."""
        self.enabled_functions[func_name] = True

    def reconfigure(self, config: SpecializationConfig):
        """Update configuration."""
        self.config = config

        # Reconfigure dispatcher
        self.dispatcher.configure(
            min_calls=config.min_calls_for_specialization,
            min_gain=config.min_performance_gain,
            max_specializations=config.max_specializations_per_function,
        )

        # Switch dispatcher type if needed
        if config.enable_adaptive_learning and not isinstance(
            self.dispatcher, AdaptiveDispatcher
        ):
            self.dispatcher = AdaptiveDispatcher(self.cache)
            self.dispatcher.configure(
                min_calls=config.min_calls_for_specialization,
                min_gain=config.min_performance_gain,
                max_specializations=config.max_specializations_per_function,
            )
        elif not config.enable_adaptive_learning and isinstance(
            self.dispatcher, AdaptiveDispatcher
        ):
            self.dispatcher = RuntimeDispatcher(self.cache)
            self.dispatcher.configure(
                min_calls=config.min_calls_for_specialization,
                min_gain=config.min_performance_gain,
                max_specializations=config.max_specializations_per_function,
            )


# Global engine instance
_global_engine = None
_engine_lock = None


def get_global_engine() -> SpecializationEngine:
    """Get the global specialization engine."""
    global _global_engine, _engine_lock

    if _engine_lock is None:
        import threading

        _engine_lock = threading.Lock()

    with _engine_lock:
        if _global_engine is None:
            _global_engine = SpecializationEngine()
        return _global_engine


def configure_specialization(config: SpecializationConfig):
    """Configure the global specialization engine."""
    engine = get_global_engine()
    engine.reconfigure(config)


def get_specialization_stats(func_name: Optional[str] = None) -> Dict[str, Any]:
    """Get specialization statistics."""
    engine = get_global_engine()
    if func_name:
        return engine.get_function_stats(func_name)
    else:
        return engine.get_global_stats()


def clear_specialization_cache(func_name: Optional[str] = None):
    """Clear specialization cache."""
    engine = get_global_engine()
    if func_name:
        engine.clear_function_cache(func_name)
    elif engine.cache:
        engine.cache.clear()
