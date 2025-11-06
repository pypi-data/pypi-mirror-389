"""
Basic tests for the Python Optimizer package.
"""

import numpy as np
import pytest

from python_optimizer import optimize
from python_optimizer.core.engine import OptimizationEngine


def test_optimize_decorator_basic():
    """Test basic functionality of the optimize decorator."""

    @optimize(jit=True)
    def add_numbers(x, y):
        return x + y

    result = add_numbers(5, 3)
    assert result == 8


def test_optimize_decorator_with_numpy():
    """Test optimize decorator with NumPy arrays."""

    @optimize(jit=True, fastmath=True)
    def sum_array(arr):
        total = 0.0
        for i in range(len(arr)):
            total += arr[i]
        return total

    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sum_array(arr)
    expected = np.sum(arr)

    np.testing.assert_allclose(result, expected)


def test_optimization_engine():
    """Test the optimization engine."""
    engine = OptimizationEngine()

    def simple_function(x):
        return x * 2

    config = {"jit": True, "cache": True}
    optimized_func = engine.optimize_function(simple_function, config)

    # Should work the same
    assert optimized_func(5) == simple_function(5)

    # Should have stats
    stats = engine.get_stats()
    assert stats["optimized_functions"] >= 1


def test_profiling():
    """Test profiling functionality."""

    @optimize(jit=True, profile=True)
    def compute_sum(arr):
        """Simple iterative function that Numba can compile."""
        total = 0.0
        for i in range(len(arr)):
            total += arr[i] * arr[i]
        return total

    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = compute_sum(arr)
    assert result == 55.0  # 1 + 4 + 9 + 16 + 25


def test_version():
    """Test that version is accessible."""
    from python_optimizer import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


if __name__ == "__main__":
    pytest.main([__file__])
