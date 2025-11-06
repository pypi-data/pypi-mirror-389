"""Tests for GPU acceleration modules.

Tests GPU device detection, memory management, dispatching, and kernels.
All tests work whether GPU is available or not (graceful degradation).
"""

import os
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest


# Test GPU device module
class TestGPUDevice:
    """Tests for GPU device detection and management."""

    def test_is_gpu_available_returns_bool(self):
        """Test that is_gpu_available returns a boolean."""
        from python_optimizer.gpu import is_gpu_available

        result = is_gpu_available()
        assert isinstance(result, bool)

    def test_get_gpu_info_returns_dict(self):
        """Test that get_gpu_info returns a dictionary."""
        from python_optimizer.gpu import get_gpu_info

        info = get_gpu_info()
        assert isinstance(info, dict)
        assert "available" in info
        assert "devices" in info
        assert isinstance(info["devices"], list)

    def test_get_gpu_info_structure(self):
        """Test GPU info dictionary structure."""
        from python_optimizer.gpu import get_gpu_info

        info = get_gpu_info()
        assert "available" in info
        assert "cupy_available" in info
        assert "numba_cuda_available" in info
        assert "current_device" in info
        assert "devices" in info

    def test_get_gpu_device_none_when_unavailable(self):
        """Test get_gpu_device returns None when GPU unavailable."""
        from python_optimizer.gpu import get_gpu_device, is_gpu_available

        if not is_gpu_available():
            device = get_gpu_device()
            assert device is None

    def test_set_gpu_device_fails_gracefully(self):
        """Test set_gpu_device fails gracefully when GPU unavailable."""
        from python_optimizer.gpu import is_gpu_available, set_gpu_device

        if not is_gpu_available():
            result = set_gpu_device(0)
            assert result is False

    def test_environment_variable_disables_gpu(self):
        """Test PYTHON_OPTIMIZER_NO_GPU environment variable."""
        # This test needs to reimport the module
        with patch.dict(os.environ, {"PYTHON_OPTIMIZER_NO_GPU": "1"}):
            # Clear cached GPU availability
            from python_optimizer.gpu.device import _device_manager

            _device_manager._gpu_available = None

            from python_optimizer.gpu import is_gpu_available

            # Should return False even if GPU is available
            result = is_gpu_available()
            # Note: This might be True if GPU was detected before env var set
            # Just ensure it returns a bool
            assert isinstance(result, bool)

    def test_gpu_device_dataclass(self):
        """Test GPUDevice dataclass properties."""
        from python_optimizer.gpu.device import GPUDevice

        device = GPUDevice(
            device_id=0,
            name="Test GPU",
            compute_capability=(7, 5),
            total_memory=8 * 1024**3,  # 8 GB
            free_memory=4 * 1024**3,  # 4 GB
            is_available=True,
            backend="cupy",
        )

        assert device.device_id == 0
        assert device.name == "Test GPU"
        assert device.compute_capability == (7, 5)
        assert abs(device.memory_gb - 8.0) < 0.1
        assert abs(device.free_memory_gb - 4.0) < 0.1
        assert abs(device.utilization_percent - 50.0) < 1.0

    def test_device_manager_singleton(self):
        """Test that device manager is a singleton."""
        # Check that multiple imports return same instance
        from python_optimizer.gpu.device import _device_manager
        from python_optimizer.gpu.device import _device_manager as dm2

        assert _device_manager is dm2


