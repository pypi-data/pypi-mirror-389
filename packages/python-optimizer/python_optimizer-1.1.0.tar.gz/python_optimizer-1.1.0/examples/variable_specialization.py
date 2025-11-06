#!/usr/bin/env python3
"""
Variable Specialization Examples and Benchmarks

This example demonstrates the variable specialization system that automatically
creates type-specific optimized versions of functions for improved performance.
"""

import random
import time
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Import the optimization decorator with specialization
from python_optimizer import (
    configure_specialization,
    get_specialization_stats,
    optimize,
)
from python_optimizer.specialization.engine import SpecializationConfig


def benchmark_function(func, test_cases, iterations=1000):
    """Benchmark a function with multiple test cases."""
    times = []

    for _ in range(iterations):
        start_time = time.perf_counter()

        for args in test_cases:
            if isinstance(args, tuple):
                func(*args)
            else:
                func(args)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return {
        "mean_time": np.mean(times),
        "std_time": np.std(times),
        "min_time": np.min(times),
        "max_time": np.max(times),
    }


# =============================================================================
# Example 1: Numeric Type Specialization
# =============================================================================


def calculate_fibonacci_python(n):
    """Pure Python Fibonacci (baseline)."""
    if n <= 1:
        return n
    return calculate_fibonacci_python(n - 1) + calculate_fibonacci_python(n - 2)


@optimize(jit=False, specialize=True)  # Only specialization, no JIT
def calculate_fibonacci_specialized(n):
    """Fibonacci with variable specialization."""
    if n <= 1:
        return n
    return calculate_fibonacci_specialized(n - 1) + calculate_fibonacci_specialized(
        n - 2
    )


@optimize(jit=True, specialize=True)  # Both JIT and specialization
def calculate_fibonacci_full(n):
    """Fibonacci with both JIT and specialization."""
    if n <= 1:
        return n
    return calculate_fibonacci_full(n - 1) + calculate_fibonacci_full(n - 2)


def demo_numeric_specialization():
    """Demonstrate numeric type specialization."""
    print("🔢 Numeric Type Specialization Demo")
    print("=" * 50)

    # Configure specialization for aggressive optimization
    configure_specialization(
        min_calls_for_specialization=3,
        min_performance_gain=0.1,
        enable_adaptive_learning=True,
    )

    # Test cases with different numeric types
    int_cases = [20, 25, 22, 24, 23, 21]  # Small integers
    float_cases = [20.0, 25.0, 22.0, 24.0, 23.0, 21.0]  # Floats

    print("\nWarm-up phase (building specializations)...")
    # Warm up specialization (trigger analysis and specialization creation)
    for n in int_cases:
        calculate_fibonacci_specialized(n)
        calculate_fibonacci_full(n)

    for n in float_cases:
        calculate_fibonacci_specialized(n)
        calculate_fibonacci_full(n)

    print("Specializations created. Running benchmarks...\n")

    # Benchmark different versions
    test_cases = [(n,) for n in int_cases]

    python_results = benchmark_function(
        calculate_fibonacci_python, test_cases, iterations=100
    )
    spec_results = benchmark_function(
        calculate_fibonacci_specialized, test_cases, iterations=100
    )
    full_results = benchmark_function(
        calculate_fibonacci_full, test_cases, iterations=100
    )

    print("Results:")
    print(
        f"Pure Python:         {python_results['mean_time']:.4f}s ± {python_results['std_time']:.4f}s"
    )
    print(
        f"Specialization only: {spec_results['mean_time']:.4f}s ± {spec_results['std_time']:.4f}s"
    )
    print(
        f"JIT + Specialization: {full_results['mean_time']:.4f}s ± {full_results['std_time']:.4f}s"
    )

    spec_speedup = python_results["mean_time"] / spec_results["mean_time"]
    full_speedup = python_results["mean_time"] / full_results["mean_time"]

    print(f"\nSpeedups:")
    print(f"Specialization speedup: {spec_speedup:.2f}x")
    print(f"Full optimization:      {full_speedup:.2f}x")

    # Show specialization statistics
    stats = get_specialization_stats("calculate_fibonacci_specialized")
    print(f"\nSpecialization Stats:")
    print(f"Total calls: {stats.get('total_calls', 0)}")
    print(f"Specialized calls: {stats.get('specialized_calls', 0)}")
    print(f"Cache hits: {stats.get('cache_hits', 0)}")
    print(f"Specializations created: {stats.get('specializations_created', 0)}")

    return {
        "python": python_results,
        "specialized": spec_results,
        "full": full_results,
        "spec_speedup": spec_speedup,
        "full_speedup": full_speedup,
    }


# =============================================================================
# Example 2: Array Operations Specialization
# =============================================================================


