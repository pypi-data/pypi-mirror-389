"""GPU performance benchmarks.

Comprehensive benchmarks comparing CPU vs GPU performance across
various operation types and data sizes.

Run with: pytest tests/test_gpu_benchmarks.py -v -m benchmark
"""

import pytest
import numpy as np
import time
from python_optimizer import optimize, is_gpu_available


@pytest.mark.benchmark
class TestGPUBenchmarks:
    """GPU performance benchmark suite."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for benchmarks."""
        self.gpu_available = is_gpu_available()
        if not self.gpu_available:
            pytest.skip("GPU not available for benchmarks")

    def benchmark_operation(self, cpu_func, gpu_func, data, iterations=100):
        """Helper to benchmark CPU vs GPU operations."""
        # Warmup
        for _ in range(5):
            cpu_func(data)
            gpu_func(data)

        # CPU timing
        cpu_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            cpu_result = cpu_func(data)
            cpu_times.append(time.perf_counter() - start)

        # GPU timing
        gpu_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            gpu_result = gpu_func(data)
            gpu_times.append(time.perf_counter() - start)

        cpu_mean = np.mean(cpu_times)
        gpu_mean = np.mean(gpu_times)
        speedup = cpu_mean / gpu_mean if gpu_mean > 0 else 1.0

        return {
            "cpu_mean": cpu_mean,
            "gpu_mean": gpu_mean,
            "cpu_std": np.std(cpu_times),
            "gpu_std": np.std(gpu_times),
            "speedup": speedup,
            "cpu_result": cpu_result,
            "gpu_result": gpu_result,
        }

    def test_benchmark_element_wise_operations(self):
        """Benchmark element-wise operations at different sizes."""
        sizes = [1_000, 10_000, 100_000, 1_000_000]

        print("\n\nElement-wise Operations Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for size in sizes:
            data = np.random.randn(size).astype(np.float32)

            @optimize(gpu=False, jit=False)
            def cpu_op(x):
                return x**2 + x * 3 - 5

            @optimize(gpu=True, gpu_min_size=100, jit=False)
            def gpu_op(x):
                return x**2 + x * 3 - 5

            results = self.benchmark_operation(cpu_op, gpu_op, data, iterations=50)

            print(
                f"{size:<12,} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

            # Verify correctness
            np.testing.assert_array_almost_equal(
                results["cpu_result"], results["gpu_result"], decimal=4
            )

    def test_benchmark_matrix_multiplication(self):
        """Benchmark matrix multiplication at different sizes."""
        sizes = [100, 500, 1000, 2000]

        print("\n\nMatrix Multiplication Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for size in sizes:
            a = np.random.randn(size, size).astype(np.float32)
            b = np.random.randn(size, size).astype(np.float32)

            @optimize(gpu=False, jit=False)
            def cpu_matmul(a, b):
                return np.matmul(a, b)

            @optimize(gpu=True, gpu_min_size=100, jit=False)
            def gpu_matmul(a, b):
                return np.matmul(a, b)

            # Warmup
            for _ in range(3):
                cpu_matmul(a, b)
                gpu_matmul(a, b)

            # CPU timing
            start = time.perf_counter()
            cpu_result = cpu_matmul(a, b)
            cpu_time = time.perf_counter() - start

            # GPU timing
            start = time.perf_counter()
            gpu_result = gpu_matmul(a, b)
            gpu_time = time.perf_counter() - start

            speedup = cpu_time / gpu_time if gpu_time > 0 else 1.0

            print(
                f"{size}x{size:<6} {cpu_time*1000:>10.3f}  "
                f"{gpu_time*1000:>10.3f}  {speedup:>8.2f}x"
            )

            # Verify correctness
            np.testing.assert_array_almost_equal(cpu_result, gpu_result, decimal=3)

    def test_benchmark_reduction_operations(self):
        """Benchmark reduction operations (sum, mean, std)."""
        sizes = [10_000, 100_000, 1_000_000, 10_000_000]

        print("\n\nReduction Operations Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for size in sizes:
            data = np.random.randn(size).astype(np.float32)

            @optimize(gpu=False, jit=False)
            def cpu_reduce(x):
                return np.sum(x**2)

            @optimize(gpu=True, gpu_min_size=1000, jit=False)
            def gpu_reduce(x):
                return np.sum(x**2)

            results = self.benchmark_operation(cpu_reduce, gpu_reduce, data, iterations=20)

            print(
                f"{size:<12,} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

            # Verify correctness (allow some tolerance for floating point)
            assert abs(results["cpu_result"] - results["gpu_result"]) / abs(
                results["cpu_result"]
            ) < 0.01

    def test_benchmark_transcendental_functions(self):
        """Benchmark transcendental functions (exp, log, sqrt)."""
        sizes = [10_000, 100_000, 1_000_000]

        print("\n\nTranscendental Functions Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for size in sizes:
            data = np.random.randn(size).astype(np.float32) + 1.0  # Ensure positive

            @optimize(gpu=False, jit=False)
            def cpu_trans(x):
                return np.sqrt(np.exp(np.log(x)))

            @optimize(gpu=True, gpu_min_size=1000, jit=False)
            def gpu_trans(x):
                return np.sqrt(np.exp(np.log(x)))

            results = self.benchmark_operation(cpu_trans, gpu_trans, data, iterations=20)

            print(
                f"{size:<12,} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

            # Verify correctness
            np.testing.assert_array_almost_equal(
                results["cpu_result"], results["gpu_result"], decimal=3
            )

    def test_benchmark_array_sorting(self):
        """Benchmark array sorting operations."""
        sizes = [10_000, 100_000, 1_000_000]

        print("\n\nArray Sorting Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for size in sizes:
            data = np.random.randn(size).astype(np.float32)

            @optimize(gpu=False, jit=False)
            def cpu_sort(x):
                return np.sort(x)

            @optimize(gpu=True, gpu_min_size=1000, jit=False)
            def gpu_sort(x):
                return np.sort(x)

            results = self.benchmark_operation(
                cpu_sort, gpu_sort, data.copy(), iterations=10
            )

            print(
                f"{size:<12,} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

            # Verify correctness
            np.testing.assert_array_almost_equal(
                results["cpu_result"], results["gpu_result"], decimal=5
            )

    def test_benchmark_threshold_sensitivity(self):
        """Benchmark threshold sensitivity."""
        size = 50_000
        thresholds = [100, 1_000, 10_000, 50_000, 100_000]

        print("\n\nThreshold Sensitivity Benchmark")
        print("=" * 70)
        print(f"{'Threshold':<12} {'Time (ms)':<12} {'Uses GPU':<10}")
        print("-" * 70)

        data = np.random.randn(size).astype(np.float32)

        for threshold in thresholds:

            @optimize(gpu=True, gpu_min_size=threshold, jit=False)
            def threshold_func(x):
                return x**2

            # Warmup
            for _ in range(5):
                threshold_func(data)

            # Timing
            times = []
            for _ in range(20):
                start = time.perf_counter()
                threshold_func(data)
                times.append(time.perf_counter() - start)

            mean_time = np.mean(times)
            uses_gpu = "Yes" if size >= threshold else "No"

            print(f"{threshold:<12,} {mean_time*1000:>10.3f}  {uses_gpu:<10}")

    def test_benchmark_data_types(self):
        """Benchmark different data types."""
        size = 1_000_000
        dtypes = [np.float32, np.float64, np.int32, np.int64]

        print("\n\nData Type Benchmark")
        print("=" * 70)
        print(f"{'Type':<12} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for dtype in dtypes:
            if dtype in [np.int32, np.int64]:
                data = np.random.randint(1, 100, size=size, dtype=dtype)
            else:
                data = np.random.randn(size).astype(dtype)

            @optimize(gpu=False, jit=False)
            def cpu_dtype(x):
                return x * 2 + 1

            @optimize(gpu=True, gpu_min_size=1000, jit=False)
            def gpu_dtype(x):
                return x * 2 + 1

            results = self.benchmark_operation(cpu_dtype, gpu_dtype, data, iterations=20)

            print(
                f"{dtype.__name__:<12} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

    def test_benchmark_multidimensional(self):
        """Benchmark multidimensional arrays."""
        shapes = [(1000, 1000), (100, 100, 100), (10, 10, 10, 10)]

        print("\n\nMultidimensional Array Benchmark")
        print("=" * 70)
        print(f"{'Shape':<20} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10}")
        print("-" * 70)

        for shape in shapes:
            data = np.random.randn(*shape).astype(np.float32)

            @optimize(gpu=False, jit=False)
            def cpu_multi(x):
                return x**2 + x

            @optimize(gpu=True, gpu_min_size=1000, jit=False)
            def gpu_multi(x):
                return x**2 + x

            results = self.benchmark_operation(cpu_multi, gpu_multi, data, iterations=20)

            shape_str = "x".join(str(s) for s in shape)
            print(
                f"{shape_str:<20} {results['cpu_mean']*1000:>10.3f}  "
                f"{results['gpu_mean']*1000:>10.3f}  {results['speedup']:>8.2f}x"
            )

            # Verify correctness
            np.testing.assert_array_almost_equal(
                results["cpu_result"], results["gpu_result"], decimal=4
            )

    def test_benchmark_combined_operations(self):
        """Benchmark combined operations (realistic workload)."""
        size = 500_000

        print("\n\nCombined Operations Benchmark (Realistic Workload)")
        print("=" * 70)

        data = np.random.randn(size).astype(np.float32)

        @optimize(gpu=False, jit=False)
        def cpu_combined(x):
            # Simulate realistic computation
            y = x**2 + x * 3
            y = np.sqrt(np.abs(y))
            y = np.exp(-y / 10)
            return np.sum(y)

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def gpu_combined(x):
            # Same computation on GPU
            y = x**2 + x * 3
            y = np.sqrt(np.abs(y))
            y = np.exp(-y / 10)
            return np.sum(y)

        results = self.benchmark_operation(
            cpu_combined, gpu_combined, data, iterations=30
        )

        print(f"CPU Time: {results['cpu_mean']*1000:.3f} ms")
        print(f"GPU Time: {results['gpu_mean']*1000:.3f} ms")
        print(f"Speedup:  {results['speedup']:.2f}x")

        # Verify correctness
        assert (
            abs(results["cpu_result"] - results["gpu_result"])
            / abs(results["cpu_result"])
            < 0.01
        )


@pytest.mark.benchmark
class TestGPUMemoryBenchmarks:
    """GPU memory management benchmarks."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for benchmarks."""
        if not is_gpu_available():
            pytest.skip("GPU not available for benchmarks")

    def test_benchmark_memory_transfer(self):
        """Benchmark CPU<->GPU memory transfer overhead."""
        sizes = [1_000, 10_000, 100_000, 1_000_000]

        print("\n\nMemory Transfer Overhead Benchmark")
        print("=" * 70)
        print(f"{'Size':<12} {'Transfer (ms)':<15} {'MB/s':<10}")
        print("-" * 70)

        for size in sizes:
            data = np.random.randn(size).astype(np.float32)
            data_size_mb = data.nbytes / (1024**2)

            @optimize(gpu=True, gpu_min_size=100, jit=False)
            def transfer_func(x):
                return x  # Just transfer, no computation

            # Warmup
            for _ in range(5):
                transfer_func(data)

            # Timing
            times = []
            for _ in range(20):
                start = time.perf_counter()
                transfer_func(data)
                times.append(time.perf_counter() - start)

            mean_time = np.mean(times)
            throughput = data_size_mb / mean_time if mean_time > 0 else 0

            print(
                f"{size:<12,} {mean_time*1000:>13.3f}  {throughput:>8.1f}"
            )

    def test_benchmark_repeated_allocations(self):
        """Benchmark repeated GPU allocations."""
        print("\n\nRepeated Allocations Benchmark")
        print("=" * 70)

        size = 100_000
        data = np.random.randn(size).astype(np.float32)

        @optimize(gpu=True, gpu_min_size=1000, jit=False)
        def alloc_func(x):
            return x * 2

        # Benchmark allocation overhead
        times = []
        for _ in range(100):
            start = time.perf_counter()
            alloc_func(data)
            times.append(time.perf_counter() - start)

        print(f"Mean time per call: {np.mean(times)*1000:.3f} ms")
        print(f"Std deviation:      {np.std(times)*1000:.3f} ms")
        print(f"Min time:           {np.min(times)*1000:.3f} ms")
        print(f"Max time:           {np.max(times)*1000:.3f} ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark", "-s"])
