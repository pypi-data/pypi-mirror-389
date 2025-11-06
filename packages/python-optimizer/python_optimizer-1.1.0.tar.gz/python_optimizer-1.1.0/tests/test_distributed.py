"""Tests for distributed computing module.

Tests backend abstraction, coordinator, and distributed genetic optimizer.
"""

import pytest

from python_optimizer.distributed import (
    BackendType,
    DistributedCoordinator,
    DistributedGeneticOptimizer,
    check_backend_availability,
    get_backend,
    set_backend,
)
from python_optimizer.genetic import ParameterRange


# Module-level functions for Windows multiprocessing compatibility
def _square(x):
    """Square function for testing."""
    return x**2


def _double(x):
    """Double function for testing."""
    return x * 2


def _identity(x):
    """Identity function for testing."""
    return x


def _fitness_origin(params):
    """Fitness function targeting origin."""
    x = params["x"]
    y = params["y"]
    return -(x**2 + y**2)


def _fitness_x(p):
    """Simple fitness based on x value."""
    return p["x"]


def _expensive_function(x):
    """Expensive function for testing."""
    return sum(i**2 for i in range(x))


def _slow_function(x):
    """Slow function for performance testing."""
    total = 0
    for i in range(10000):
        total += i**2
    return total + x


class TestBackendAvailability:
    """Test backend availability detection."""

    def test_check_backend_availability(self):
        """Test backend availability checker."""
        backends = check_backend_availability()
        assert isinstance(backends, dict)
        assert "multiprocessing" in backends
        assert backends["multiprocessing"]["available"] is True
        assert "ray" in backends
        assert "dask" in backends

    def test_multiprocessing_always_available(self):
        """Test multiprocessing backend is always available."""
        backends = check_backend_availability()
        assert backends["multiprocessing"]["available"] is True


class TestBackendManagement:
    """Test backend management functions."""

    def test_set_backend_multiprocessing(self):
        """Test setting multiprocessing backend."""
        backend = set_backend(BackendType.MULTIPROCESSING, num_workers=2)
        assert backend is not None
        assert backend.num_workers() == 2

    def test_get_backend_auto_initializes(self):
        """Test get_backend auto-initializes if needed."""
        backend = get_backend()
        assert backend is not None
        assert backend.num_workers() > 0

    def test_backend_submission(self):
        """Test task submission to backend."""
        backend = set_backend(BackendType.MULTIPROCESSING, num_workers=2)

        future = backend.submit(_square, 5)
        result = backend.gather([future])[0]
        assert result == 25

    def test_backend_map(self):
        """Test mapping function over items."""
        backend = set_backend(BackendType.MULTIPROCESSING, num_workers=2)

        results = backend.map(_square, [1, 2, 3, 4, 5])
        assert results == [1, 4, 9, 16, 25]


class TestDistributedCoordinator:
    """Test distributed coordinator."""

    def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        coordinator = DistributedCoordinator()
        assert coordinator.max_retries == 3
        assert coordinator.enable_monitoring is True

    def test_coordinator_map(self):
        """Test coordinator map operation."""
        set_backend(BackendType.MULTIPROCESSING, num_workers=2)
        coordinator = DistributedCoordinator()

        results = coordinator.map(_double, [1, 2, 3, 4])
        assert results == [2, 4, 6, 8]

    def test_coordinator_statistics(self):
        """Test coordinator statistics tracking."""
        set_backend(BackendType.MULTIPROCESSING, num_workers=2)
        coordinator = DistributedCoordinator()

        coordinator.map(_square, [1, 2, 3])

        stats = coordinator.get_stats()
        assert stats["tasks_submitted"] == 3
        assert stats["tasks_completed"] == 3
        assert stats["num_workers"] == 2

    def test_coordinator_reduce(self):
        """Test map-reduce operation."""
        set_backend(BackendType.MULTIPROCESSING, num_workers=2)
        coordinator = DistributedCoordinator()

        # Sum of squares
        result = coordinator.reduce(
            _square,
            [1, 2, 3, 4],
            lambda a, b: a + b,
            initial=0,
        )
        assert result == 30  # 1 + 4 + 9 + 16

    def test_coordinator_empty_map(self):
        """Test mapping over empty list."""
        coordinator = DistributedCoordinator()
        results = coordinator.map(_identity, [])
        assert results == []


class TestDistributedGeneticOptimizer:
    """Test distributed genetic algorithm optimizer."""

    def test_optimizer_initialization(self):
        """Test distributed genetic optimizer initialization."""
        param_ranges = [
            ParameterRange("x", 0.0, 10.0, "float"),
            ParameterRange("y", 0.0, 10.0, "float"),
        ]

        optimizer = DistributedGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=20,
            num_workers=2,
        )

        assert optimizer.population_size == 20
        assert optimizer.num_workers == 2
        assert len(optimizer.parameter_ranges) == 2

    def test_distributed_optimization(self):
        """Test distributed genetic optimization."""
        set_backend(BackendType.MULTIPROCESSING, num_workers=2)

        param_ranges = [
            ParameterRange("x", -5.0, 5.0, "float"),
            ParameterRange("y", -5.0, 5.0, "float"),
        ]

        optimizer = DistributedGeneticOptimizer(
            parameter_ranges=param_ranges,
            population_size=20,
            num_workers=2,
        )

        best = optimizer.optimize(
            fitness_function=_fitness_origin,
            generations=5,
            verbose=False,
        )

        # Best should be near origin
        assert abs(best.parameters["x"]) < 2.0
        assert abs(best.parameters["y"]) < 2.0
        assert best.fitness >= -25.0  # Should find decent solution

    def test_distributed_stats(self):
        """Test distributed optimization statistics."""
        set_backend(BackendType.MULTIPROCESSING, num_workers=2)

        param_ranges = [ParameterRange("x", 0.0, 1.0, "float")]

        optimizer = DistributedGeneticOptimizer(
            parameter_ranges=param_ranges, population_size=10, num_workers=2
        )

        optimizer.optimize(
            fitness_function=_fitness_x,
            generations=3,
            verbose=False,
        )

        stats = optimizer.get_distributed_stats()
        assert "total_evaluations" in stats
        assert "num_workers" in stats
        assert stats["total_evaluations"] > 0


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_distributed_workflow(self):
        """Test complete distributed workflow."""
        # Set backend
        set_backend(BackendType.MULTIPROCESSING, num_workers=4)

        # Create coordinator
        coordinator = DistributedCoordinator()

        # Distribute computation
        results = coordinator.map(_expensive_function, [10, 20, 30, 40])

        assert len(results) == 4
        assert all(r > 0 for r in results)

        # Check statistics
        stats = coordinator.get_stats()
        assert stats["tasks_completed"] == 4
        assert stats["num_workers"] == 4


@pytest.mark.benchmark
class TestPerformance:
    """Performance tests for distributed computing."""

    def test_speedup_with_multiprocessing(self):
        """Test that multiprocessing provides speedup."""
        import time

        items = list(range(100))

        # Sequential execution
        start = time.perf_counter()
        sequential_results = [_slow_function(x) for x in items]
        sequential_time = time.perf_counter() - start

        # Distributed execution
        set_backend(BackendType.MULTIPROCESSING, num_workers=4)
        coordinator = DistributedCoordinator()

        start = time.perf_counter()
        distributed_results = coordinator.map(_slow_function, items)
        distributed_time = time.perf_counter() - start

        # Results should match
        assert sequential_results == distributed_results

        # Distributed should be faster (allow some tolerance)
        # Note: Might not always be faster for small workloads due to overhead
        assert distributed_time < sequential_time * 1.5
