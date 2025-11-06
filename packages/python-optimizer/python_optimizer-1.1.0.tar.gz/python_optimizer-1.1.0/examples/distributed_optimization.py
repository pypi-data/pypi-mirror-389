"""
Distributed Computing Examples

This module demonstrates distributed computing capabilities of
Python Optimizer.
"""

import multiprocessing as mp
import time
from typing import Any, Dict

import numpy as np

from python_optimizer.distributed import (
    BackendType,
    DistributedCoordinator,
    DistributedGeneticOptimizer,
    get_backend,
    set_backend,
)
from python_optimizer.genetic import ParameterRange

# =============================================================================
# Example 1: Basic Distributed Map
# =============================================================================


def example_1_basic_map():
    """Demonstrate basic distributed map operation."""
    print("=" * 80)
    print("Example 1: Basic Distributed Map")
    print("=" * 80)

    # Setup multiprocessing backend
    set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    coordinator = DistributedCoordinator()

    # Define expensive function
    def expensive_computation(x: int) -> float:
        # Simulate expensive computation
        time.sleep(0.01)
        return x**2 + np.sin(x)

    # Distribute computation
    items = list(range(100))

    print(f"Processing {len(items)} items with 4 workers...")
    start_time = time.time()
    results = coordinator.map(expensive_computation, items)
    elapsed = time.time() - start_time

    print(f"Completed in {elapsed:.2f}s")
    print(f"First 10 results: {results[:10]}")

    # Compare with sequential
    print("\nComparing with sequential execution...")
    start_time = time.time()
    _ = [expensive_computation(x) for x in items]  # noqa: F841
    seq_elapsed = time.time() - start_time

    print(f"Sequential time: {seq_elapsed:.2f}s")
    print(f"Speedup: {seq_elapsed / elapsed:.2f}x")

    # Get statistics
    stats = coordinator.get_stats()
    print("\nCoordinator Statistics:")
    print(f"  Tasks completed: {stats['tasks_completed']}")
    print(f"  Throughput: {stats['throughput']:.1f} tasks/s")
    print(f"  Workers: {stats['num_workers']}")

    print()


# =============================================================================
# Example 2: Map-Reduce Pattern
# =============================================================================


def example_2_map_reduce():
    """Demonstrate map-reduce pattern for aggregation."""
    print("=" * 80)
    print("Example 2: Map-Reduce Pattern")
    print("=" * 80)

    set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    coordinator = DistributedCoordinator()

    # Calculate sum of squares using map-reduce
    numbers = list(range(1, 1001))

    result = coordinator.reduce(
        func=lambda x: x**2,  # Map: square each number
        items=numbers,
        reducer=lambda a, b: a + b,  # Reduce: sum results
        initial=0,
    )

    print(f"Sum of squares from 1 to 1000: {result}")
    print(f"Expected: {sum(x**2 for x in numbers)}")
    print(f"Match: {result == sum(x**2 for x in numbers)}")

    # Calculate product using map-reduce
    numbers = list(range(1, 11))
    result = coordinator.reduce(
        func=lambda x: x,  # Map: identity
        items=numbers,
        reducer=lambda a, b: a * b,  # Reduce: multiply
        initial=1,
    )

    print(f"\nFactorial of 10: {result}")
    print(f"Expected: {np.math.factorial(10)}")

    print()


# =============================================================================
# Example 3: Batch Task Submission
# =============================================================================


def example_3_batch_submission():
    """Demonstrate batch task submission with different arguments."""
    print("=" * 80)
    print("Example 3: Batch Task Submission")
    print("=" * 80)

    set_backend(BackendType.MULTIPROCESSING, num_workers=4)
    coordinator = DistributedCoordinator()

    # Define function with multiple arguments
    def train_model(config: Dict[str, Any], epochs: int) -> float:
        """Simulate model training."""
        # Simulate training time
        time.sleep(0.05)
        # Simulate validation accuracy based on hyperparameters
        lr = config.get("learning_rate", 0.01)
        batch_size = config.get("batch_size", 32)
        accuracy = 0.5 + 0.3 * (1 - abs(lr - 0.001)) + 0.1 * (batch_size / 128)
        accuracy += np.random.normal(0, 0.02)  # Add noise
        return min(max(accuracy, 0), 1)

    # Create batch of different configurations
    configs = [
        {"learning_rate": 0.001, "batch_size": 32},
        {"learning_rate": 0.01, "batch_size": 64},
        {"learning_rate": 0.1, "batch_size": 128},
        {"learning_rate": 0.0001, "batch_size": 16},
    ]

    args_list = [(config, 10) for config in configs]

    print(f"Training {len(configs)} models with different configurations...")
    results = coordinator.submit_batch(train_model, args_list)

    print("\nResults:")
    for i, (config, accuracy) in enumerate(zip(configs, results)):
        print(
            f"  Config {i+1}: lr={config['learning_rate']}, "
            f"batch_size={config['batch_size']} -> Accuracy: {accuracy:.4f}"
        )

    best_idx = np.argmax(results)
    print(f"\nBest configuration: {configs[best_idx]}")
    print(f"Best accuracy: {results[best_idx]:.4f}")

    print()


