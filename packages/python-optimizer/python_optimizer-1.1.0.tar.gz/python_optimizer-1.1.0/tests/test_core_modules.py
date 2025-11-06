"""
Comprehensive tests for core modules (decorator.py and engine.py).
"""

import numpy as np
import pytest

from python_optimizer import optimize
from python_optimizer.core.decorator import (
    clear_optimization_cache,
    clear_specialization_cache,
    configure_specialization,
    disable_profiling,
    enable_profiling,
    get_optimization_stats,
    get_specialization_stats,
    set_optimization_level,
)
from python_optimizer.core.engine import OptimizationEngine


class TestOptimizeDecorator:
    """Test the @optimize decorator."""

    def test_optimize_without_parameters(self):
        """Test @optimize without any parameters."""

        @optimize
        def simple_add(x, y):
            return x + y

        result = simple_add(3, 4)
        assert result == 7
        assert hasattr(simple_add, "_optimization_config")
        assert simple_add._has_jit is True

    def test_optimize_with_jit_disabled(self):
        """Test optimize with JIT disabled."""

        @optimize(jit=False, specialize=False, profile=False)
        def no_jit_func(x):
            return x * 2

        result = no_jit_func(5)
        assert result == 10
        assert hasattr(no_jit_func, "_optimization_config")
        assert no_jit_func._optimization_config["jit"] is False

    def test_optimize_with_specialization(self):
        """Test optimize with specialization enabled."""

        @optimize(jit=False, specialize=True)
        def specialized_func(x):
            return x + 1

        # Call multiple times to trigger specialization
        for i in range(10):
            result = specialized_func(i)
            assert result == i + 1

        assert specialized_func._has_specialization is True

    def test_optimize_with_profiling(self):
        """Test optimize with profiling enabled."""

        @optimize(jit=False, profile=True)
        def profiled_func(x):
            return x**2

        result = profiled_func(4)
        assert result == 16

    def test_optimize_with_all_flags(self):
        """Test optimize with all optimization flags enabled."""

        @optimize(
            jit=True,
            specialize=True,
            profile=True,
            aggressiveness=3,
            cache=True,
            parallel=False,
            nogil=False,
            fastmath=True,
        )
        def full_optimization(x):
            total = 0
            for i in range(x):
                total += i
            return total

        result = full_optimization(10)
        expected = sum(range(10))
        assert result == expected

    def test_optimize_aggressiveness_levels(self):
        """Test different aggressiveness levels."""
        for level in [0, 1, 2, 3]:

            @optimize(jit=True, aggressiveness=level)
            def func(x):
                return x + 1

            result = func(5)
            assert result == 6

    def test_optimize_with_cache_disabled(self):
        """Test optimize with caching disabled."""

        @optimize(jit=True, cache=False)
        def uncached_func(x):
            return x * 3

        result = uncached_func(7)
        assert result == 21

    def test_optimize_with_parallel(self):
        """Test optimize with parallel execution."""

        @optimize(jit=True, parallel=True)
        def parallel_func(arr):
            total = 0.0
            for val in arr:
                total += val
            return total

        test_arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = parallel_func(test_arr)
        assert result == 15.0

    def test_optimize_with_nogil(self):
        """Test optimize with GIL release."""

        @optimize(jit=True, nogil=True)
        def nogil_func(n):
            result = 0.0
            for i in range(n):
                result += i
            return result

        result = nogil_func(100)
        expected = sum(range(100))
        assert result == expected

    def test_optimize_with_fastmath_disabled(self):
        """Test optimize with fastmath disabled."""

        @optimize(jit=True, fastmath=False)
        def precise_math(x):
            return x * x + x * 0.1

        result = precise_math(5.0)
        assert abs(result - 25.5) < 0.001

    def test_optimize_preserves_function_name(self):
        """Test that optimization preserves function metadata."""

        @optimize
        def my_special_function(x):
            """This is a docstring."""
            return x

        assert my_special_function.__name__ == "my_special_function"
        assert my_special_function.__doc__ == "This is a docstring."

    def test_optimize_original_function_reference(self):
        """Test that original function is preserved."""

        def original(x):
            return x * 2

        optimized = optimize(original)

        assert optimized._original_function is original
        assert optimized(5) == 10