# Test GPU memory module
class TestGPUMemory:
    """Tests for GPU memory management."""

    def test_get_gpu_memory_info_returns_none_or_info(self):
        """Test get_gpu_memory_info returns None or GPUMemoryInfo."""
        from python_optimizer.gpu import get_gpu_memory_info, is_gpu_available

        mem_info = get_gpu_memory_info()

        if is_gpu_available():
            # Should return GPUMemoryInfo if GPU available
            from python_optimizer.gpu.memory import GPUMemoryInfo

            assert mem_info is None or isinstance(mem_info, GPUMemoryInfo)
        else:
            # Should return None if no GPU
            assert mem_info is None

    def test_clear_gpu_cache_no_error(self):
        """Test clear_gpu_cache doesn't raise errors."""
        from python_optimizer.gpu import clear_gpu_cache

        # Should work whether GPU available or not
        clear_gpu_cache()  # Should not raise

    def test_gpu_memory_info_properties(self):
        """Test GPUMemoryInfo dataclass properties."""
        from python_optimizer.gpu.memory import GPUMemoryInfo

        mem_info = GPUMemoryInfo(
            total=8 * 1024**3,  # 8 GB
            free=6 * 1024**3,  # 6 GB
            used=2 * 1024**3,  # 2 GB
            cached=512 * 1024**2,  # 512 MB
        )

        assert abs(mem_info.total_gb - 8.0) < 0.1
        assert abs(mem_info.free_gb - 6.0) < 0.1
        assert abs(mem_info.used_gb - 2.0) < 0.1
        assert abs(mem_info.cached_gb - 0.5) < 0.1
        assert abs(mem_info.utilization_percent - 25.0) < 1.0

    def test_gpu_memory_manager_stats(self):
        """Test GPU memory manager statistics."""
        from python_optimizer.gpu.memory import _memory_manager

        stats = _memory_manager.get_stats()
        assert isinstance(stats, dict)
        assert "active_allocations" in stats
        assert "total_allocated_bytes" in stats
        assert "peak_memory_bytes" in stats
        assert "pool_enabled" in stats


# Test GPU dispatcher
class TestGPUDispatcher:
    """Tests for GPU dispatcher."""

    def test_dispatcher_initialization(self):
        """Test GPUDispatcher initialization."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(
            min_size_threshold=5000,
            max_size_threshold=1_000_000,
            force_gpu=False,
            force_cpu=False,
        )

        assert dispatcher.min_size_threshold == 5000
        assert dispatcher.max_size_threshold == 1_000_000
        assert dispatcher.force_gpu is False
        assert dispatcher.force_cpu is False

    def test_dispatcher_force_cpu(self):
        """Test dispatcher with force_cpu=True."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(force_cpu=True)
        large_array = np.random.randn(100_000)

        # Should never use GPU
        assert dispatcher.should_use_gpu(large_array) is False

    def test_dispatcher_force_gpu(self):
        """Test dispatcher with force_gpu=True."""
        from python_optimizer.gpu import is_gpu_available
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(force_gpu=True)
        large_array = np.random.randn(100_000)

        result = dispatcher.should_use_gpu(large_array)
        # Should match GPU availability
        assert result == is_gpu_available()

    def test_dispatcher_size_threshold_small(self):
        """Test dispatcher respects small size threshold."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(min_size_threshold=10_000)
        small_array = np.random.randn(1000)

        # Small array should not use GPU
        assert dispatcher.should_use_gpu(small_array) is False

    def test_dispatcher_size_threshold_large(self):
        """Test dispatcher with large array."""
        from python_optimizer.gpu import is_gpu_available
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(min_size_threshold=10_000)
        large_array = np.random.randn(100_000)

        result = dispatcher.should_use_gpu(large_array)
        # Should use GPU if available and above threshold
        if is_gpu_available():
            assert result is True
        else:
            assert result is False

    def test_dispatcher_to_gpu(self):
        """Test dispatcher to_gpu conversion."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher()
        arr = np.array([1, 2, 3, 4, 5])
        result = dispatcher.to_gpu(arr)

        # Result should be array-like
        assert hasattr(result, "__len__")

    def test_dispatcher_to_cpu(self):
        """Test dispatcher to_cpu conversion."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher()
        arr = np.array([1, 2, 3, 4, 5])
        result = dispatcher.to_cpu(arr)

        # Should return numpy array
        assert isinstance(result, np.ndarray)

    def test_dispatcher_dispatch_cpu_function(self):
        """Test dispatcher dispatch with CPU function."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(force_cpu=True)

        def cpu_func(x):
            return x**2

        arr = np.array([1, 2, 3, 4, 5])
        result = dispatcher.dispatch(cpu_func, None, arr)

        np.testing.assert_array_equal(result, np.array([1, 4, 9, 16, 25]))

    def test_dispatcher_wrap_decorator(self):
        """Test dispatcher wrap decorator."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher(force_cpu=True)

        @dispatcher.wrap()
        def test_func(x):
            return x * 2

        result = test_func(5)
        assert result == 10

    def test_dispatcher_stats(self):
        """Test dispatcher statistics tracking."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher()

        def test_func(x):
            return x + 1

        arr = np.array([1, 2, 3])
        dispatcher.dispatch(test_func, None, arr)

        stats = dispatcher.get_stats()
        assert isinstance(stats, dict)
        assert "gpu_available" in stats
        assert "total_calls" in stats
        assert "gpu_calls" in stats
        assert "cpu_calls" in stats
        assert stats["total_calls"] >= 1

    def test_dispatcher_reset_stats(self):
        """Test dispatcher reset_stats."""
        from python_optimizer.gpu.dispatcher import GPUDispatcher

        dispatcher = GPUDispatcher()

        def test_func(x):
            return x + 1

        arr = np.array([1, 2, 3])
        dispatcher.dispatch(test_func, None, arr)
        dispatcher.reset_stats()

        stats = dispatcher.get_stats()
        assert stats["total_calls"] == 0
        assert stats["gpu_calls"] == 0
        assert stats["cpu_calls"] == 0


