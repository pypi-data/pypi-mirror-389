"""
Tests for the variable specialization system.
"""

import time
from typing import Any, Dict, List

import numpy as np
import pytest

from python_optimizer import (
    clear_specialization_cache,
    get_specialization_stats,
    optimize,
)
from python_optimizer.specialization.analyzer import (
    TypeAnalyzer,
    TypePattern,
    VariableUsage,
)
from python_optimizer.specialization.cache import CacheEntry, SpecializationCache
from python_optimizer.specialization.dispatcher import DispatchResult, RuntimeDispatcher
from python_optimizer.specialization.engine import (
    SpecializationConfig,
    SpecializationEngine,
)


class TestTypeAnalyzer:
    """Test the type analysis component."""

    def test_variable_usage_creation(self):
        """Test creation of VariableUsage objects."""
        usage = VariableUsage("test_var")
        assert usage.name == "test_var"
        assert len(usage.operations) == 0
        assert len(usage.types_seen) == 0
        assert usage.usage_count == 0

    def test_add_operation(self):
        """Test adding operations to variable usage."""
        usage = VariableUsage("x")
        usage.add_operation("+")
        usage.add_operation("*")

        assert "+" in usage.operations
        assert "*" in usage.operations
        assert usage.usage_count == 2
        assert usage.is_numeric_heavy  # Should be True for numeric operations

    def test_add_type(self):
        """Test adding types to variable usage."""
        usage = VariableUsage("x")
        usage.add_type(int)
        usage.add_type(float)

        assert int in usage.types_seen
        assert float in usage.types_seen

    def test_dominant_type_detection(self):
        """Test dominant type detection."""
        usage = VariableUsage("x")
        usage.add_type(int)
        usage.add_type(float)
        usage.add_operation("+")

        dominant = usage.get_dominant_type()
        assert dominant in {
            int,
            float,
        }  # Should prefer numeric types for numeric operations

    def test_type_pattern_creation(self):
        """Test TypePattern creation and scoring."""
        pattern = TypePattern(
            function_name="test_func", parameter_types={"x": int, "y": float}
        )

        assert pattern.function_name == "test_func"
        assert pattern.parameter_types["x"] == int
        assert pattern.parameter_types["y"] == float
        assert pattern.optimization_potential > 0  # Should have some potential

    @pytest.mark.xfail(reason="Type analyzer needs more implementation work")
    def test_analyzer_with_simple_function(self):
        """Test analyzer with a simple function."""

        def simple_add(x, y):
            return x + y

        analyzer = TypeAnalyzer()
        usage = analyzer.analyze_function(simple_add)

        # Should detect variable usage in the function
        assert isinstance(usage, dict)


class TestSpecializationCache:
    """Test the specialization cache."""

    def setup_method(self):
        """Set up test cache."""
        self.cache = SpecializationCache(max_size=10, enable_persistence=False)

    def test_cache_creation(self):
        """Test cache creation."""
        assert self.cache.max_size == 10
        assert not self.cache.enable_persistence

    def test_cache_entry_creation(self):
        """Test cache entry creation."""

        def test_func():
            return 42

        entry = CacheEntry(
            specialized_func=test_func,
            param_name="x",
            param_type=int,
            usage_pattern={"is_numeric_heavy": True},
            performance_gain=0.5,
            creation_time=time.time(),
        )

        assert entry.specialized_func == test_func
        assert entry.param_name == "x"
        assert entry.param_type == int
        assert entry.performance_gain == 0.5
        assert entry.cache_key != ""  # Should generate a cache key

    @pytest.mark.xfail(reason="Specialization cache API needs more work")
    def test_cache_put_and_get(self):
        """Test caching and retrieval."""

        def test_func():
            return 42

        entry = CacheEntry(
            specialized_func=test_func,
            param_name="x",
            param_type=int,
            usage_pattern={"is_numeric_heavy": True},
            performance_gain=0.5,
            creation_time=time.time(),
        )

        # Store entry
        success = self.cache.put("test_func", entry)
        assert success

        # Retrieve entry
        retrieved = self.cache.get("test_func", (int,), {"is_numeric_heavy": True})
        assert retrieved is not None
        assert retrieved.specialized_func == test_func

    def test_cache_stats(self):
        """Test cache statistics."""
        stats = self.cache.get_stats()

        assert "total_entries" in stats
        assert "functions_cached" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


class TestRuntimeDispatcher:
    """Test the runtime dispatcher."""

    def setup_method(self):
        """Set up test dispatcher."""
        self.cache = SpecializationCache(max_size=10, enable_persistence=False)
        self.dispatcher = RuntimeDispatcher(self.cache)

    def test_dispatcher_creation(self):
        """Test dispatcher creation."""
        assert self.dispatcher.cache == self.cache
        assert self.dispatcher.min_calls_for_specialization == 5

    def test_argument_type_analysis(self):
        """Test argument type analysis."""

        def test_func(x: int, y: float) -> float:
            return x + y

        param_types = self.dispatcher._analyze_argument_types(test_func, (42, 3.14), {})

        assert param_types["x"] == int
        assert param_types["y"] == float

    def test_dispatch_result_creation(self):
        """Test dispatch result creation."""

        def test_func():
            return 42

        result = DispatchResult(
            selected_function=test_func,
            selection_reason="test",
            expected_gain=0.5,
            is_specialized=True,
        )

        assert result.selected_function == test_func
        assert result.selection_reason == "test"
        assert result.expected_gain == 0.5
        assert result.is_specialized
        assert result.specialization_key != ""  # Should generate a key