class TestGlobalFunctions:
    """Test global helper functions."""

    def test_get_optimization_stats(self):
        """Test getting optimization statistics."""
        stats = get_optimization_stats()

        assert isinstance(stats, dict)
        assert "optimized_functions" in stats
        assert "jit_compilations" in stats

    def test_clear_optimization_cache(self):
        """Test clearing optimization cache."""
        # Should work without errors
        clear_optimization_cache()
        assert True

    def test_set_optimization_level(self):
        """Test setting optimization level."""
        for level in [0, 1, 2, 3]:
            set_optimization_level(level)

        # Test invalid level
        with pytest.raises(ValueError):
            set_optimization_level(5)

        with pytest.raises(ValueError):
            set_optimization_level(-1)

    def test_enable_disable_profiling(self):
        """Test enabling and disabling profiling."""
        enable_profiling()
        disable_profiling()
        assert True

    def test_get_specialization_stats(self):
        """Test getting specialization statistics."""
        stats = get_specialization_stats()

        assert isinstance(stats, dict)

    def test_clear_specialization_cache(self):
        """Test clearing specialization cache."""
        clear_specialization_cache()
        assert True

    def test_configure_specialization(self):
        """Test configuring specialization."""
        configure_specialization(
            min_calls_for_specialization=10,
            min_performance_gain=0.3,
            enable_adaptive_learning=True,
        )
        assert True


