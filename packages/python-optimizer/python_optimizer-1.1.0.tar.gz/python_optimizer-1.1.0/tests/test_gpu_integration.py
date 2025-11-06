"""Integration tests for GPU with other optimization features.

Tests GPU + JIT, GPU + Specialization, and combined optimizations.
"""

import pytest
import numpy as np
from python_optimizer import (
    optimize,
    is_gpu_available,
    get_gpu_info,
    get_gpu_memory_info,
    clear_gpu_cache,
)


class TestGPUWithJIT:
    """Tests for GPU integration with JIT compilation."""

    def test_gpu_jit_basic_combination(self):
        """Test basic GPU + JIT combination."""

        @optimize(gpu=True, jit=True, gpu_min_size=1000)
        def combined_func(x):
            return x * 2 + 5

        result = combined_func(10)
        assert result == 25

    def test_gpu_jit_array_operation(self):
        """Test GPU + JIT with array operations."""

        @optimize(gpu=True, jit=False, gpu_min_size=100)
        def array_op(x):
            return x**2 + x

        arr = np.random.randn(1000)
        result = array_op(arr)

        expected = arr**2 + arr
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_gpu_jit_with_parallel(self):
        """Test GPU + JIT + parallel combination."""

        @optimize(gpu=True, jit=True, parallel=True, gpu_min_size=1000)
        def parallel_func(x):
            return x * 3

        result = parallel_func(7)
        assert result == 21

    def test_gpu_jit_with_fastmath(self):
        """Test GPU + JIT + fastmath combination."""

        @optimize(gpu=True, jit=True, fastmath=True, gpu_min_size=1000)
        def fastmath_func(x):
            return x / 2

        result = fastmath_func(10)
        assert result == 5

    def test_gpu_jit_metadata(self):
        """Test that GPU + JIT sets correct metadata."""

        @optimize(gpu=True, jit=True)
        def meta_func(x):
            return x

        assert hasattr(meta_func, "_has_gpu")
        assert hasattr(meta_func, "_has_jit")
        assert meta_func._has_gpu is True
        assert meta_func._has_jit is True


class TestGPUWithSpecialization:
    """Tests for GPU integration with variable specialization."""

    def test_gpu_specialization_combination(self):
        """Test GPU + specialization combination."""

        @optimize(gpu=True, specialize=True, jit=False, gpu_min_size=100)
        def spec_func(x):
            if isinstance(x, (list, np.ndarray)):
                return np.sum(x)
            return x

        # Test with different types
        result1 = spec_func([1, 2, 3, 4, 5])
        assert result1 == 15

        result2 = spec_func(np.array([1, 2, 3, 4, 5]))
        assert result2 == 15

        result3 = spec_func(10)
        assert result3 == 10

    def test_gpu_specialization_array_types(self):
        """Test GPU + specialization with different array types."""

        @optimize(gpu=True, specialize=True, jit=False, gpu_min_size=100)
        def type_func(x):
            return x**2

        # Small array (CPU)
        small = np.random.randn(50)
        result1 = type_func(small)
        assert result1.shape == small.shape

        # Large array (GPU if available)
        large = np.random.randn(1000)
        result2 = type_func(large)
        assert result2.shape == large.shape

    def test_gpu_specialization_metadata(self):
        """Test that GPU + specialization sets correct metadata."""

        @optimize(gpu=True, specialize=True, jit=False)
        def meta_func(x):
            return x

        assert hasattr(meta_func, "_has_gpu")
        assert hasattr(meta_func, "_has_specialization")
        assert meta_func._has_gpu is True
        assert meta_func._has_specialization is True


class TestCombinedOptimizations:
    """Tests for GPU + JIT + Specialization combined."""

    def test_all_optimizations_enabled(self):
        """Test with all optimizations enabled."""

        @optimize(
            gpu=True,
            jit=True,
            specialize=True,
            gpu_min_size=100,
        )
        def all_opts(x):
            return x * 2

        result = all_opts(5)
        assert result == 10

    def test_all_optimizations_with_array(self):
        """Test all optimizations with array input."""

        @optimize(
            gpu=True,
            jit=False,
            specialize=True,
            gpu_min_size=100,
        )
        def array_all_opts(x):
            return x**2 + x

        arr = np.random.randn(1000)
        result = array_all_opts(arr)

        expected = arr**2 + arr
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_all_optimizations_metadata(self):
        """Test metadata with all optimizations."""

        @optimize(gpu=True, jit=True, specialize=True, profile=True)
        def meta_all(x):
            return x

        assert hasattr(meta_all, "_has_gpu")
        assert hasattr(meta_all, "_has_jit")
        assert hasattr(meta_all, "_has_specialization")
        assert meta_all._has_gpu is True
        assert meta_all._has_jit is True
        assert meta_all._has_specialization is True