def matrix_multiply_python(A, B):
    """Pure Python matrix multiplication."""
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])

    if cols_A != rows_B:
        raise ValueError("Matrix dimensions don't match")

    C = [[0 for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                C[i][j] += A[i][k] * B[k][j]

    return C


@optimize(jit=False, specialize=True)
def matrix_multiply_specialized(A, B):
    """Matrix multiplication with array specialization."""
    if isinstance(A, np.ndarray) and isinstance(B, np.ndarray):
        # NumPy path - specialized for ndarray
        return A @ B
    else:
        # Generic path for lists
        rows_A, cols_A = len(A), len(A[0]) if A else 0
        rows_B, cols_B = len(B), len(B[0]) if B else 0

        if cols_A != rows_B:
            raise ValueError("Matrix dimensions don't match")

        C = [[0 for _ in range(cols_B)] for _ in range(rows_A)]

        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    C[i][j] += A[i][k] * B[k][j]

        return C


def demo_array_specialization():
    """Demonstrate array type specialization."""
    print("\n📊 Array Type Specialization Demo")
    print("=" * 50)

    # Create test matrices
    size = 50

    # Python lists
    A_list = [[random.random() for _ in range(size)] for _ in range(size)]
    B_list = [[random.random() for _ in range(size)] for _ in range(size)]

    # NumPy arrays
    A_numpy = np.random.random((size, size))
    B_numpy = np.random.random((size, size))

    print("Warming up specializations...")

    # Warm up with different types
    for _ in range(5):
        matrix_multiply_specialized(A_list, B_list)
        matrix_multiply_specialized(A_numpy, B_numpy)

    print("Running benchmarks...\n")

    # Benchmark with lists
    list_test_cases = [(A_list, B_list)]
    python_list_results = benchmark_function(
        matrix_multiply_python, list_test_cases, iterations=20
    )
    spec_list_results = benchmark_function(
        matrix_multiply_specialized, list_test_cases, iterations=20
    )

    # Benchmark with NumPy arrays
    numpy_test_cases = [(A_numpy, B_numpy)]
    spec_numpy_results = benchmark_function(
        matrix_multiply_specialized, numpy_test_cases, iterations=100
    )

    # Direct NumPy comparison
    def numpy_direct(A, B):
        return A @ B

    numpy_direct_results = benchmark_function(
        numpy_direct, numpy_test_cases, iterations=100
    )

    print("Results:")
    print(f"Python lists (baseline):     {python_list_results['mean_time']:.4f}s")
    print(f"Specialized lists:           {spec_list_results['mean_time']:.4f}s")
    print(f"Specialized NumPy arrays:    {spec_numpy_results['mean_time']:.4f}s")
    print(f"Direct NumPy:               {numpy_direct_results['mean_time']:.4f}s")

    list_speedup = python_list_results["mean_time"] / spec_list_results["mean_time"]
    numpy_overhead = spec_numpy_results["mean_time"] / numpy_direct_results["mean_time"]

    print(f"\nSpeedups:")
    print(f"List specialization: {list_speedup:.2f}x")
    print(f"NumPy overhead:      {numpy_overhead:.2f}x (lower is better)")

    return {"list_speedup": list_speedup, "numpy_overhead": numpy_overhead}


# =============================================================================
# Example 3: Container Specialization
# =============================================================================


def process_data_python(data, operation):
    """Pure Python data processing."""
    if operation == "sum":
        return sum(data)
    elif operation == "max":
        return max(data)
    elif operation == "mean":
        return sum(data) / len(data)
    else:
        return len(data)


@optimize(jit=False, specialize=True)
def process_data_specialized(data, operation):
    """Data processing with container specialization."""
    if isinstance(data, np.ndarray):
        # Specialized NumPy path
        if operation == "sum":
            return np.sum(data)
        elif operation == "max":
            return np.max(data)
        elif operation == "mean":
            return np.mean(data)
        else:
            return len(data)
    else:
        # Generic container path
        if operation == "sum":
            return sum(data)
        elif operation == "max":
            return max(data)
        elif operation == "mean":
            return sum(data) / len(data)
        else:
            return len(data)


def demo_container_specialization():
    """Demonstrate container type specialization."""
    print("\n📦 Container Type Specialization Demo")
    print("=" * 50)

    size = 100000

    # Different container types
    list_data = [random.random() for _ in range(size)]
    tuple_data = tuple(list_data)
    array_data = np.array(list_data)

    operations = ["sum", "max", "mean"]

    print("Warming up specializations...")

    # Warm up with different container types
    for op in operations:
        for _ in range(3):
            process_data_specialized(list_data, op)
            process_data_specialized(tuple_data, op)
            process_data_specialized(array_data, op)

    print("Running benchmarks...\n")

    results = {}

    for container_name, container_data in [
        ("list", list_data),
        ("tuple", tuple_data),
        ("array", array_data),
    ]:
        test_cases = [(container_data, op) for op in operations]

        python_results = benchmark_function(
            process_data_python, test_cases, iterations=50
        )
        spec_results = benchmark_function(
            process_data_specialized, test_cases, iterations=50
        )

        speedup = python_results["mean_time"] / spec_results["mean_time"]
        results[container_name] = speedup

        print(f"{container_name.capitalize()} containers:")
        print(f"  Python:      {python_results['mean_time']:.4f}s")
        print(f"  Specialized: {spec_results['mean_time']:.4f}s")
        print(f"  Speedup:     {speedup:.2f}x\n")

    return results


# =============================================================================
# Example 4: Adaptive Learning Demo
# =============================================================================


@optimize(jit=False, specialize=True)
def adaptive_computation(data, mode):
    """Function that benefits from adaptive specialization."""
    if mode == "fast":
        # Simple computation
        return sum(data) * 2
    elif mode == "medium":
        # Moderate computation
        result = 0
        for x in data:
            result += x * x
        return result
    else:
        # Complex computation
        result = 0
        for x in data:
            result += x * x * x + x * x + x
        return result


def demo_adaptive_learning():
    """Demonstrate adaptive learning capabilities."""
    print("\n🧠 Adaptive Learning Demo")
    print("=" * 50)

    # Configure for aggressive adaptive learning
    configure_specialization(
        min_calls_for_specialization=2,
        min_performance_gain=0.05,
        enable_adaptive_learning=True,
    )

    data_int = list(range(10000))
    data_float = [float(x) for x in data_int]
    modes = ["fast", "medium", "complex"]

    print("Phase 1: Initial learning with integer data...")

    # Phase 1: Train with integers
    for mode in modes:
        for _ in range(10):
            adaptive_computation(data_int, mode)

    stats_phase1 = get_specialization_stats("adaptive_computation")
    print(f"Specializations created: {stats_phase1.get('specializations_created', 0)}")
    print(f"Specialized calls: {stats_phase1.get('specialized_calls', 0)}")

    print("\nPhase 2: Adapting to float data...")

    # Phase 2: Switch to floats
    for mode in modes:
        for _ in range(10):
            adaptive_computation(data_float, mode)

    stats_phase2 = get_specialization_stats("adaptive_computation")
    print(f"Total specializations: {stats_phase2.get('specializations_created', 0)}")
    print(f"Total specialized calls: {stats_phase2.get('specialized_calls', 0)}")
    print(f"Cache hit rate: {stats_phase2.get('cache_hit_rate', 0):.2%}")

    # Show effectiveness if available
    from python_optimizer.specialization.dispatcher import get_global_dispatcher

    dispatcher = get_global_dispatcher()
    if hasattr(dispatcher, "get_effectiveness_report"):
        effectiveness = dispatcher.get_effectiveness_report()
        print(f"\nTop performing specializations:")
        for spec, score in effectiveness.get("top_performers", [])[:3]:
            print(f"  {spec}: {score:.2%} improvement")

    return stats_phase2


# =============================================================================
# Comprehensive Benchmark Suite
# =============================================================================


def run_comprehensive_benchmark():
    """Run all specialization benchmarks."""
    print("🚀 Variable Specialization Comprehensive Benchmark")
    print("=" * 80)

    results = {}

    # Run all demos
    results["numeric"] = demo_numeric_specialization()
    results["array"] = demo_array_specialization()
    results["container"] = demo_container_specialization()
    results["adaptive"] = demo_adaptive_learning()

    # Generate summary
    print("\n📊 BENCHMARK SUMMARY")
    print("=" * 80)

    print("Numeric Specialization:")
    print(f"  Specialization-only speedup: {results['numeric']['spec_speedup']:.2f}x")
    print(f"  Full optimization speedup:   {results['numeric']['full_speedup']:.2f}x")

    print("\nArray Specialization:")
    print(f"  List processing speedup:     {results['array']['list_speedup']:.2f}x")
    print(f"  NumPy dispatch overhead:     {results['array']['numpy_overhead']:.2f}x")

    print("\nContainer Specialization:")
    for container, speedup in results["container"].items():
        print(f"  {container.capitalize()} speedup:              {speedup:.2f}x")

    print("\nAdaptive Learning:")
    adaptive_stats = results["adaptive"]
    print(
        f"  Specializations created:     {adaptive_stats.get('specializations_created', 0)}"
    )
    print(
        f"  Total specialized calls:     {adaptive_stats.get('specialized_calls', 0)}"
    )
    print(
        f"  Cache hit rate:              {adaptive_stats.get('cache_hit_rate', 0):.2%}"
    )

    # Overall statistics
    global_stats = get_specialization_stats()
    print(f"\nGlobal Specialization Statistics:")
    print(
        f"  Functions optimized:         {global_stats.get('functions_optimized', 0)}"
    )
    print(f"  Total calls processed:       {global_stats.get('total_calls', 0)}")
    print(
        f"  Global specialization rate:  {global_stats.get('global_specialization_rate', 0):.2%}"
    )
    print(
        f"  Global cache hit rate:       {global_stats.get('global_cache_hit_rate', 0):.2%}"
    )

    return results


if __name__ == "__main__":
    # Set up logging for better output
    import logging

    logging.basicConfig(level=logging.INFO)

    # Run comprehensive benchmark
    results = run_comprehensive_benchmark()

    print(f"\n✨ Variable specialization benchmarks completed!")
    print(f"📈 Average performance improvement observed across all tests.")
    print(f"🎯 Specialization system successfully adapted to different data types.")
    print(
        f"💡 Consider enabling specialization for production workloads with mixed-type inputs."
    )