class TestOptimizationEngine:
    """Test OptimizationEngine class."""

    def test_engine_initialization(self):
        """Test engine creation."""
        engine = OptimizationEngine()

        assert engine.optimization_level == 1
        assert engine.profiling_enabled is False
        assert isinstance(engine.cache, dict)
        assert isinstance(engine.stats, dict)

    def test_optimize_function_with_jit(self):
        """Test optimizing function with JIT."""
        engine = OptimizationEngine()

        def compute(x):
            return x * 2

        config = {"jit": True, "profile": False, "cache": True}
        optimized = engine.optimize_function(compute, config)

        assert optimized is not None
        result = optimized(5)
        assert result == 10

    def test_optimize_function_cache_hit(self):
        """Test cache hit on repeated optimization."""
        engine = OptimizationEngine()

        def test_func(x):
            return x + 1

        config = {"jit": True, "profile": False, "cache": True}

        # First call - cache miss
        opt1 = engine.optimize_function(test_func, config)
        initial_misses = engine.stats["cache_misses"]

        # Second call - should hit cache
        opt2 = engine.optimize_function(test_func, config)
        final_hits = engine.stats["cache_hits"]

        assert final_hits > 0
        assert opt1 is not None
        assert opt2 is not None

    def test_optimize_function_with_profiling(self):
        """Test function optimization with profiling."""
        engine = OptimizationEngine()

        def profiled_func(x, y):
            return x * y

        config = {"jit": False, "profile": True, "cache": True}
        optimized = engine.optimize_function(profiled_func, config)

        result = optimized(3, 4)
        assert result == 12

        # Check profiling data exists
        if hasattr(optimized, "_profile_data"):
            assert optimized._profile_data["call_count"] >= 1

    def test_jit_compilation_fallback(self):
        """Test JIT compilation fallback on incompatible code."""
        engine = OptimizationEngine()

        # Function that can't be JIT compiled (uses list methods)
        def non_jittable(data):
            # Use list to avoid dict which Numba can't compile
            return len(data)

        config = {"jit": True, "profile": False, "cache": True}
        optimized = engine.optimize_function(non_jittable, config)

        # Should work (Numba may handle or fall back)
        result = optimized([1, 2, 3])
        assert result == 3

    @pytest.mark.xfail(reason="Numba lazy compilation behavior varies by version")
    def test_jit_compilation_exception_handling(self):
        """Test JIT handles exceptions properly."""
        engine = OptimizationEngine()

        # Function that may cause JIT issues but should fall back
        def problematic_func(x):
            # Use a pattern that Numba might have trouble with
            if hasattr(x, "__dict__"):
                return len(x.__dict__)
            return 0

        config = {"jit": True, "profile": False, "cache": True}
        # Should fall back gracefully or compile successfully
        optimized = engine.optimize_function(problematic_func, config)

        # Test with simple object
        class SimpleObj:
            pass

        obj = SimpleObj()
        # Either works or falls back - either way no crash
        result = optimized(obj)
        assert result >= 0

    def test_get_stats(self):
        """Test getting engine statistics."""
        engine = OptimizationEngine()

        def test_func(x):
            return x

        config = {"jit": True, "profile": False, "cache": True}
        engine.optimize_function(test_func, config)

        stats = engine.get_stats()

        assert "optimized_functions" in stats
        assert "jit_compilations" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "total_optimization_time" in stats

    def test_clear_cache(self):
        """Test clearing engine cache."""
        engine = OptimizationEngine()

        def test_func(x):
            return x

        config = {"jit": True, "profile": False, "cache": True}
        engine.optimize_function(test_func, config)

        assert len(engine.cache) > 0

        engine.clear_cache()

        assert len(engine.cache) == 0

    def test_set_optimization_level(self):
        """Test setting optimization level."""
        engine = OptimizationEngine()

        for level in [0, 1, 2, 3]:
            engine.set_optimization_level(level)
            assert engine.optimization_level == level

        # Test invalid level
        with pytest.raises(ValueError):
            engine.set_optimization_level(4)

    def test_enable_disable_profiling(self):
        """Test enabling/disabling profiling."""
        engine = OptimizationEngine()

        assert engine.profiling_enabled is False

        engine.enable_profiling()
        assert engine.profiling_enabled is True

        engine.disable_profiling()
        assert engine.profiling_enabled is False

    def test_profiling_wrapper_error_handling(self):
        """Test profiling wrapper handles errors correctly."""
        engine = OptimizationEngine()

        def failing_func(x):
            if x < 0:
                raise ValueError("Negative value")
            return x

        config = {"jit": False, "profile": True, "cache": True}
        optimized = engine.optimize_function(failing_func, config)

        # Should work normally
        assert optimized(5) == 5

        # Should raise error correctly
        with pytest.raises(ValueError):
            optimized(-1)

    def test_profiling_tracks_multiple_calls(self):
        """Test profiling tracks statistics across multiple calls."""
        engine = OptimizationEngine()

        def tracked_func(x):
            return x * 2

        config = {"jit": False, "profile": True, "cache": True}
        optimized = engine.optimize_function(tracked_func, config)

        # Call multiple times
        for i in range(5):
            optimized(i)

        # Check profiling data
        if hasattr(optimized, "_profile_data"):
            profile_data = optimized._profile_data
            assert profile_data["call_count"] == 5
            assert profile_data["total_time"] > 0
            assert profile_data["avg_time"] > 0
            assert profile_data["min_time"] >= 0
            assert profile_data["max_time"] >= profile_data["min_time"]

    def test_jit_config_options(self):
        """Test JIT configuration with various options."""
        engine = OptimizationEngine()

        def test_func(x):
            return x + 1

        configs = [
            {"jit": True, "cache": True, "nogil": False, "fastmath": True},
            {"jit": True, "cache": False, "nogil": True, "fastmath": False},
            {"jit": True, "cache": True, "parallel": False},
        ]

        for config in configs:
            optimized = engine.optimize_function(test_func, config)
            assert optimized(5) == 6

    def test_optimization_stats_tracking(self):
        """Test that statistics are properly tracked."""
        engine = OptimizationEngine()

        def func1(x):
            return x

        def func2(x):
            return x * 2

        config = {"jit": True, "profile": False, "cache": True}

        # Optimize multiple functions
        engine.optimize_function(func1, config)
        engine.optimize_function(func2, config)

        stats = engine.get_stats()

        assert stats["optimized_functions"] >= 2
        assert stats["jit_compilations"] >= 0
        assert stats["total_optimization_time"] >= 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_optimize_lambda_function(self):
        """Test optimizing lambda functions."""
        optimized_lambda = optimize(lambda x: x * 2)

        result = optimized_lambda(5)
        assert result == 10

    def test_optimize_function_with_defaults(self):
        """Test optimizing function with default arguments."""

        @optimize
        def func_with_defaults(x, y=10):
            return x + y

        assert func_with_defaults(5) == 15
        assert func_with_defaults(5, 20) == 25

    def test_optimize_function_with_kwargs(self):
        """Test optimizing function with keyword arguments."""

        @optimize(jit=False)  # Disable JIT as **kwargs not supported by Numba
        def func_with_kwargs(x, **kwargs):
            return x + kwargs.get("offset", 0)

        assert func_with_kwargs(5) == 5
        assert func_with_kwargs(5, offset=10) == 15

    def test_multiple_decorators(self):
        """Test optimize works with multiple decorators."""

        def outer_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs) + 1

            return wrapper

        @outer_decorator
        @optimize(jit=True)
        def decorated_func(x):
            return x * 2

        result = decorated_func(5)
        assert result == 11  # (5 * 2) + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