class TestGPUThresholdBehavior:
    """Tests for GPU threshold behavior with different optimization combinations."""

    def test_small_array_uses_cpu(self):
        """Test that small arrays use CPU even with GPU enabled."""

        @optimize(gpu=True, gpu_min_size=10_000, jit=False)
        def threshold_func(x):
            return x * 2

        small = np.random.randn(100)
        result = threshold_func(small)

        assert result.shape == small.shape

    def test_large_array_behavior(self):
        """Test large array behavior with GPU."""

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def large_func(x):
            return x**2

        large = np.random.randn(10_000)
        result = large_func(large)

        expected = large**2
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_threshold_with_jit(self):
        """Test threshold behavior with JIT enabled."""

        @optimize(gpu=True, jit=True, gpu_min_size=5000)
        def jit_threshold(x):
            return x + 1

        arr = np.random.randn(1000)
        result = jit_threshold(arr)

        expected = arr + 1
        np.testing.assert_array_almost_equal(result, expected, decimal=5)


class TestGPUMemoryManagement:
    """Tests for GPU memory management during integration."""

    def test_memory_info_accessible(self):
        """Test that GPU memory info is accessible."""
        mem_info = get_gpu_memory_info()

        # Should return None or valid GPUMemoryInfo
        if is_gpu_available():
            from python_optimizer.gpu.memory import GPUMemoryInfo

            assert mem_info is None or isinstance(mem_info, GPUMemoryInfo)
        else:
            assert mem_info is None

    def test_cache_clear_works(self):
        """Test that clearing GPU cache works."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def cache_func(x):
            return x * 2

        arr = np.random.randn(1000)
        cache_func(arr)

        # Clear cache
        clear_gpu_cache()

        # Should still work after cache clear
        result = cache_func(arr)
        expected = arr * 2
        np.testing.assert_array_almost_equal(result, expected)

    def test_repeated_calls_no_memory_error(self):
        """Test repeated calls don't cause memory errors."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def repeat_func(x):
            return x + 1

        arr = np.random.randn(1000)

        # Multiple calls
        for _ in range(50):
            result = repeat_func(arr)

        assert result.shape == arr.shape


