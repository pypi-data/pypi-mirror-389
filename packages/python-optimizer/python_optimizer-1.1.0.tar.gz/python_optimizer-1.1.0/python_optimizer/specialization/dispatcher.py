"""
Runtime Specialization Dispatcher

This module implements runtime logic to select the best specialized version
of a function based on input types and performance characteristics.
"""

import inspect
import threading
import time
import types
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from .analyzer import TypeAnalyzer, TypePattern
from .cache import CacheEntry, SpecializationCache, get_global_cache
from .generators import SpecializationCodeGenerator


@dataclass
class DispatchResult:
    """Result of runtime dispatch decision."""

    selected_function: Callable
    selection_reason: str
    expected_gain: float = 0.0
    dispatch_time_us: float = 0.0
    is_specialized: bool = False
    specialization_key: str = ""

    def __post_init__(self):
        if self.is_specialized and not self.specialization_key:
            self.specialization_key = f"specialized_{id(self.selected_function)}"


class RuntimeDispatcher:
    """Manages runtime selection of specialized function versions."""

    def __init__(self, cache: Optional[SpecializationCache] = None):
        self.cache = cache or get_global_cache()
        self.type_analyzer = TypeAnalyzer()
        self.code_generator = SpecializationCodeGenerator()

        # Performance tracking
        self.dispatch_stats: Dict[str, List[float]] = defaultdict(list)
        self.selection_history: Dict[str, List[str]] = defaultdict(list)

        # Specialization thresholds
        self.min_calls_for_specialization = 5
        self.min_performance_gain = 0.2
        self.max_specializations_per_function = 10

        # Thread safety
        self._lock = threading.RLock()

    def dispatch(
        self, func: types.FunctionType, args: Tuple, kwargs: Dict[str, Any]
    ) -> DispatchResult:
        """Select the best function version for the given arguments."""
        start_time = time.perf_counter()

        func_name = func.__name__

        # Analyze argument types
        param_types = self._analyze_argument_types(func, args, kwargs)
        usage_patterns = self._get_usage_patterns(func_name, param_types)

        # Record this call for analysis
        self.type_analyzer.record_runtime_call(func_name, args, kwargs)

        # Check cache first
        cached_entry = self.cache.get(func_name, param_types, usage_patterns)
        if cached_entry:
            dispatch_time = (time.perf_counter() - start_time) * 1_000_000
            return DispatchResult(
                selected_function=cached_entry.specialized_func,
                selection_reason="cache_hit",
                expected_gain=cached_entry.performance_gain,
                dispatch_time_us=dispatch_time,
                is_specialized=True,
                specialization_key=cached_entry.cache_key,
            )

        # Check if we should create a specialization
        should_specialize, reason = self._should_specialize(func_name, param_types)

        if should_specialize:
            specialized_func = self._create_specialization(
                func, param_types, usage_patterns
            )
            if specialized_func:
                # Cache the new specialization
                entry = CacheEntry(
                    specialized_func=specialized_func,
                    param_name=list(param_types.keys())[0] if param_types else "",
                    param_type=list(param_types.values())[0] if param_types else object,
                    usage_pattern=usage_patterns,
                    performance_gain=getattr(
                        specialized_func, "__optimization_gain__", 0.3
                    ),
                    creation_time=time.time(),
                )

                self.cache.put(func_name, entry)

                dispatch_time = (time.perf_counter() - start_time) * 1_000_000
                return DispatchResult(
                    selected_function=specialized_func,
                    selection_reason=f"new_specialization_{reason}",
                    expected_gain=entry.performance_gain,
                    dispatch_time_us=dispatch_time,
                    is_specialized=True,
                    specialization_key=entry.cache_key,
                )

        # Use original function
        dispatch_time = (time.perf_counter() - start_time) * 1_000_000
        return DispatchResult(
            selected_function=func,
            selection_reason="original_function",
            dispatch_time_us=dispatch_time,
            is_specialized=False,
        )

    def _analyze_argument_types(
        self, func: types.FunctionType, args: Tuple, kwargs: Dict[str, Any]
    ) -> Dict[str, type]:
        """Analyze the types of function arguments."""
        param_types = {}

        try:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # Process positional arguments
            for i, arg in enumerate(args):
                if i < len(param_names):
                    param_types[param_names[i]] = type(arg)

            # Process keyword arguments
            for param_name, value in kwargs.items():
                param_types[param_name] = type(value)

        except Exception:
            # Fallback: generic parameter names
            for i, arg in enumerate(args):
                param_types[f"arg_{i}"] = type(arg)

        return param_types

    def _get_usage_patterns(
        self, func_name: str, param_types: Dict[str, type]
    ) -> Dict[str, Any]:
        """Get usage patterns for the function parameters."""
        patterns = {}

        # Simple heuristics based on types
        for param_name, param_type in param_types.items():
            if param_type in {int, float, complex}:
                patterns["is_numeric_heavy"] = True

            if param_type == np.ndarray:
                patterns["is_array_indexed"] = True
                patterns["is_numeric_heavy"] = True

            if param_type in {list, tuple, dict}:
                patterns["is_container"] = True

        return patterns

    def _should_specialize(
        self, func_name: str, param_types: Dict[str, type]
    ) -> Tuple[bool, str]:
        """Determine if we should create a specialization."""

        # Check call frequency
        if func_name in self.type_analyzer.runtime_types:
            call_data = self.type_analyzer.runtime_types[func_name]
            total_calls = sum(len(type_list) for type_list in call_data.values())

            if total_calls < self.min_calls_for_specialization:
                return False, "insufficient_calls"
        else:
            return False, "no_call_history"

        # Check if we already have too many specializations
        func_stats = self.cache.get_function_stats(func_name)
        if (
            func_stats.get("specializations", 0)
            >= self.max_specializations_per_function
        ):
            return False, "max_specializations_reached"

        # Check optimization potential
        for param_name, param_type in param_types.items():
            # High-value types
            if param_type in {int, float, np.ndarray}:
                return True, f"high_value_type_{param_type.__name__}"

            # Numeric operations on containers
            if param_type in {list, tuple} and self._has_numeric_pattern(func_name):
                return True, "numeric_container_operations"

        return False, "low_optimization_potential"

    def _has_numeric_pattern(self, func_name: str) -> bool:
        """Check if function has numeric operation patterns."""
        # This would analyze the function's call patterns
        # For now, simple heuristic
        return func_name.lower() in ["calculate", "compute", "process", "optimize"]

    def _create_specialization(
        self,
        func: types.FunctionType,
        param_types: Dict[str, type],
        usage_patterns: Dict[str, Any],
    ) -> Optional[Callable]:
        """Create a specialized version of the function."""

        if not param_types:
            return None

        # Try specializing for the most promising parameter
        best_specialization = None
        best_gain = 0.0

        for param_name, param_type in param_types.items():
            try:
                specialized_func = self.code_generator.generate_specialized_function(
                    func, param_name, param_type, usage_patterns
                )

                if specialized_func:
                    gain = getattr(specialized_func, "__optimization_gain__", 0.0)
                    if gain > best_gain:
                        best_gain = gain
                        best_specialization = specialized_func

            except Exception:
                continue  # Try next parameter

        if best_specialization and best_gain >= self.min_performance_gain:
            return best_specialization

        return None

    def get_dispatch_stats(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """Get dispatch performance statistics."""
        with self._lock:
            if func_name:
                return {
                    "function_name": func_name,
                    "dispatch_times": self.dispatch_stats.get(func_name, []),
                    "selection_history": self.selection_history.get(func_name, []),
                    "cache_stats": self.cache.get_function_stats(func_name),
                }
            else:
                # Global stats
                total_dispatches = sum(
                    len(times) for times in self.dispatch_stats.values()
                )
                avg_dispatch_time = 0.0
                if total_dispatches > 0:
                    all_times = [
                        time for times in self.dispatch_stats.values() for time in times
                    ]
                    avg_dispatch_time = sum(all_times) / len(all_times)

                return {
                    "total_dispatches": total_dispatches,
                    "functions_analyzed": len(self.dispatch_stats),
                    "avg_dispatch_time_us": avg_dispatch_time,
                    "cache_stats": self.cache.get_stats(),
                }

    def clear_stats(self):
        """Clear dispatch statistics."""
        with self._lock:
            self.dispatch_stats.clear()
            self.selection_history.clear()

    def configure(
        self,
        min_calls: Optional[int] = None,
        min_gain: Optional[float] = None,
        max_specializations: Optional[int] = None,
    ):
        """Configure dispatcher parameters."""
        if min_calls is not None:
            self.min_calls_for_specialization = min_calls
        if min_gain is not None:
            self.min_performance_gain = min_gain
        if max_specializations is not None:
            self.max_specializations_per_function = max_specializations


class AdaptiveDispatcher(RuntimeDispatcher):
    """Advanced dispatcher that adapts based on runtime performance feedback."""

    def __init__(self, cache: Optional[SpecializationCache] = None):
        super().__init__(cache)

        # Performance feedback tracking
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.specialization_effectiveness: Dict[str, float] = {}

        # Adaptive thresholds
        self.adaptive_min_gain = 0.2
        self.adaptation_window = 50  # Number of calls to consider for adaptation

    def record_performance(
        self,
        func_name: str,
        specialization_key: str,
        execution_time: float,
        is_specialized: bool,
    ):
        """Record actual performance for adaptive learning."""
        key = (
            f"{func_name}:{specialization_key}"
            if is_specialized
            else f"{func_name}:original"
        )
        self.performance_history[key].append(execution_time)

        # Keep only recent history
        if len(self.performance_history[key]) > self.adaptation_window:
            self.performance_history[key] = self.performance_history[key][
                -self.adaptation_window :
            ]

        # Update effectiveness scores
        self._update_effectiveness_scores(func_name)

    def _update_effectiveness_scores(self, func_name: str):
        """Update effectiveness scores based on performance history."""
        original_key = f"{func_name}:original"

        if original_key not in self.performance_history:
            return

        original_times = self.performance_history[original_key]
        if len(original_times) < 5:  # Need baseline data
            return

        baseline_avg = sum(original_times) / len(original_times)

        # Compare specialized versions
        for key, times in self.performance_history.items():
            if not key.startswith(f"{func_name}:") or key == original_key:
                continue

            if len(times) < 5:
                continue

            specialized_avg = sum(times) / len(times)

            # Calculate actual speedup (negative means slower)
            if specialized_avg > 0:
                actual_speedup = (baseline_avg - specialized_avg) / baseline_avg
                self.specialization_effectiveness[key] = actual_speedup
            else:
                self.specialization_effectiveness[key] = -1.0  # Mark as ineffective

    def _should_specialize(
        self, func_name: str, param_types: Dict[str, type]
    ) -> Tuple[bool, str]:
        """Enhanced specialization decision with adaptive learning."""

        # First, check base criteria
        should_spec, reason = super()._should_specialize(func_name, param_types)

        if not should_spec:
            return False, reason

        # Check if we have negative feedback for similar specializations
        for key, effectiveness in self.specialization_effectiveness.items():
            if key.startswith(f"{func_name}:") and effectiveness < -0.1:  # 10% slower
                # Be more conservative
                self.adaptive_min_gain = min(0.5, self.adaptive_min_gain + 0.1)
                return False, "negative_feedback"

        # Check if we have positive feedback - be more aggressive
        positive_feedback = any(
            eff > 0.2
            for key, eff in self.specialization_effectiveness.items()
            if key.startswith(f"{func_name}:")
        )

        if positive_feedback:
            self.adaptive_min_gain = max(0.1, self.adaptive_min_gain - 0.05)

        return True, f"adaptive_{reason}"

    def get_effectiveness_report(self) -> Dict[str, Any]:
        """Get report on specialization effectiveness."""
        return {
            "effectiveness_scores": dict(self.specialization_effectiveness),
            "adaptive_min_gain": self.adaptive_min_gain,
            "performance_history_size": {
                k: len(v) for k, v in self.performance_history.items()
            },
            "top_performers": sorted(
                [(k, v) for k, v in self.specialization_effectiveness.items() if v > 0],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }


# Global dispatcher instance
_global_dispatcher = None
_dispatcher_lock = threading.Lock()


def get_global_dispatcher() -> RuntimeDispatcher:
    """Get the global runtime dispatcher instance."""
    global _global_dispatcher
    with _dispatcher_lock:
        if _global_dispatcher is None:
            _global_dispatcher = AdaptiveDispatcher()
        return _global_dispatcher


def dispatch_function_call(
    func: types.FunctionType, args: Tuple, kwargs: Dict[str, Any]
) -> DispatchResult:
    """Dispatch a function call using the global dispatcher."""
    dispatcher = get_global_dispatcher()
    return dispatcher.dispatch(func, args, kwargs)