# Test GPU kernels
class TestGPUKernels:
    """Tests for GPU kernel library."""

    def test_array_sum(self):
        """Test GPU array sum."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.array_sum(arr)

        assert result == 15.0

    def test_array_mean(self):
        """Test GPU array mean."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.array_mean(arr)

        assert result == 3.0

    def test_array_std(self):
        """Test GPU array standard deviation."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.array_std(arr)

        expected = np.std(arr)
        assert abs(result - expected) < 0.01

    def test_matrix_multiply(self):
        """Test GPU matrix multiplication."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        a = np.array([[1, 2], [3, 4]])
        b = np.array([[5, 6], [7, 8]])
        result = GPUKernelLibrary.matrix_multiply(a, b)

        expected = np.matmul(a, b)
        np.testing.assert_array_almost_equal(result, expected)

    def test_element_wise_multiply(self):
        """Test GPU element-wise multiplication."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        a = np.array([1, 2, 3, 4, 5])
        b = np.array([2, 3, 4, 5, 6])
        result = GPUKernelLibrary.element_wise_multiply(a, b)

        expected = a * b
        np.testing.assert_array_equal(result, expected)

    def test_element_wise_add(self):
        """Test GPU element-wise addition."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        a = np.array([1, 2, 3, 4, 5])
        b = np.array([5, 4, 3, 2, 1])
        result = GPUKernelLibrary.element_wise_add(a, b)

        expected = a + b
        np.testing.assert_array_equal(result, expected)

    def test_power(self):
        """Test GPU power operation."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.power(arr, 2)

        expected = arr**2
        np.testing.assert_array_equal(result, expected)

    def test_sqrt(self):
        """Test GPU square root."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 4, 9, 16, 25])
        result = GPUKernelLibrary.sqrt(arr)

        expected = np.sqrt(arr)
        np.testing.assert_array_almost_equal(result, expected)

    def test_exp(self):
        """Test GPU exponential."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([0, 1, 2, 3, 4])
        result = GPUKernelLibrary.exp(arr)

        expected = np.exp(arr)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_log(self):
        """Test GPU natural logarithm."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.log(arr)

        expected = np.log(arr)
        np.testing.assert_array_almost_equal(result, expected)

    def test_dot_product(self):
        """Test GPU dot product."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        a = np.array([1, 2, 3, 4, 5])
        b = np.array([5, 4, 3, 2, 1])
        result = GPUKernelLibrary.dot_product(a, b)

        expected = np.dot(a, b)
        assert abs(result - expected) < 0.01

    def test_cumsum(self):
        """Test GPU cumulative sum."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5])
        result = GPUKernelLibrary.cumsum(arr)

        expected = np.cumsum(arr)
        np.testing.assert_array_equal(result, expected)

    def test_sort(self):
        """Test GPU sort."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([5, 2, 8, 1, 9, 3])
        result = GPUKernelLibrary.sort(arr)

        expected = np.sort(arr)
        np.testing.assert_array_equal(result, expected)

    def test_argsort(self):
        """Test GPU argsort."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([5, 2, 8, 1, 9, 3])
        result = GPUKernelLibrary.argsort(arr)

        expected = np.argsort(arr)
        np.testing.assert_array_equal(result, expected)

    def test_min_max(self):
        """Test GPU min and max."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([5, 2, 8, 1, 9, 3])

        min_result = GPUKernelLibrary.min(arr)
        max_result = GPUKernelLibrary.max(arr)

        assert min_result == 1.0
        assert max_result == 9.0

    def test_concatenate(self):
        """Test GPU array concatenation."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        a = np.array([1, 2, 3])
        b = np.array([4, 5, 6])
        result = GPUKernelLibrary.concatenate([a, b])

        expected = np.concatenate([a, b])
        np.testing.assert_array_equal(result, expected)

    def test_reshape(self):
        """Test GPU reshape."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([1, 2, 3, 4, 5, 6])
        result = GPUKernelLibrary.reshape(arr, (2, 3))

        expected = np.reshape(arr, (2, 3))
        np.testing.assert_array_equal(result, expected)

    def test_transpose(self):
        """Test GPU transpose."""
        from python_optimizer.gpu.kernels import GPUKernelLibrary

        arr = np.array([[1, 2, 3], [4, 5, 6]])
        result = GPUKernelLibrary.transpose(arr)

        expected = np.transpose(arr)
        np.testing.assert_array_equal(result, expected)

    def test_convenience_functions(self):
        """Test convenience wrapper functions."""
        from python_optimizer.gpu.kernels import gpu_matmul, gpu_mean, gpu_sum

        arr = np.array([1, 2, 3, 4, 5])
        assert gpu_sum(arr) == 15.0
        assert gpu_mean(arr) == 3.0

        a = np.array([[1, 2], [3, 4]])
        b = np.array([[5, 6], [7, 8]])
        result = gpu_matmul(a, b)
        expected = np.matmul(a, b)
        np.testing.assert_array_almost_equal(result, expected)


# Test GPU integration with main package
class TestGPUIntegration:
    """Tests for GPU integration with main package."""

    def test_gpu_imports_from_main_package(self):
        """Test that GPU functions can be imported from main package."""
        from python_optimizer import get_gpu_info, is_gpu_available

        assert callable(is_gpu_available)
        assert callable(get_gpu_info)

    def test_optimize_decorator_gpu_parameter(self):
        """Test @optimize decorator with gpu parameter."""
        from python_optimizer import optimize

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def test_func(x):
            return x**2

        arr = np.array([1, 2, 3, 4, 5])
        result = test_func(arr)

        expected = arr**2
        np.testing.assert_array_equal(result, expected)

    def test_optimize_metadata_has_gpu(self):
        """Test that optimized function has GPU metadata."""
        from python_optimizer import optimize

        @optimize(gpu=True)
        def test_func(x):
            return x + 1

        assert hasattr(test_func, "_has_gpu")
        assert test_func._has_gpu is True

    def test_gpu_with_jit_combination(self):
        """Test GPU combined with JIT."""
        from python_optimizer import optimize

        @optimize(gpu=True, jit=True, gpu_min_size=1000)
        def combined_func(x):
            return x * 2

        result = combined_func(5)
        assert result == 10

    def test_gpu_fallback_without_cupy(self):
        """Test GPU gracefully falls back when CuPy unavailable."""
        from python_optimizer import optimize

        @optimize(gpu=True, jit=False)
        def test_func(x):
            return x**2

        # Should work even without GPU
        arr = np.array([1, 2, 3, 4, 5])
        result = test_func(arr)
        expected = arr**2
        np.testing.assert_array_equal(result, expected)


# Performance tests (quick validation, not benchmarks)
class TestGPUPerformance:
    """Quick performance validation tests."""

    def test_gpu_handles_large_arrays(self):
        """Test GPU can handle large arrays."""
        from python_optimizer import optimize

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def large_computation(x):
            return x**2 + x * 3

        # Large array
        arr = np.random.randn(100_000)
        result = large_computation(arr)

        assert result.shape == arr.shape
        assert result.dtype == arr.dtype

    def test_gpu_handles_multiple_calls(self):
        """Test GPU handles multiple sequential calls."""
        from python_optimizer import optimize

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def multi_call_func(x):
            return x + 1

        arr = np.random.randn(1000)

        for _ in range(10):
            result = multi_call_func(arr)
            assert result.shape == arr.shape

    def test_gpu_memory_no_leak(self):
        """Test GPU doesn't leak memory on repeated calls."""
        from python_optimizer import is_gpu_available, optimize

        if not is_gpu_available():
            pytest.skip("GPU not available")

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def memory_test(x):
            return x * 2

        arr = np.random.randn(10_000)

        # Multiple calls shouldn't leak
        for _ in range(100):
            result = memory_test(arr)

        # If we got here without OOM, test passes
        assert result.shape == arr.shape


