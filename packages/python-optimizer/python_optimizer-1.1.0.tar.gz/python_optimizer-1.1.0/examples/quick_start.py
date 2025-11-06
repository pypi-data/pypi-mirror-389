#!/usr/bin/env python3
"""
Quick Start Guide for Python Optimizer

This example shows the simplest ways to get started with Python Optimizer
and see immediate performance improvements.
"""

import time

import numpy as np

# Import the optimizer
from python_optimizer import optimize


def example_1_basic_usage():
    """Example 1: Basic usage - just add the decorator!"""

    print("🚀 EXAMPLE 1: Basic Usage")
    print("=" * 50)

    # Just add @optimize to your existing function
    @optimize()  # Uses smart defaults: jit=True, specialize=True
    def calculate_sum_of_squares(numbers):
        """Calculate sum of squares - now optimized automatically!"""
        total = 0
        for num in numbers:
            total += num * num
        return total

    # Test with different data
    test_data = list(range(10000))

    print("Computing sum of squares for 10,000 numbers...")

    # First call includes optimization time
    start = time.perf_counter()
    result = calculate_sum_of_squares(test_data)
    first_time = time.perf_counter() - start

    # Subsequent calls are optimized
    start = time.perf_counter()
    result2 = calculate_sum_of_squares(test_data)
    optimized_time = time.perf_counter() - start

    print(f"Result: {result}")
    print(f"First call (with optimization): {first_time:.4f}s")
    print(f"Optimized call:                {optimized_time:.4f}s")
    print(f"Speedup: {first_time/optimized_time:.1f}x")


def example_2_different_data_types():
    """Example 2: Automatic specialization for different data types"""

    print("\n🔧 EXAMPLE 2: Automatic Specialization")
    print("=" * 50)

    @optimize(specialize=True)  # Enable specialization
    def process_data(data):
        """Process data - optimizes differently for each data type!"""
        if isinstance(data, list):
            return sum(x * x for x in data)
        elif isinstance(data, np.ndarray):
            return np.sum(data**2)
        else:
            return data * data

    # Test different data types
    list_data = [1, 2, 3, 4, 5] * 1000
    array_data = np.array(list_data)
    scalar_data = 42

    print("Processing different data types...")

    # Each type gets its own optimized version
    times = {}

    for name, data in [
        ("List", list_data),
        ("Array", array_data),
        ("Scalar", scalar_data),
    ]:
        # Warmup
        process_data(data)

        # Benchmark
        times_list = []
        for _ in range(20):
            start = time.perf_counter()
            result = process_data(data)
            times_list.append(time.perf_counter() - start)

        avg_time = sum(times_list) / len(times_list)
        times[name] = avg_time

        print(f"{name:6}: result={result:12.0f}, avg_time={avg_time*1000:.3f}ms")

    print(f"\n✨ Each data type gets its own specialized optimized version!")


def example_3_financial_calculation():
    """Example 3: Real-world financial calculation"""

    print("\n💰 EXAMPLE 3: Financial Calculation")
    print("=" * 50)

    @optimize(jit=True, specialize=True)  # JIT + specialization for maximum speed
    def calculate_portfolio_return(prices, weights):
        """Calculate portfolio return with optimization"""

        # Convert to numpy if needed (specialization handles this efficiently)
        if not isinstance(prices, np.ndarray):
            prices = np.array(prices)
        if not isinstance(weights, np.ndarray):
            weights = np.array(weights)

        # Calculate returns
        returns = np.diff(prices, axis=0) / prices[:-1]

        # Portfolio returns
        portfolio_returns = np.dot(returns, weights)

        # Calculate metrics
        total_return = np.prod(1 + portfolio_returns) - 1
        avg_return = np.mean(portfolio_returns)
        volatility = np.std(portfolio_returns)
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0

        return {
            "total_return": total_return,
            "avg_return": avg_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
        }

    # Generate sample market data
    np.random.seed(42)
    n_days = 252  # One trading year
    n_assets = 3

    # Simulate price movements
    initial_prices = np.array([100.0, 50.0, 25.0])
    returns = np.random.normal(0.0005, 0.015, (n_days, n_assets))  # Daily returns

    prices = np.zeros((n_days + 1, n_assets))
    prices[0] = initial_prices

    for i in range(n_days):
        prices[i + 1] = prices[i] * (1 + returns[i])

    # Portfolio weights
    weights = np.array([0.6, 0.3, 0.1])

    print("Calculating portfolio performance for 1 year of daily data...")

    # Test with both numpy arrays and lists to show specialization
    test_cases = [
        (prices, weights, "NumPy arrays"),
        (prices.tolist(), weights.tolist(), "Python lists"),
    ]

    for prices_data, weights_data, description in test_cases:
        # Warmup
        calculate_portfolio_return(prices_data, weights_data)

        # Benchmark
        times = []
        for _ in range(50):
            start = time.perf_counter()
            result = calculate_portfolio_return(prices_data, weights_data)
            times.append(time.perf_counter() - start)

        avg_time = sum(times) / len(times)

        print(f"\n{description}:")
        print(f"  Total return: {result['total_return']:8.2%}")
        print(f"  Avg daily return: {result['avg_return']:8.4%}")
        print(f"  Volatility: {result['volatility']:8.4%}")
        print(f"  Sharpe ratio: {result['sharpe_ratio']:8.2f}")
        print(f"  Execution time: {avg_time*1000:8.3f}ms")