# =============================================================================
# Example 4: Distributed Genetic Algorithm - Simple Optimization
# =============================================================================


def example_4_simple_genetic():
    """Demonstrate distributed genetic algorithm for simple optimization."""
    print("=" * 80)
    print("Example 4: Distributed Genetic Algorithm - Simple Optimization")
    print("=" * 80)

    # Setup backend
    set_backend(BackendType.MULTIPROCESSING, num_workers=4)

    # Define optimization problem: minimize f(x, y) = x^2 + y^2
    param_ranges = [
        ParameterRange("x", -10.0, 10.0, "float"),
        ParameterRange("y", -10.0, 10.0, "float"),
    ]

    def fitness_function(params: Dict[str, float]) -> float:
        """Fitness function to maximize (negative of objective)."""
        x, y = params["x"], params["y"]
        # Maximize negative of squared distance from origin
        return -(x**2 + y**2)

    # Create distributed optimizer
    optimizer = DistributedGeneticOptimizer(
        parameter_ranges=param_ranges,
        population_size=100,
        num_workers=4,
        mutation_rate=0.1,
        crossover_rate=0.7,
    )

    print("Running distributed genetic optimization...")
    print("Population size: 100")
    print("Workers: 4")
    print("Target: Find minimum of f(x,y) = x^2 + y^2")

    best = optimizer.optimize(
        fitness_function=fitness_function, generations=50, verbose=True
    )

    print("\nOptimization complete!")
    x_val = best.parameters["x"]
    y_val = best.parameters["y"]
    print(f"Best solution: x={x_val:.6f}, y={y_val:.6f}")
    print(f"Best fitness: {best.fitness:.6f}")
    dist = np.sqrt(x_val**2 + y_val**2)
    print(f"Distance from origin: {dist:.6f}")

    # Get distributed statistics
    stats = optimizer.get_distributed_stats()
    print("\nDistributed Statistics:")
    print(f"  Total evaluations: {stats['total_evaluations']}")
    print(f"  Throughput: {stats['throughput']:.1f} evals/s")
    print(f"  Workers: {stats['num_workers']}")

    print()


# =============================================================================
# Example 5: Distributed Genetic Algorithm - Hyperparameter Tuning
# =============================================================================


def example_5_hyperparameter_tuning():
    """Demonstrate distributed hyperparameter optimization."""
    print("=" * 80)
    print("Example 5: Distributed Hyperparameter Tuning")
    print("=" * 80)

    set_backend(BackendType.MULTIPROCESSING, num_workers=mp.cpu_count())

    # Define hyperparameter search space
    param_ranges = [
        ParameterRange("learning_rate", 1e-4, 1e-1, "float"),
        ParameterRange("batch_size", 16, 128, "int"),
        ParameterRange("hidden_dim", 64, 256, "int"),
        ParameterRange("dropout", 0.0, 0.5, "float"),
    ]

    def simulate_training(params: Dict[str, Any]) -> float:
        """Simulate model training and return validation accuracy."""
        # Simulate training time
        time.sleep(0.1)

        # Simulate accuracy based on hyperparameters
        lr = params["learning_rate"]
        batch_size = params["batch_size"]
        hidden_dim = params["hidden_dim"]
        dropout = params["dropout"]

        # Optimal values (unknown to optimizer)
        optimal_lr = 0.001
        optimal_batch = 64
        optimal_hidden = 128
        optimal_dropout = 0.2

        # Calculate "accuracy" based on distance from optimal
        lr_score = 1 - min(abs(np.log10(lr) - np.log10(optimal_lr)) / 2, 1)
        batch_score = 1 - min(abs(batch_size - optimal_batch) / 100, 1)
        hidden_score = 1 - min(abs(hidden_dim - optimal_hidden) / 200, 1)
        dropout_score = 1 - min(abs(dropout - optimal_dropout) / 0.5, 1)

        accuracy = (
            0.5
            + 0.3 * lr_score
            + 0.1 * batch_score
            + 0.05 * hidden_score
            + 0.05 * dropout_score
        )

        # Add noise
        accuracy += np.random.normal(0, 0.01)
        return min(max(accuracy, 0), 1)

    # Create distributed optimizer
    num_workers = mp.cpu_count()
    optimizer = DistributedGeneticOptimizer(
        parameter_ranges=param_ranges,
        population_size=50,
        num_workers=num_workers,
        mutation_rate=0.15,
        crossover_rate=0.8,
    )

    print("Running distributed hyperparameter optimization...")
    print("Population size: 50")
    print(f"Workers: {num_workers}")
    print("Search space: learning_rate, batch_size, hidden_dim, dropout")

    best = optimizer.optimize(
        fitness_function=simulate_training, generations=30, verbose=True
    )

    print("\nOptimization complete!")
    print("Best hyperparameters:")
    print(f"  Learning rate: {best.parameters['learning_rate']:.6f}")
    print(f"  Batch size: {best.parameters['batch_size']}")
    print(f"  Hidden dim: {best.parameters['hidden_dim']}")
    print(f"  Dropout: {best.parameters['dropout']:.4f}")
    print(f"Best validation accuracy: {best.fitness:.4f}")

    # Get statistics
    stats = optimizer.get_distributed_stats()
    print("\nDistributed Statistics:")
    print(f"  Total evaluations: {stats['total_evaluations']}")
    print(f"  Throughput: {stats['throughput']:.1f} evals/s")

    print()


