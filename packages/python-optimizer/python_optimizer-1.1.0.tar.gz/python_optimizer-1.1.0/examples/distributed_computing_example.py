"""Distributed Computing Example

Demonstrates distributed optimization capabilities:
- Distributed JIT compilation
- Shared specialization cache
- Distributed genetic algorithm
- Multi-worker optimization
"""

import numpy as np
import time
from python_optimizer import optimize
from python_optimizer.distributed import (
    BackendType,
    DistributedCoordinator,
    DistributedGeneticOptimizer,
    get_backend,
    get_distributed_jit_cache,
    get_distributed_spec_cache,
    set_backend,
)
from python_optimizer.genetic import ParameterRange


def example_1_basic_distributed():
    """Basic distributed computation example."""
    print("=" * 60)
    print("Example 1: Basic Distributed Computation")
    print("=" * 60)
    
    # Set up multiprocessing backend with 4 workers
    backend = set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    print(f"Initialized backend with {backend.num_workers()} workers\n")
    
    # Create coordinator
    coordinator = DistributedCoordinator()
    
    # Expensive computation to distribute
    def expensive_computation(x):
        """Simulate expensive computation."""
        result = 0
        for i in range(1000):
            result += x ** 2 + np.sin(x * i) * np.cos(x * i)
        return result
    
    # Data to process
    data = list(range(100))
    
    # Sequential execution for comparison
    print("Running sequential execution...")
    start = time.perf_counter()
    sequential_results = [expensive_computation(x) for x in data]
    sequential_time = time.perf_counter() - start
    print(f"Sequential time: {sequential_time:.3f}s\n")
    
    # Distributed execution
    print("Running distributed execution...")
    start = time.perf_counter()
    distributed_results = coordinator.map(expensive_computation, data)
    distributed_time = time.perf_counter() - start
    print(f"Distributed time: {distributed_time:.3f}s")
    
    # Verify results match
    assert sequential_results == distributed_results, "Results don't match!"
    
    # Show speedup
    speedup = sequential_time / distributed_time
    print(f"Speedup: {speedup:.2f}x\n")
    
    # Show coordinator stats
    stats = coordinator.get_stats()
    print("Coordinator Statistics:")
    print(f"  Tasks completed: {stats['tasks_completed']}")
    print(f"  Throughput: {stats['throughput']:.1f} tasks/s")
    print(f"  Workers: {stats['num_workers']}")


