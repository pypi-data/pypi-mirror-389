"""Distributed Genetic Algorithm Optimizer

Extends GeneticOptimizer for distributed population evaluation.
Distributes fitness evaluation across multiple workers for massive speedup.
"""

import logging
from typing import Callable, List, Optional

from python_optimizer.distributed.backend import get_backend
from python_optimizer.distributed.coordinator import DistributedCoordinator
from python_optimizer.genetic import Individual, ParameterRange
import random

logger = logging.getLogger(__name__)


class DistributedGeneticOptimizer:
    """Distributed genetic algorithm optimizer.

    Extends GeneticOptimizer to distribute fitness evaluation across workers.
    Provides massive speedup for expensive fitness functions.

    Features:
    - Distributed fitness evaluation
    - Parallel population processing
    - Automatic load balancing
    - Fault tolerance
    - Progress tracking
    """

    def __init__(
        self,
        parameter_ranges: List[ParameterRange],
        population_size: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elitism_count: int = 2,
        num_workers: Optional[int] = None,
        backend: str = "multiprocessing",
    ):
        """Initialize distributed genetic optimizer.

        Args:
            parameter_ranges: List of parameter ranges to optimize
            population_size: Size of population
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            elitism_count: Number of elite individuals to preserve
            num_workers: Number of workers (None for auto)
            backend: Backend to use ('multiprocessing', 'ray', 'dask')
        """
        self.parameter_ranges = parameter_ranges
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_count = elitism_count
        self.population = []
        self.best_individual = None
        self._random = random.Random()

        self.num_workers = num_workers
        self.backend = backend
        self.coordinator = DistributedCoordinator()

        # Statistics
        self.distributed_stats = {
            "total_evaluations": 0,
            "distributed_evaluations": 0,
            "speedup": 0.0,
        }

    def evaluate_population(
        self, population: List[Individual], fitness_function: Callable
    ) -> List[float]:
        """Evaluate fitness of entire population in parallel.

        Args:
            population: List of individuals
            fitness_function: Function to evaluate fitness

        Returns:
            List of fitness scores
        """
        # Extract parameters from population
        param_sets = [ind.parameters for ind in population]

        # Distribute fitness evaluation across workers
        logger.info(
            f"Distributing {len(param_sets)} fitness evaluations "
            f"across {get_backend().num_workers()} workers"
        )

        # Use coordinator to map fitness function over population
        fitness_scores = self.coordinator.map(fitness_function, param_sets)

        # Update statistics
        self.distributed_stats["total_evaluations"] += len(population)
        self.distributed_stats["distributed_evaluations"] += len(population)

        return fitness_scores

    def _initialize_population(self):
        """Initialize random population."""
        self.population = []
        for _ in range(self.population_size):
            ind = Individual()
            ind.parameters = {}
            for param_range in self.parameter_ranges:
                if param_range.param_type == "float":
                    ind.parameters[param_range.name] = self._random.uniform(
                        param_range.min_val, param_range.max_val
                    )
                elif param_range.param_type == "int":
                    ind.parameters[param_range.name] = self._random.randint(
                        int(param_range.min_val), int(param_range.max_val)
                    )
            ind.fitness = None
            self.population.append(ind)

    def _tournament_selection(self, tournament_size=3):
        """Select individual using tournament selection."""
        tournament = self._random.sample(
            self.population, min(tournament_size, len(self.population))
        )
        return max(tournament, key=lambda x: x.fitness if x.fitness else float("-inf"))

    def _crossover(self, parent1, parent2):
        """Create two children via crossover."""
        child1, child2 = Individual(), Individual()
        child1.parameters, child2.parameters = {}, {}
        
        for param_range in self.parameter_ranges:
            name = param_range.name
            if self._random.random() < 0.5:
                child1.parameters[name] = parent1.parameters[name]
                child2.parameters[name] = parent2.parameters[name]
            else:
                child1.parameters[name] = parent2.parameters[name]
                child2.parameters[name] = parent1.parameters[name]
        
        child1.fitness = None
        child2.fitness = None
        return child1, child2

    def _mutate(self, individual):
        """Mutate individual."""
        mutated = Individual()
        mutated.parameters = individual.parameters.copy()
        
        for param_range in self.parameter_ranges:
            if self._random.random() < self.mutation_rate:
                name = param_range.name
                if param_range.param_type == "float":
                    mutated.parameters[name] = self._random.uniform(
                        param_range.min_val, param_range.max_val
                    )
                elif param_range.param_type == "int":
                    mutated.parameters[name] = self._random.randint(
                        int(param_range.min_val), int(param_range.max_val)
                    )
        
        mutated.fitness = None
        return mutated

    def optimize(
        self,
        fitness_function: Callable,
        generations: int = 100,
        target_fitness: Optional[float] = None,
        verbose: bool = True,
    ) -> Individual:
        """Run distributed genetic algorithm optimization.

        Args:
            fitness_function: Function to maximize
            generations: Number of generations
            target_fitness: Stop if this fitness is reached
            verbose: Print progress

        Returns:
            Best individual found

        Example:
            optimizer = DistributedGeneticOptimizer(
                parameter_ranges,
                population_size=1000,
                num_workers=8
            )
            best = optimizer.optimize(fitness_fn, generations=100)
        """
        # Initialize population
        self._initialize_population()

        # Evaluate initial population (distributed)
        fitness_scores = self.evaluate_population(self.population, fitness_function)

        # Assign fitness scores
        for ind, score in zip(self.population, fitness_scores):
            ind.fitness = score

        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        self.best_individual = self.population[0]

        if verbose:
            print(f"Generation 0: Best fitness = {self.best_individual.fitness:.6f}")

        # Evolution loop
        for gen in range(1, generations + 1):
            # Create new population through selection, crossover, mutation
            new_population = []

            # Elitism - preserve best individuals
            new_population.extend(self.population[: self.elitism_count])

            # Generate rest of population
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self._tournament_selection()
                parent2 = self._tournament_selection()

                # Crossover
                if self._random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2

                # Mutation
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)

                new_population.extend([child1, child2])

            # Trim to population size
            new_population = new_population[: self.population_size]

            # Evaluate new population (distributed)
            fitness_scores = self.evaluate_population(new_population, fitness_function)

            # Assign fitness scores
            for ind, score in zip(new_population, fitness_scores):
                ind.fitness = score

            # Sort and update
            new_population.sort(key=lambda x: x.fitness, reverse=True)
            self.population = new_population

            if new_population[0].fitness > self.best_individual.fitness:
                self.best_individual = new_population[0]

            if verbose and gen % 10 == 0:
                stats = self.coordinator.get_stats()
                print(
                    f"Generation {gen}: Best fitness = {self.best_individual.fitness:.6f}, "
                    f"Throughput = {stats['throughput']:.1f} evals/s"
                )

            # Check target fitness
            if target_fitness and self.best_individual.fitness >= target_fitness:
                if verbose:
                    print(
                        f"Target fitness {target_fitness} reached at generation {gen}"
                    )
                break

        return self.best_individual

    def get_distributed_stats(self):
        """Get distributed optimization statistics.

        Returns:
            Dictionary with distributed statistics
        """
        coordinator_stats = self.coordinator.get_stats()
        return {
            **self.distributed_stats,
            **coordinator_stats,
            "backend": self.backend,
        }


def optimize_genetic_distributed(
    fitness_function: Callable,
    parameter_ranges: List[ParameterRange],
    population_size: int = 100,
    generations: int = 100,
    num_workers: Optional[int] = None,
    backend: str = "multiprocessing",
    **kwargs,
) -> Individual:
    """Convenience function for distributed genetic optimization.

    Args:
        fitness_function: Function to maximize
        parameter_ranges: List of parameter ranges
        population_size: Size of population
        generations: Number of generations
        num_workers: Number of workers
        backend: Backend to use
        **kwargs: Additional arguments for optimizer

    Returns:
        Best individual found

    Example:
        best = optimize_genetic_distributed(
            fitness_fn,
            parameter_ranges,
            population_size=1000,
            generations=100,
            num_workers=8
        )
    """
    optimizer = DistributedGeneticOptimizer(
        parameter_ranges=parameter_ranges,
        population_size=population_size,
        num_workers=num_workers,
        backend=backend,
        **kwargs,
    )

    return optimizer.optimize(
        fitness_function=fitness_function, generations=generations
    )