# =============================================================================
# Example 6: Performance Comparison
# =============================================================================


def example_6_performance_comparison():
    """Compare sequential vs distributed performance."""
    print("=" * 80)
    print("Example 6: Performance Comparison")
    print("=" * 80)

    # Define expensive fitness function
    def expensive_fitness(params: Dict[str, float]) -> float:
        """Expensive fitness function."""
        time.sleep(0.05)  # Simulate expensive computation
        x = params["x"]
        return -(x**2)

    param_ranges = [ParameterRange("x", -10.0, 10.0, "float")]

    population_size = 100
    generations = 20

    # Sequential genetic algorithm
    print("Running sequential genetic algorithm...")
    from python_optimizer.genetic import GeneticOptimizer

    seq_optimizer = GeneticOptimizer(
        parameter_ranges=param_ranges, population_size=population_size
    )

    seq_start = time.time()
    seq_best = seq_optimizer.optimize(
        fitness_function=expensive_fitness,
        generations=generations,
        verbose=False,
    )
    seq_time = time.time() - seq_start

    print(f"Sequential time: {seq_time:.2f}s")
    print(f"Sequential best fitness: {seq_best.fitness:.6f}")

    # Distributed genetic algorithm
    print("\nRunning distributed genetic algorithm...")
    num_workers = 4
    set_backend(BackendType.MULTIPROCESSING, num_workers=num_workers)

    dist_optimizer = DistributedGeneticOptimizer(
        parameter_ranges=param_ranges,
        population_size=population_size,
        num_workers=num_workers,
    )

    dist_start = time.time()
    dist_best = dist_optimizer.optimize(
        fitness_function=expensive_fitness,
        generations=generations,
        verbose=False,
    )
    dist_time = time.time() - dist_start

    print(f"Distributed time: {dist_time:.2f}s")
    print(f"Distributed best fitness: {dist_best.fitness:.6f}")

    # Calculate speedup
    speedup = seq_time / dist_time
    efficiency = speedup / num_workers

    separator = "=" * 40
    print(f"\n{separator}")
    print("Performance Summary:")
    print(separator)
    print(f"Sequential time:   {seq_time:.2f}s")
    print(f"Distributed time:  {dist_time:.2f}s")
    print(f"Speedup:           {speedup:.2f}x")
    print(f"Workers:           {num_workers}")
    print(f"Efficiency:        {efficiency:.2%}")
    print(separator)

    print()


# =============================================================================
# Example 7: Backend Comparison
# =============================================================================


def example_7_backend_info():
    """Display information about available backends."""
    print("=" * 80)
    print("Example 7: Backend Information")
    print("=" * 80)

    # Check multiprocessing
    print("Multiprocessing Backend:")
    try:
        backend = set_backend(BackendType.MULTIPROCESSING, num_workers=4)
        print("  Status: Available")
        print(f"  Workers: {backend.num_workers()}")
        print("  Best for: Local multi-core execution")
    except Exception as e:
        print(f"  Status: Not available ({e})")

    # Check Ray
    print("\nRay Backend:")
    try:
        from python_optimizer.distributed.backend import RAY_AVAILABLE

        if RAY_AVAILABLE:
            print("  Status: Available (not initialized)")
            print("  Best for: Multi-node clusters")
            print("  Note: Install with 'pip install ray'")
        else:
            print("  Status: Not installed")
            print("  Install: pip install ray")
    except Exception as e:
        print(f"  Status: Error ({e})")

    # Check Dask
    print("\nDask Backend:")
    try:
        from python_optimizer.distributed.backend import DASK_AVAILABLE

        if DASK_AVAILABLE:
            print("  Status: Available (not initialized)")
            print("  Best for: Dask ecosystem integration")
            msg = "  Note: Install with 'pip install dask distributed'"
            print(msg)
        else:
            print("  Status: Not installed")
            print("  Install: pip install dask distributed")
    except Exception as e:
        print(f"  Status: Error ({e})")

    # Current backend
    try:
        backend = get_backend()
        print(f"\nCurrent Backend: {type(backend).__name__}")
    except Exception as e:
        print(f"\nCurrent Backend: None ({e})")

    print()


# =============================================================================
# Main
# =============================================================================


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("Python Optimizer - Distributed Computing Examples")
    print("=" * 80)
    print()

    # Run examples
    example_1_basic_map()
    example_2_map_reduce()
    example_3_batch_submission()
    example_4_simple_genetic()
    example_5_hyperparameter_tuning()
    example_6_performance_comparison()
    example_7_backend_info()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