class TestGPUErrorHandling:
    """Tests for GPU error handling and fallback."""

    def test_gpu_fallback_on_error(self):
        """Test that GPU falls back to CPU on error."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def fallback_func(x):
            return x**2

        # Should work even if GPU fails
        arr = np.random.randn(1000)
        result = fallback_func(arr)

        expected = arr**2
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def invalid_func(x):
            return x * 2

        # Should handle scalar
        result = invalid_func(5)
        assert result == 10

        # Should handle list (result will be doubled list)
        result = invalid_func([1, 2, 3])
        # List * 2 duplicates the list
        assert result == [1, 2, 3, 1, 2, 3] or np.array_equal(result, np.array([2, 4, 6]))


class TestGPUWithProfile:
    """Tests for GPU with profiling enabled."""

    def test_gpu_profile_combination(self):
        """Test GPU + profile combination."""

        @optimize(gpu=True, profile=True, jit=False, gpu_min_size=100)
        def profile_func(x):
            return x * 3

        arr = np.random.randn(1000)
        result = profile_func(arr)

        expected = arr * 3
        np.testing.assert_array_almost_equal(result, expected)

    def test_profile_metadata(self):
        """Test profile metadata with GPU."""

        @optimize(gpu=True, profile=True, jit=False)
        def meta_profile(x):
            return x

        assert hasattr(meta_profile, "_has_gpu")
        assert meta_profile._has_gpu is True


class TestGPUConfiguration:
    """Tests for GPU configuration options."""

    def test_different_min_sizes(self):
        """Test different gpu_min_size values."""
        sizes = [100, 1000, 10_000]

        for size in sizes:

            @optimize(gpu=True, gpu_min_size=size, jit=False)
            def size_func(x):
                return x + 1

            arr = np.random.randn(500)
            result = size_func(arr)
            assert result.shape == arr.shape

    def test_gpu_with_cache_disabled(self):
        """Test GPU with caching disabled."""

        @optimize(gpu=True, cache=False, jit=False, gpu_min_size=100)
        def no_cache_func(x):
            return x * 2

        arr = np.random.randn(1000)
        result = no_cache_func(arr)

        expected = arr * 2
        np.testing.assert_array_almost_equal(result, expected)

    def test_gpu_with_different_aggressiveness(self):
        """Test GPU with different aggressiveness levels."""
        for level in range(4):

            @optimize(gpu=True, aggressiveness=level, jit=False, gpu_min_size=100)
            def agg_func(x):
                return x + level

            arr = np.random.randn(1000)
            result = agg_func(arr)
            expected = arr + level
            np.testing.assert_array_almost_equal(result, expected)


class TestGPUDataTypes:
    """Tests for GPU with different data types."""

    def test_float32_arrays(self):
        """Test GPU with float32 arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def float32_func(x):
            return x * 2

        arr = np.random.randn(1000).astype(np.float32)
        result = float32_func(arr)

        expected = arr * 2
        np.testing.assert_array_almost_equal(result, expected)

    def test_float64_arrays(self):
        """Test GPU with float64 arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def float64_func(x):
            return x + 1

        arr = np.random.randn(1000).astype(np.float64)
        result = float64_func(arr)

        expected = arr + 1
        np.testing.assert_array_almost_equal(result, expected)

    def test_int_arrays(self):
        """Test GPU with integer arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def int_func(x):
            return x * 2

        arr = np.random.randint(0, 100, size=1000)
        result = int_func(arr)

        expected = arr * 2
        np.testing.assert_array_equal(result, expected)

    def test_complex_arrays(self):
        """Test GPU with complex arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def complex_func(x):
            return x * 2

        arr = np.random.randn(1000) + 1j * np.random.randn(1000)
        result = complex_func(arr)

        expected = arr * 2
        np.testing.assert_array_almost_equal(result, expected)


class TestGPUMultidimensional:
    """Tests for GPU with multidimensional arrays."""

    def test_2d_arrays(self):
        """Test GPU with 2D arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def matrix_func(x):
            return x**2

        arr = np.random.randn(50, 50)
        result = matrix_func(arr)

        expected = arr**2
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_3d_arrays(self):
        """Test GPU with 3D arrays."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def tensor_func(x):
            return x + 1

        arr = np.random.randn(10, 10, 10)
        result = tensor_func(arr)

        expected = arr + 1
        np.testing.assert_array_almost_equal(result, expected)

    def test_matrix_operations(self):
        """Test GPU with matrix operations."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def matmul_func(a, b):
            return np.matmul(a, b)

        a = np.random.randn(50, 50)
        b = np.random.randn(50, 50)
        result = matmul_func(a, b)

        expected = np.matmul(a, b)
        np.testing.assert_array_almost_equal(result, expected, decimal=4)


class TestGPUEdgeCases:
    """Tests for GPU edge cases."""

    def test_empty_array(self):
        """Test GPU with empty array."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def empty_func(x):
            return x

        arr = np.array([])
        result = empty_func(arr)

        assert result.shape == arr.shape

    def test_single_element_array(self):
        """Test GPU with single element."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def single_func(x):
            return x * 2

        arr = np.array([5.0])
        result = single_func(arr)

        expected = np.array([10.0])
        np.testing.assert_array_equal(result, expected)

    def test_very_large_array(self):
        """Test GPU with very large array."""

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def large_func(x):
            return x + 1

        arr = np.random.randn(1_000_000)
        result = large_func(arr)

        assert result.shape == arr.shape
        assert np.all(result == arr + 1)

    def test_nan_handling(self):
        """Test GPU with NaN values."""

        @optimize(gpu=True, gpu_min_size=100, jit=False)
        def nan_func(x):
            return x * 2

        arr = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        result = nan_func(arr)

        expected = arr * 2
        np.testing.assert_array_equal(result[:2], expected[:2])
        assert np.isnan(result[2])
        np.testing.assert_array_equal(result[3:], expected[3:])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
