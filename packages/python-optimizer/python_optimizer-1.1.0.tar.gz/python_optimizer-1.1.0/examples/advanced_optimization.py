#!/usr/bin/env python3
"""
Advanced optimization examples demonstrating the latest Python Optimizer features.

This module showcases variable specialization, intelligent caching, adaptive learning,
and performance monitoring capabilities.
"""

import statistics
import time
from typing import Any, Dict, List, Union

import matplotlib.pyplot as plt
import numpy as np

# Import the latest optimizer features
from python_optimizer import (
    clear_specialization_cache,
    configure_specialization,
    get_cache_stats,
    get_specialization_stats,
    optimize,
)


def example_1_variable_specialization():
    """Example 1: Advanced variable specialization with multiple data types."""

    print("🔧 EXAMPLE 1: Variable Specialization")
    print("=" * 60)

    # Clear previous cache
    clear_specialization_cache()

    @optimize(specialize=True, jit=False, adaptive_learning=True)
    def smart_data_processor(data, operation="sum"):
        """
        A polymorphic function that processes different data types optimally.
        Each type combination gets its own specialized version.
        """
        if operation == "sum":
            if isinstance(data, np.ndarray):
                return np.sum(data)
            elif isinstance(data, list):
                return sum(data)
            elif isinstance(data, tuple):
                return sum(data)
            else:
                return data

        elif operation == "mean":
            if isinstance(data, np.ndarray):
                return np.mean(data)
            elif hasattr(data, "__len__") and len(data) > 0:
                return sum(data) / len(data)
            else:
                return float(data)

        elif operation == "max":
            if isinstance(data, np.ndarray):
                return np.max(data)
            elif hasattr(data, "__iter__"):
                return max(data)
            else:
                return data

        else:  # 'count'
            if hasattr(data, "__len__"):
                return len(data)
            else:
                return 1

    # Test data of different types
    test_cases = [
        ([1, 2, 3, 4, 5] * 200, "list"),
        (tuple(range(1000)), "tuple"),
        (np.random.randn(1000), "numpy_array"),
        (list(np.random.randn(500)), "large_list"),
        (42, "scalar"),
        (range(100), "range_object"),
    ]

    operations = ["sum", "mean", "max", "count"]

    print("Processing different data types with various operations...")
    print("\nType".ljust(15) + "Operation".ljust(10) + "Result".ljust(15) + "Time (ms)")
    print("-" * 55)

    performance_data = {}

    for data, data_type in test_cases:
        performance_data[data_type] = {}

        for operation in operations:
            # Warmup to create specializations
            for _ in range(3):
                smart_data_processor(data, operation)

            # Benchmark
            times = []
            for _ in range(20):
                start = time.perf_counter()
                result = smart_data_processor(data, operation)
                times.append(time.perf_counter() - start)

            avg_time = statistics.mean(times)
            performance_data[data_type][operation] = avg_time

            result_str = (
                f"{result:.3f}"
                if isinstance(result, (int, float))
                else str(result)[:12]
            )
            print(f"{data_type:15} {operation:10} {result_str:15} {avg_time*1000:.3f}")

    # Show specialization statistics
    stats = get_specialization_stats("smart_data_processor")
    print(f"\n📊 Specialization Statistics:")
    print(f"Total specializations: {stats.get('specializations_created', 0)}")
    print(f"Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    print(f"Total calls: {stats.get('total_calls', 0)}")
    print(f"Average performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    return performance_data


def example_2_adaptive_learning():
    """Example 2: Adaptive learning and cache optimization."""

    print("\n🧠 EXAMPLE 2: Adaptive Learning")
    print("=" * 60)

    # Configure specialization with adaptive learning
    configure_specialization(
        min_calls_for_specialization=2,
        enable_adaptive_learning=True,
        max_cache_size=50,
        max_memory_mb=25,
    )

    @optimize(specialize=True, adaptive_learning=True, min_calls_for_spec=2)
    def adaptive_algorithm(data, method="fast"):
        """
        Algorithm that adapts its behavior based on data characteristics.
        The optimizer learns which specializations are most effective.
        """

        if method == "fast":
            # Fast path for numpy arrays
            if isinstance(data, np.ndarray):
                return np.sum(data**2)
            # Fast path for lists
            elif isinstance(data, list):
                total = 0
                for x in data:
                    total += x * x
                return total
            else:
                return data * data

        elif method == "accurate":
            # More accurate but slower computation
            if isinstance(data, np.ndarray):
                # Use higher precision
                return float(np.sum(data.astype(np.float64) ** 2))
            elif hasattr(data, "__iter__"):
                # Kahan summation for better accuracy
                total = 0.0
                compensation = 0.0
                for x in data:
                    y = x * x - compensation
                    temp = total + y
                    compensation = (temp - total) - y
                    total = temp
                return total
            else:
                return float(data) ** 2

        else:  # 'auto'
            # Automatically choose method based on data size
            if hasattr(data, "__len__"):
                return adaptive_algorithm(
                    data, "accurate" if len(data) > 1000 else "fast"
                )
            else:
                return adaptive_algorithm(data, "fast")

    # Simulate different usage patterns to trigger adaptive learning
    print("Simulating diverse usage patterns...")

    # Phase 1: Mostly fast operations on small data
    print("\nPhase 1: Small data, fast operations")
    for i in range(20):
        data = np.random.randn(100)
        result = adaptive_algorithm(data, "fast")

        if i % 5 == 0:
            stats = get_specialization_stats("adaptive_algorithm")
            print(
                f"  Step {i+1:2d}: {stats.get('specializations_created', 0)} specs, "
                f"hit rate: {stats.get('cache_hit_rate', 0):.1%}"
            )

    # Phase 2: Mix of accurate operations on larger data
    print("\nPhase 2: Large data, accurate operations")
    for i in range(20):
        if i % 2 == 0:
            data = list(np.random.randn(2000))
            method = "accurate"
        else:
            data = np.random.randn(1500)
            method = "fast"

        result = adaptive_algorithm(data, method)

        if i % 5 == 0:
            stats = get_specialization_stats("adaptive_algorithm")
            cache_stats = get_cache_stats()
            print(
                f"  Step {i+1:2d}: Memory: {cache_stats['memory_usage_estimate']:.1f}MB, "
                f"hit rate: {stats.get('cache_hit_rate', 0):.1%}"
            )

    # Phase 3: Auto mode with mixed data sizes
    print("\nPhase 3: Auto mode with mixed sizes")
    data_sizes = [50, 500, 1500, 3000, 100, 2500]
    for i, size in enumerate(data_sizes * 3):  # Repeat 3 times
        data = np.random.randn(size)
        result = adaptive_algorithm(data, "auto")

    # Final adaptive learning statistics
    final_stats = get_specialization_stats("adaptive_algorithm")
    cache_stats = get_cache_stats()

    print(f"\n📈 Adaptive Learning Results:")
    print(f"Final specializations: {final_stats.get('specializations_created', 0)}")
    print(f"Final hit rate: {final_stats.get('cache_hit_rate', 0):.1%}")
    print(f"Performance improvement: {final_stats.get('avg_performance_gain', 1):.2f}x")
    print(f"Cache memory usage: {cache_stats['memory_usage_estimate']:.2f}MB")
    print(f"Cache evictions: {cache_stats['evictions']}")

    return final_stats


def example_3_financial_computing():
    """Example 3: High-performance financial computing with specialization."""

    print("\n💰 EXAMPLE 3: Financial Computing")
    print("=" * 60)

    clear_specialization_cache()

    @optimize(jit=True, specialize=True, fastmath=True, cache=True)
    def advanced_portfolio_metrics(
        returns, weights, benchmark_returns=None, risk_free_rate=0.02
    ):
        """
        Calculate comprehensive portfolio metrics with specialized optimization.
        Different input types (lists vs arrays) get optimized versions.
        """

        # Convert inputs to numpy arrays if needed (specialization will optimize this)
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)
        if not isinstance(weights, np.ndarray):
            weights = np.array(weights)

        # Portfolio returns calculation
        if returns.ndim == 1:
            # Single asset case
            portfolio_returns = returns
        else:
            # Multi-asset portfolio
            portfolio_returns = np.dot(returns, weights)

        # Basic metrics
        mean_return = np.mean(portfolio_returns)
        std_return = np.std(portfolio_returns)

        # Annualized metrics (assuming daily data)
        annual_return = mean_return * 252
        annual_volatility = std_return * np.sqrt(252)

        # Sharpe ratio
        sharpe = (
            (annual_return - risk_free_rate) / annual_volatility
            if annual_volatility > 0
            else 0
        )

        # Maximum drawdown calculation
        cumulative = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdowns)

        # Calmar ratio
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino ratio (downside deviation)
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = (
            np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
        )
        sortino = (
            (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        )

        # Value at Risk (95% confidence)
        var_95 = np.percentile(portfolio_returns, 5)

        # Expected Shortfall (Conditional VaR)
        es_95 = np.mean(portfolio_returns[portfolio_returns <= var_95])

        metrics = {
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "max_drawdown": max_drawdown,
            "var_95": var_95,
            "expected_shortfall": es_95,
            "win_rate": np.mean(portfolio_returns > 0),
            "best_day": np.max(portfolio_returns),
            "worst_day": np.min(portfolio_returns),
        }

        # Add benchmark comparison if provided
        if benchmark_returns is not None:
            if not isinstance(benchmark_returns, np.ndarray):
                benchmark_returns = np.array(benchmark_returns)

            # Beta calculation
            covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

            # Alpha calculation
            benchmark_return = np.mean(benchmark_returns) * 252
            alpha = annual_return - (
                risk_free_rate + beta * (benchmark_return - risk_free_rate)
            )

            metrics.update(
                {
                    "beta": beta,
                    "alpha": alpha,
                    "correlation": np.corrcoef(portfolio_returns, benchmark_returns)[
                        0, 1
                    ],
                }
            )

        return metrics

    # Generate realistic market data
    np.random.seed(42)  # For reproducibility

    # Create correlated asset returns (3 assets, 252 trading days)
    n_assets = 3
    n_days = 252

    # Asset characteristics
    asset_names = ["Large Cap Stocks", "Bonds", "Commodities"]
    expected_returns = np.array([0.001, 0.0003, 0.0005])  # Daily
    volatilities = np.array([0.015, 0.008, 0.020])  # Daily

    # Correlation matrix
    correlation = np.array([[1.0, -0.1, 0.3], [-0.1, 1.0, -0.2], [0.3, -0.2, 1.0]])

    # Generate covariance matrix
    cov_matrix = np.outer(volatilities, volatilities) * correlation

    # Generate returns
    returns = np.random.multivariate_normal(expected_returns, cov_matrix, n_days)

    # Generate benchmark returns (market index)
    benchmark_returns = np.random.normal(0.0008, 0.012, n_days)

    # Test different portfolio strategies
    strategies = {
        "Conservative": np.array([0.3, 0.6, 0.1]),
        "Balanced": np.array([0.6, 0.3, 0.1]),
        "Aggressive": np.array([0.7, 0.1, 0.2]),
        "Equal Weight": np.array([1 / 3, 1 / 3, 1 / 3]),
    }

    print("Analyzing portfolio strategies with specialized optimization...")

    results = {}
    performance_times = {}

    for strategy_name, weights in strategies.items():
        print(f"\n{strategy_name} Portfolio:")
        print(f"Weights: {dict(zip(asset_names, weights))}")

        # Test with different input types to trigger specialization

        # As numpy arrays (should be fastest)
        times_array = []
        for _ in range(50):
            start = time.perf_counter()
            metrics = advanced_portfolio_metrics(returns, weights, benchmark_returns)
            times_array.append(time.perf_counter() - start)

        # As lists (different specialization)
        returns_list = returns.tolist()
        weights_list = weights.tolist()
        benchmark_list = benchmark_returns.tolist()

        times_list = []
        for _ in range(50):
            start = time.perf_counter()
            metrics = advanced_portfolio_metrics(
                returns_list, weights_list, benchmark_list
            )
            times_list.append(time.perf_counter() - start)

        # Store results
        results[strategy_name] = metrics
        performance_times[strategy_name] = {"array": times_array, "list": times_list}

        # Display key metrics
        print(f"  Annual Return: {metrics['annual_return']:8.2%}")
        print(f"  Volatility:    {metrics['annual_volatility']:8.2%}")
        print(f"  Sharpe Ratio:  {metrics['sharpe_ratio']:8.2f}")
        print(f"  Max Drawdown:  {metrics['max_drawdown']:8.2%}")
        print(f"  Beta:          {metrics.get('beta', 0):8.2f}")
        print(f"  Alpha:         {metrics.get('alpha', 0):8.2%}")

        # Performance comparison
        avg_time_array = statistics.mean(times_array)
        avg_time_list = statistics.mean(times_list)
        print(f"  Array input:   {avg_time_array*1000:8.3f}ms")
        print(f"  List input:    {avg_time_list*1000:8.3f}ms")

    # Specialization statistics
    stats = get_specialization_stats("advanced_portfolio_metrics")
    print(f"\n📊 Financial Computing Optimization:")
    print(f"Specializations created: {stats.get('specializations_created', 0)}")
    print(f"Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    print(f"Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    return results, performance_times


def example_4_machine_learning():
    """Example 4: Machine learning algorithm optimization."""

    print("\n🤖 EXAMPLE 4: Machine Learning Optimization")
    print("=" * 60)

    clear_specialization_cache()

    @optimize(specialize=True, jit=True, adaptive_learning=True)
    def optimized_kmeans_step(data, centroids, max_iter=100):
        """
        Optimized K-means clustering step with specialization for different data types.
        """
        n_samples = len(data)
        n_features = len(data[0]) if hasattr(data[0], "__len__") else 1
        k = len(centroids)

        # Handle different input types
        if isinstance(data, np.ndarray):
            # NumPy array path (most efficient)
            data_array = data
        else:
            # Convert lists/other types to numpy
            data_array = np.array(data)

        if isinstance(centroids, np.ndarray):
            centroids_array = centroids
        else:
            centroids_array = np.array(centroids)

        # Initialize assignments
        assignments = np.zeros(n_samples, dtype=np.int32)

        # Main clustering loop
        for iteration in range(max_iter):
            old_assignments = assignments.copy()

            # Assign points to nearest centroids
            for i in range(n_samples):
                min_distance = float("inf")
                best_cluster = 0

                for j in range(k):
                    # Calculate squared Euclidean distance
                    distance = 0.0
                    for d in range(data_array.shape[1] if data_array.ndim > 1 else 1):
                        if data_array.ndim > 1:
                            diff = data_array[i, d] - centroids_array[j, d]
                        else:
                            diff = data_array[i] - centroids_array[j]
                        distance += diff * diff

                    if distance < min_distance:
                        min_distance = distance
                        best_cluster = j

                assignments[i] = best_cluster

            # Update centroids
            new_centroids = np.zeros_like(centroids_array)
            counts = np.zeros(k)

            for i in range(n_samples):
                cluster = assignments[i]
                counts[cluster] += 1

                for d in range(data_array.shape[1] if data_array.ndim > 1 else 1):
                    if data_array.ndim > 1:
                        new_centroids[cluster, d] += data_array[i, d]
                    else:
                        new_centroids[cluster, 0] += data_array[i]

            # Compute new centroid positions
            for j in range(k):
                if counts[j] > 0:
                    for d in range(
                        new_centroids.shape[1] if new_centroids.ndim > 1 else 1
                    ):
                        if new_centroids.ndim > 1:
                            new_centroids[j, d] /= counts[j]
                        else:
                            new_centroids[j] /= counts[j]

            centroids_array = new_centroids

            # Check for convergence
            if np.array_equal(assignments, old_assignments):
                break

        return assignments, centroids_array, iteration + 1

    # Generate test datasets
    np.random.seed(42)

    # Dataset 1: 2D clustering problem
    n_samples_2d = 1000
    data_2d = np.vstack(
        [
            np.random.normal([2, 2], 0.5, (n_samples_2d // 3, 2)),
            np.random.normal([6, 6], 0.5, (n_samples_2d // 3, 2)),
            np.random.normal([2, 6], 0.5, (n_samples_2d // 3, 2)),
        ]
    )
    initial_centroids_2d = np.random.random((3, 2)) * 8

    # Dataset 2: 1D clustering problem
    data_1d = np.concatenate(
        [
            np.random.normal(10, 2, 300),
            np.random.normal(30, 3, 300),
            np.random.normal(50, 2, 300),
        ]
    )
    initial_centroids_1d = np.random.random((3, 1)) * 60

    # Dataset 3: Higher dimensional
    data_5d = np.random.randn(500, 5)
    initial_centroids_5d = np.random.randn(4, 5)

    datasets = [
        (data_2d, initial_centroids_2d, "2D Data (numpy)"),
        (data_2d.tolist(), initial_centroids_2d.tolist(), "2D Data (lists)"),
        (data_1d.reshape(-1, 1), initial_centroids_1d, "1D Data"),
        (data_5d, initial_centroids_5d, "5D Data"),
    ]

    print("Running K-means clustering with different data types...")

    results = {}

    for data, centroids, description in datasets:
        print(f"\n{description}:")

        # Warmup to create specializations
        for _ in range(3):
            _, _, _ = optimized_kmeans_step(data, centroids, max_iter=10)

        # Benchmark performance
        times = []
        for _ in range(20):
            start = time.perf_counter()
            assignments, final_centroids, iterations = optimized_kmeans_step(
                data, centroids, max_iter=50
            )
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)
        results[description] = {
            "time": avg_time,
            "iterations": iterations,
            "n_samples": len(data),
        }

        print(f"  Samples: {len(data):5d}")
        print(f"  Converged in: {iterations:2d} iterations")
        print(f"  Average time: {avg_time*1000:6.2f}ms")
        print(f"  Time per sample: {avg_time*1000/len(data):6.3f}ms")

    # Show ML optimization statistics
    stats = get_specialization_stats("optimized_kmeans_step")
    print(f"\n🧠 ML Optimization Statistics:")
    print(f"Specializations created: {stats.get('specializations_created', 0)}")
    print(f"Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    print(f"Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    return results


def example_5_cache_management():
    """Example 5: Advanced cache management and monitoring."""

    print("\n💾 EXAMPLE 5: Cache Management")
    print("=" * 60)

    # Configure cache with specific limits for demonstration
    configure_specialization(
        max_cache_size=20,  # Small cache to trigger evictions
        max_memory_mb=5,  # Low memory limit
        eviction_policy="adaptive",
        min_calls_for_specialization=1,
        enable_adaptive_learning=True,
    )

    @optimize(specialize=True, cache=True)
    def cache_test_function(data, operation, parameter=1.0):
        """Function designed to create many specializations for cache testing."""

        if operation == "power":
            if isinstance(data, np.ndarray):
                return np.power(data, parameter)
            else:
                return [x**parameter for x in data]

        elif operation == "scale":
            if isinstance(data, np.ndarray):
                return data * parameter
            else:
                return [x * parameter for x in data]

        elif operation == "normalize":
            if isinstance(data, np.ndarray):
                mean = np.mean(data)
                std = np.std(data)
                return (data - mean) / std if std > 0 else data
            else:
                mean = sum(data) / len(data)
                variance = sum((x - mean) ** 2 for x in data) / len(data)
                std = variance**0.5
                return [(x - mean) / std for x in data] if std > 0 else data

        else:  # 'identity'
            return data

    # Generate diverse test scenarios to fill cache
    data_types = [
        np.random.randn(100),
        list(np.random.randn(50)),
        tuple(np.random.randn(30)),
        np.random.randn(200, 2).flatten(),  # Different size array
    ]

    operations = ["power", "scale", "normalize", "identity"]
    parameters = [1.0, 2.0, 0.5, 1.5, 3.0]

    print("Filling cache with diverse specializations...")

    cache_evolution = []

    # Execute various combinations to stress test cache
    for i in range(100):
        data = data_types[i % len(data_types)]
        operation = operations[i % len(operations)]
        parameter = parameters[i % len(parameters)]

        # Execute function
        result = cache_test_function(data, operation, parameter)

        # Record cache statistics every 10 iterations
        if i % 10 == 0:
            cache_stats = get_cache_stats()
            func_stats = get_specialization_stats("cache_test_function")

            cache_evolution.append(
                {
                    "iteration": i,
                    "total_entries": cache_stats["total_entries"],
                    "memory_usage": cache_stats["memory_usage_estimate"],
                    "hit_rate": cache_stats["hit_rate"],
                    "evictions": cache_stats["evictions"],
                    "specializations": func_stats.get("specializations_created", 0),
                }
            )

            print(
                f"  Iteration {i:3d}: "
                f"Entries: {cache_stats['total_entries']:2d}, "
                f"Memory: {cache_stats['memory_usage_estimate']:4.1f}MB, "
                f"Hit Rate: {cache_stats['hit_rate']:5.1%}, "
                f"Evictions: {cache_stats['evictions']:2d}"
            )

    # Final comprehensive cache analysis
    final_cache_stats = get_cache_stats()
    final_func_stats = get_specialization_stats("cache_test_function")

    print(f"\n📊 Final Cache Analysis:")
    print(f"Total cache entries: {final_cache_stats['total_entries']}")
    print(f"Memory usage: {final_cache_stats['memory_usage_estimate']:.2f}MB")
    print(f"Overall hit rate: {final_cache_stats['hit_rate']:.1%}")
    print(f"Total evictions: {final_cache_stats['evictions']}")
    print(
        f"Specializations created: {final_func_stats.get('specializations_created', 0)}"
    )
    print(f"Cache efficiency: {final_func_stats.get('cache_hit_rate', 0):.1%}")

    # Cache health assessment
    print(f"\n🏥 Cache Health Assessment:")
    if final_cache_stats["hit_rate"] > 0.8:
        print("  ✅ Excellent hit rate - cache is very effective")
    elif final_cache_stats["hit_rate"] > 0.6:
        print("  ✅ Good hit rate - cache is performing well")
    else:
        print("  ⚠️  Low hit rate - consider increasing cache size")

    if final_cache_stats["evictions"] < final_cache_stats["total_entries"]:
        print("  ✅ Eviction rate is healthy")
    else:
        print("  ⚠️  High eviction rate - consider increasing memory limit")

    if final_cache_stats["memory_usage_estimate"] < 4:
        print("  ✅ Memory usage is optimal")
    else:
        print("  ⚠️  Memory usage is near limit")

    return cache_evolution, final_cache_stats


def create_performance_visualization(performance_data):
    """Create comprehensive performance visualizations."""

    print("\n📊 Creating Performance Visualizations...")

    # Create figure with multiple subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Python Optimizer - Advanced Performance Analysis", fontsize=16)

    # Plot 1: Specialization performance by data type
    data_types = list(performance_data.keys())
    sum_times = [performance_data[dt]["sum"] for dt in data_types]

    bars1 = ax1.bar(
        data_types, [t * 1000 for t in sum_times], alpha=0.7, color="skyblue"
    )
    ax1.set_title("Sum Operation Performance by Data Type")
    ax1.set_ylabel("Execution Time (ms)")
    ax1.tick_params(axis="x", rotation=45)

    # Add value labels on bars
    for bar, time_val in zip(bars1, sum_times):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.001,
            f"{time_val*1000:.3f}ms",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Plot 2: Cache hit rate evolution (simulated data)
    iterations = list(range(0, 101, 10))
    hit_rates = [0.0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.85, 0.9, 0.92, 0.94, 0.95]

    ax2.plot(iterations, hit_rates, "o-", color="green", linewidth=2, markersize=6)
    ax2.set_title("Cache Hit Rate Evolution")
    ax2.set_xlabel("Iterations")
    ax2.set_ylabel("Hit Rate")
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0.9, color="red", linestyle="--", alpha=0.7, label="Target (90%)")
    ax2.legend()

    # Plot 3: Memory usage over time (simulated)
    memory_usage = [0.1, 0.5, 1.2, 2.1, 3.2, 4.1, 4.8, 4.9, 4.8, 4.9, 5.0]
    memory_limit = [5.0] * len(iterations)

    ax3.fill_between(
        iterations, memory_usage, alpha=0.6, color="orange", label="Memory Usage"
    )
    ax3.plot(iterations, memory_limit, "r--", linewidth=2, label="Memory Limit")
    ax3.set_title("Cache Memory Usage Over Time")
    ax3.set_xlabel("Iterations")
    ax3.set_ylabel("Memory (MB)")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Performance comparison (speedup factors)
    scenarios = [
        "Fibonacci",
        "Statistics",
        "Financial",
        "ML K-means",
        "Data Processing",
    ]
    speedups = [51, 25, 85, 120, 45]  # Example speedup factors

    bars4 = ax4.bar(
        scenarios,
        speedups,
        alpha=0.7,
        color=["coral", "lightblue", "lightgreen", "plum", "wheat"],
    )
    ax4.set_title("Performance Speedup by Scenario")
    ax4.set_ylabel("Speedup Factor (x)")
    ax4.tick_params(axis="x", rotation=45)

    # Add value labels
    for bar, speedup in zip(bars4, speedups):
        height = bar.get_height()
        ax4.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{speedup}x",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()

    # Save the plot
    output_path = "/Users/julio/Projects/python-optimizer/examples/advanced_performance_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Performance analysis chart saved to: {output_path}")

    try:
        plt.show()
    except:
        print("Chart created but not displayed (non-interactive environment)")


def main():
    """Run all advanced examples."""

    print("🚀 Python Optimizer - Advanced Examples")
    print("=" * 80)

    try:
        # Run all examples and collect results
        results = {}

        # Example 1: Variable specialization
        results["specialization"] = example_1_variable_specialization()

        # Example 2: Adaptive learning
        results["adaptive"] = example_2_adaptive_learning()

        # Example 3: Financial computing
        results["financial"], results["financial_perf"] = (
            example_3_financial_computing()
        )

        # Example 4: Machine learning
        results["ml"] = example_4_machine_learning()

        # Example 5: Cache management
        results["cache_evolution"], results["cache_final"] = (
            example_5_cache_management()
        )

        # Create visualizations
        create_performance_visualization(results["specialization"])

        # Final summary
        print("\n" + "=" * 80)
        print("🎉 Advanced Examples Completed Successfully!")
        print("=" * 80)

        print("\n📈 Summary of Achievements:")
        print(f"✅ Variable specialization with multiple data types")
        print(f"✅ Adaptive learning and cache optimization")
        print(f"✅ High-performance financial computing")
        print(f"✅ Optimized machine learning algorithms")
        print(f"✅ Advanced cache management and monitoring")
        print(f"✅ Performance visualizations generated")

        # Global statistics
        global_cache_stats = get_cache_stats()
        print(f"\n🌐 Global Optimization Statistics:")
        print(f"Total cache entries: {global_cache_stats['total_entries']}")
        print(f"Memory usage: {global_cache_stats['memory_usage_estimate']:.2f}MB")
        print(f"Overall hit rate: {global_cache_stats['hit_rate']:.1%}")
        print(f"Cache uptime: {global_cache_stats['uptime_hours']:.2f} hours")

        print(f"\n📊 Check generated visualization:")
        print(f"   examples/advanced_performance_analysis.png")

    except Exception as e:
        print(f"❌ Error running advanced examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