def example_2_distributed_jit():
    """Distributed JIT compilation example."""
    print("\n" + "=" * 60)
    print("Example 2: Distributed JIT Compilation")
    print("=" * 60)
    
    # Get distributed JIT cache
    jit_cache = get_distributed_jit_cache()
    jit_cache.clear()  # Start fresh
    
    @optimize(jit=True)
    def fibonacci_jit(n):
        """Fibonacci with JIT compilation."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    # First compilation
    print("First call (compiling)...")
    start = time.perf_counter()
    result1 = fibonacci_jit(40)
    compile_time = time.perf_counter() - start
    print(f"Result: {result1}, Time: {compile_time:.4f}s")
    
    # Subsequent calls use cached compilation
    print("\nSubsequent calls (cached)...")
    start = time.perf_counter()
    result2 = fibonacci_jit(40)
    cached_time = time.perf_counter() - start
    print(f"Result: {result2}, Time: {cached_time:.4f}s")
    
    speedup = compile_time / cached_time
    print(f"Speedup from caching: {speedup:.1f}x\n")
    
    # Show cache stats
    cache_stats = jit_cache.get_stats()
    print("JIT Cache Statistics:")
    print(f"  Hits: {cache_stats['hits']}")
    print(f"  Misses: {cache_stats['misses']}")
    print(f"  Hit rate: {cache_stats['hit_rate']:.1%}")
    print(f"  Cache size: {cache_stats['cache_size']}")


def example_3_distributed_specialization():
    """Distributed specialization cache example."""
    print("\n" + "=" * 60)
    print("Example 3: Distributed Specialization Cache")
    print("=" * 60)
    
    # Get distributed specialization cache
    spec_cache = get_distributed_spec_cache()
    spec_cache.clear()  # Start fresh
    
    @optimize(specialize=True, jit=False)
    def polymorphic_function(data):
        """Function that handles multiple types."""
        if isinstance(data, list):
            return sum(x ** 2 for x in data)
        elif isinstance(data, np.ndarray):
            return np.sum(data ** 2)
        elif isinstance(data, tuple):
            return sum(x ** 2 for x in data)
        else:
            return data ** 2
    
    # Process different types
    test_data = [
        [1, 2, 3, 4, 5] * 100,           # List
        np.array([1, 2, 3, 4, 5] * 100),  # NumPy array
        tuple([1, 2, 3, 4, 5] * 100),     # Tuple
        42,                               # Scalar
    ]
    
    print("Processing different data types...")
    for i, data in enumerate(test_data):
        data_type = type(data).__name__
        
        # Warmup calls
        for _ in range(5):
            _ = polymorphic_function(data)
        
        # Timed calls
        start = time.perf_counter()
        for _ in range(100):
            result = polymorphic_function(data)
        elapsed = time.perf_counter() - start
        
        print(f"  {data_type:15s}: {elapsed:.4f}s, Result: {result}")
    
    # Show cache stats
    cache_stats = spec_cache.get_stats()
    print("\nSpecialization Cache Statistics:")
    print(f"  Hits: {cache_stats['hits']}")
    print(f"  Misses: {cache_stats['misses']}")
    print(f"  Hit rate: {cache_stats['hit_rate']:.1%}")
    print(f"  Cache size: {cache_stats['cache_size']}")
    print(f"  Specializations created: {cache_stats['specializations_created']}")


def example_4_distributed_genetic():
    """Distributed genetic algorithm example."""
    print("\n" + "=" * 60)
    print("Example 4: Distributed Genetic Algorithm")
    print("=" * 60)
    
    # Set up backend
    set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    
    # Define optimization problem: minimize Rosenbrock function
    def fitness_function(params):
        """Rosenbrock function (minimize)."""
        x = params["x"]
        y = params["y"]
        return -((1 - x) ** 2 + 100 * (y - x ** 2) ** 2)  # Negative for maximization
    
    # Parameter ranges
    param_ranges = [
        ParameterRange("x", -5.0, 5.0, "float"),
        ParameterRange("y", -5.0, 5.0, "float"),
    ]
    
    # Create distributed optimizer
    optimizer = DistributedGeneticOptimizer(
        parameter_ranges=param_ranges,
        population_size=100,
        mutation_rate=0.1,
        crossover_rate=0.7,
        elitism_count=5,
        num_workers=4,
    )
    
    # Run optimization
    print("Running distributed genetic algorithm...")
    print(f"Population size: 100")
    print(f"Generations: 50")
    print(f"Workers: 4\n")
    
    start = time.perf_counter()
    best = optimizer.optimize(
        fitness_function=fitness_function,
        generations=50,
        verbose=False,
    )
    elapsed = time.perf_counter() - start
    
    print(f"\nOptimization completed in {elapsed:.2f}s")
    print(f"Best solution found:")
    print(f"  x = {best.parameters['x']:.6f}")
    print(f"  y = {best.parameters['y']:.6f}")
    print(f"  Fitness = {best.fitness:.6f}")
    print(f"  (Optimal is x=1, y=1, fitness=0)")
    
    # Show distributed stats
    stats = optimizer.get_distributed_stats()
    print("\nDistributed Statistics:")
    print(f"  Total evaluations: {stats['total_evaluations']}")
    print(f"  Throughput: {stats['throughput']:.1f} evals/s")
    print(f"  Backend: {stats['backend']}")


def example_5_map_reduce():
    """Map-reduce pattern example."""
    print("\n" + "=" * 60)
    print("Example 5: Map-Reduce Pattern")
    print("=" * 60)
    
    # Set up backend
    set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    coordinator = DistributedCoordinator()
    
    # Large dataset
    data = list(range(1, 1001))
    
    print(f"Computing sum of squares for {len(data)} numbers...")
    
    # Map function: compute square
    def square(x):
        return x ** 2
    
    # Reduce function: sum
    def add(a, b):
        return a + b
    
    # Execute map-reduce
    start = time.perf_counter()
    result = coordinator.reduce(
        func=square,
        items=data,
        reducer=add,
        initial=0,
    )
    elapsed = time.perf_counter() - start
    
    print(f"Result: {result}")
    print(f"Time: {elapsed:.4f}s")
    print(f"(Expected: {sum(x**2 for x in data)})")
    
    # Show stats
    stats = coordinator.get_stats()
    print(f"\nThroughput: {stats['throughput']:.1f} items/s")


def main():
    """Run all distributed computing examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Distributed Computing Examples" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        example_1_basic_distributed()
        example_2_distributed_jit()
        example_3_distributed_specialization()
        example_4_distributed_genetic()
        example_5_map_reduce()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