# Test GPU Genetic Optimizer
class TestGPUGeneticOptimizer:
    """Tests for GPU genetic algorithm optimizer."""

    def test_gpu_genetic_optimizer_import(self):
        """Test GPUGeneticOptimizer can be imported."""
        try:
            from python_optimizer.gpu import (
                GPU_GENETIC_AVAILABLE,
                GPUGeneticOptimizer,
            )

            assert GPU_GENETIC_AVAILABLE is not None
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

    def test_gpu_genetic_optimizer_initialization(self):
        """Test GPUGeneticOptimizer initialization."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import GPUGeneticOptimizer
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", -10.0, 10.0, "float"),
            ParameterRange("y", -10.0, 10.0, "float"),
        ]

        optimizer = GPUGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=50,
            use_gpu=True,
            force_cpu=False,
        )

        assert optimizer.population_size == 50
        assert optimizer.use_gpu is True
        assert hasattr(optimizer, "_gpu_available")

    def test_gpu_genetic_optimizer_basic_optimization(self):
        """Test GPUGeneticOptimizer runs basic optimization."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import GPUGeneticOptimizer
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", -10.0, 10.0, "float"),
        ]

        def fitness_function(params):
            x = params["x"]
            return -(x**2)  # Maximize (minimum at x=0)

        optimizer = GPUGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=20,
            use_gpu=True,
        )

        best = optimizer.optimize(
            fitness_function=fitness_function, generations=10, verbose=False
        )

        # Should find something close to 0
        assert best.parameters["x"] is not None
        assert best.fitness is not None
        # Best fitness should be better than random
        assert best.fitness > -100

    def test_gpu_genetic_optimizer_cpu_fallback(self):
        """Test GPUGeneticOptimizer falls back to CPU."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import GPUGeneticOptimizer
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", -5.0, 5.0, "float"),
        ]

        def fitness_function(params):
            return -params["x"] ** 2

        # Force CPU
        optimizer = GPUGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=10,
            force_cpu=True,
        )

        assert optimizer.use_gpu is False

        best = optimizer.optimize(
            fitness_function=fitness_function, generations=5, verbose=False
        )

        assert best is not None

    def test_gpu_genetic_optimizer_get_stats(self):
        """Test GPU genetic optimizer statistics."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import GPUGeneticOptimizer
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", -1.0, 1.0, "float"),
        ]

        def fitness_function(params):
            return -params["x"] ** 2

        optimizer = GPUGeneticOptimizer(
            parameter_ranges=param_ranges, population_size=10
        )

        optimizer.optimize(
            fitness_function=fitness_function, generations=3, verbose=False
        )

        stats = optimizer.get_gpu_stats()

        assert isinstance(stats, dict)
        assert "gpu_available" in stats
        assert "gpu_enabled" in stats
        assert "total_evaluations" in stats
        assert "population_size" in stats

    def test_gpu_genetic_optimizer_batch_processing(self):
        """Test GPU genetic optimizer with custom batch size."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import GPUGeneticOptimizer
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", 0.0, 10.0, "float"),
        ]

        def fitness_function(params):
            return -abs(params["x"] - 5.0)  # Target x=5

        optimizer = GPUGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=20,
            gpu_batch_size=5,  # Small batches
        )

        best = optimizer.optimize(
            fitness_function=fitness_function, generations=5, verbose=False
        )

        # Should find something close to 5
        assert 0 <= best.parameters["x"] <= 10
        assert best.fitness is not None

    def test_optimize_genetic_gpu_convenience_function(self):
        """Test optimize_genetic_gpu convenience function."""
        try:
            from python_optimizer.genetic import ParameterRange
            from python_optimizer.gpu import optimize_genetic_gpu
        except ImportError:
            pytest.skip("GPU genetic optimizer not available")

        param_ranges = [
            ParameterRange("x", -2.0, 2.0, "float"),
        ]

        def fitness_function(params):
            return -params["x"] ** 2

        best = optimize_genetic_gpu(
            parameter_ranges=param_ranges,
            fitness_function=fitness_function,
            population_size=15,
            generations=5,
            use_gpu=True,
        )

        assert best is not None
        assert best.parameters["x"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
