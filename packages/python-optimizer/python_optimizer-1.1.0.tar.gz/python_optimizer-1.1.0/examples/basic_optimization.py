#!/usr/bin/env python3
"""
Basic optimization example demonstrating the Python Optimizer toolkit.

This example shows how to use the @optimize decorator to accelerate
common Python functions using JIT compilation.
"""

import time

import numpy as np

from python_optimizer import optimize


# Simple numerical computation
@optimize(jit=True, profile=True)
def fibonacci(n):
    """Compute Fibonacci number with JIT optimization."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# Matrix multiplication example
@optimize(jit=True, fastmath=True)
def matrix_multiply(A, B):
    """JIT-optimized matrix multiplication."""
    rows_A, cols_A = A.shape
    rows_B, cols_B = B.shape

    if cols_A != rows_B:
        raise ValueError("Matrix dimensions don't match")

    C = np.zeros((rows_A, cols_B))
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                C[i, j] += A[i, k] * B[k, j]
    return C


# Numerical integration example
@optimize(jit=True, nogil=True)
def monte_carlo_pi(n_samples):
    """Estimate π using Monte Carlo method."""
    inside_circle = 0
    for _ in range(n_samples):
        x = np.random.random()
        y = np.random.random()
        if x * x + y * y <= 1.0:
            inside_circle += 1
    return 4.0 * inside_circle / n_samples


def benchmark_function(func, *args, name="Function"):
    """Benchmark a function's performance."""
    print(f"\n--- Benchmarking {name} ---")

    # Warmup (for JIT compilation)
    print("Warming up...")
    func(*args)

    # Actual benchmark
    start_time = time.perf_counter()
    result = func(*args)
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print(f"Result: {result}")
    print(f"Execution time: {execution_time:.6f} seconds")

    return result, execution_time


def main():
    """Run the basic optimization examples."""
    print("Python Optimizer - Basic Examples")
    print("=" * 50)

    # Example 1: Fibonacci
    print("\n🧮 Example 1: Fibonacci Calculation")
    fib_result, fib_time = benchmark_function(fibonacci, 35, "Fibonacci(35)")

    # Example 2: Matrix multiplication
    print("\n🔢 Example 2: Matrix Multiplication")
    A = np.random.random((100, 100))
    B = np.random.random((100, 100))
    matrix_result, matrix_time = benchmark_function(
        matrix_multiply, A, B, "Matrix Multiplication (100x100)"
    )

    # Example 3: Monte Carlo π estimation
    print("\n🎯 Example 3: Monte Carlo π Estimation")
    pi_result, pi_time = benchmark_function(
        monte_carlo_pi, 1000000, "Monte Carlo π (1M samples)"
    )
    print(f"π estimate: {pi_result:.6f} (error: {abs(pi_result - np.pi):.6f})")

    # Performance summary
    print("\n📊 Performance Summary")
    print("=" * 50)
    print(f"Fibonacci(35):           {fib_time:.6f}s")
    print(f"Matrix Multiplication:   {matrix_time:.6f}s")
    print(f"Monte Carlo π:          {pi_time:.6f}s")

    print("\n✨ All examples completed successfully!")
    print("Note: First runs include JIT compilation time.")
    print("Subsequent calls will be significantly faster!")


if __name__ == "__main__":
    main()