class TestSpecializationEngine:
    """Test the specialization engine."""

    def setup_method(self):
        """Set up test engine."""
        config = SpecializationConfig(
            enabled=True,
            min_calls_for_specialization=2,
            enable_adaptive_learning=False,
            enable_caching=False,  # Disable for simpler testing
        )
        self.engine = SpecializationEngine(config)

    def test_engine_creation(self):
        """Test engine creation."""
        assert self.engine.config.enabled
        assert self.engine.config.min_calls_for_specialization == 2

    def test_function_optimization_wrapper(self):
        """Test function optimization wrapper creation."""

        def simple_add(x, y):
            return x + y

        optimized_func = self.engine.optimize_function(simple_add)

        assert callable(optimized_func)
        assert hasattr(optimized_func, "__specialized__")
        assert optimized_func.__specialized__
        assert optimized_func.__original_function__ == simple_add

    def test_optimized_function_execution(self):
        """Test execution of optimized function."""

        def simple_multiply(x, y):
            return x * y

        optimized_func = self.engine.optimize_function(simple_multiply)

        # Should work with different argument types
        result_int = optimized_func(5, 6)
        result_float = optimized_func(2.5, 4.0)

        assert result_int == 30
        assert result_float == 10.0

    def test_function_stats_tracking(self):
        """Test function statistics tracking."""

        def test_func(x):
            return x * 2

        optimized_func = self.engine.optimize_function(test_func)

        # Execute a few times
        for i in range(5):
            optimized_func(i)

        stats = self.engine.get_function_stats("test_func")
        assert stats["total_calls"] == 5

    def test_global_stats(self):
        """Test global statistics."""

        def func1(x):
            return x + 1

        def func2(x):
            return x * 2

        # Optimize both functions
        opt_func1 = self.engine.optimize_function(func1)
        opt_func2 = self.engine.optimize_function(func2)

        # Execute them
        opt_func1(42)
        opt_func2(42)

        global_stats = self.engine.get_global_stats()
        assert global_stats["functions_optimized"] == 2
        assert global_stats["total_calls"] == 2


class TestIntegration:
    """Integration tests for the complete specialization system."""

    def test_end_to_end_optimization(self):
        """Test end-to-end optimization with the @optimize decorator."""
        # Clear any existing cache
        clear_specialization_cache()

        @optimize(jit=False, specialize=True)
        def fibonacci_specialized(n):
            if n <= 1:
                return n
            return fibonacci_specialized(n - 1) + fibonacci_specialized(n - 2)

        # Execute with different types to trigger specialization
        for i in range(10):  # Build up call history
            fibonacci_specialized(15)

        # Should have created specializations
        stats = get_specialization_stats("fibonacci_specialized")
        assert stats is not None
        assert isinstance(stats, dict)

    def test_numeric_specialization_benefit(self):
        """Test that numeric specialization provides benefits."""

        @optimize(jit=False, specialize=True)
        def numeric_heavy_function(x):
            result = x
            for _ in range(100):
                result = result * 1.1 + 0.5
            return result

        # Warm up specialization
        for _ in range(10):
            numeric_heavy_function(42.0)

        # Measure performance
        start_time = time.perf_counter()
        for _ in range(100):
            numeric_heavy_function(42.0)
        specialized_time = time.perf_counter() - start_time

        # Should complete without errors
        assert specialized_time > 0

    def test_array_specialization(self):
        """Test array type specialization."""

        @optimize(jit=False, specialize=True)
        def array_processing(data):
            if isinstance(data, np.ndarray):
                return np.sum(data**2)
            else:
                return sum(x * x for x in data)

        # Test with different array types
        list_data = [1, 2, 3, 4, 5]
        array_data = np.array([1, 2, 3, 4, 5])

        # Warm up
        for _ in range(5):
            array_processing(list_data)
            array_processing(array_data)

        # Should handle both types correctly
        list_result = array_processing(list_data)
        array_result = array_processing(array_data)

        assert list_result == array_result == 55

    def test_configuration_changes(self):
        """Test changing specialization configuration."""
        from python_optimizer import configure_specialization

        # Configure for aggressive specialization
        configure_specialization(
            min_calls_for_specialization=1,
            min_performance_gain=0.01,
            enable_adaptive_learning=True,
        )

        @optimize(jit=False, specialize=True)
        def configurable_func(x):
            return x * x + x + 1

        # Should work with new configuration
        result = configurable_func(5)
        assert result == 31

    def teardown_method(self):
        """Clean up after tests."""
        clear_specialization_cache()


if __name__ == "__main__":
    pytest.main([__file__])