def example_4_monitoring():
    """Example 4: Monitor optimization performance"""

    print("\n📊 EXAMPLE 4: Performance Monitoring")
    print("=" * 50)

    from python_optimizer import get_cache_stats, get_specialization_stats

    @optimize(specialize=True, adaptive_learning=True)
    def monitored_function(data, operation="sum"):
        """Function with performance monitoring"""
        if operation == "sum":
            return sum(data) if isinstance(data, list) else np.sum(data)
        elif operation == "mean":
            return sum(data) / len(data) if isinstance(data, list) else np.mean(data)
        else:
            return len(data)

    # Run some operations
    test_data = [
        ([1, 2, 3] * 100, "sum"),
        (np.array([1, 2, 3] * 100), "sum"),
        ([1, 2, 3] * 100, "mean"),
        (np.array([1, 2, 3] * 100), "mean"),
    ]

    print("Running monitored operations...")
    for data, op in test_data * 10:  # Run multiple times
        result = monitored_function(data, op)

    # Check performance statistics
    stats = get_specialization_stats("monitored_function")
    cache_stats = get_cache_stats()

    print(f"\n📈 Performance Statistics:")
    print(f"Function: monitored_function")
    print(f"  Specializations created: {stats.get('specializations_created', 0)}")
    print(f"  Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    print(f"  Total calls: {stats.get('total_calls', 0)}")
    print(f"  Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    print(f"\nGlobal Cache:")
    print(f"  Total entries: {cache_stats['total_entries']}")
    print(f"  Memory usage: {cache_stats['memory_usage_estimate']:.2f} MB")
    print(f"  Hit rate: {cache_stats['hit_rate']:.1%}")

    print(f"\n✨ The optimizer automatically tracks performance!")


def example_5_configuration():
    """Example 5: Customize optimization settings"""

    print("\n⚙️  EXAMPLE 5: Configuration")
    print("=" * 50)

    from python_optimizer import configure_specialization

    # Configure optimization behavior
    configure_specialization(
        min_calls_for_specialization=2,  # Create specializations quickly
        enable_adaptive_learning=True,  # Learn from usage patterns
        max_cache_size=100,  # Limit cache size
        max_memory_mb=20,  # Limit memory usage
    )

    @optimize(specialize=True)
    def configured_function(x, y):
        """Function using custom configuration"""
        return x * y + x**2 + y**2

    print("Using custom optimization configuration...")

    # Test the configured function
    test_cases = [(1, 2), (1.5, 2.5), (np.array([1, 2]), np.array([3, 4]))]

    for x, y in test_cases:
        # Call multiple times to trigger specialization
        for _ in range(3):
            result = configured_function(x, y)

        print(f"f({x}, {y}) = {result}")

    # Show current configuration worked
    stats = get_specialization_stats("configured_function")
    print(f"\nConfiguration Results:")
    print(f"  Specializations: {stats.get('specializations_created', 0)}")
    print(f"  Hit rate: {stats.get('cache_hit_rate', 0):.1%}")

    print(f"\n✅ Custom configuration applied successfully!")


def main():
    """Run all quick start examples"""

    print("🏁 Python Optimizer - Quick Start Guide")
    print("=" * 60)
    print("Get started with just one decorator - @optimize()!")
    print()

    try:
        # Run examples in order
        example_1_basic_usage()
        example_2_different_data_types()
        example_3_financial_calculation()
        example_4_monitoring()
        example_5_configuration()

        # Summary
        print("\n" + "=" * 60)
        print("🎉 Quick Start Complete!")
        print("=" * 60)
        print("\n🚀 Key Takeaways:")
        print("• Add @optimize() to any function for instant speedup")
        print("• Specialization automatically optimizes for different data types")
        print("• Built-in monitoring shows performance gains")
        print("• Configuration lets you customize behavior")
        print("• Works with existing code - no changes needed!")

        print("\n📚 Next Steps:")
        print("• Try advanced_optimization.py for more features")
        print("• Check examples/ directory for specific use cases")
        print("• Read docs/optimization_overview.md for complete guide")

    except Exception as e:
        print(f"❌ Error in quick start: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
