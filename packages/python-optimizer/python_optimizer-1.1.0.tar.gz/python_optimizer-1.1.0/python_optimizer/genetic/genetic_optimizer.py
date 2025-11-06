"""
Genetic Algorithm Engine for Trading Strategy Optimization
Uses genetic algorithms to optimize strategy parameters and indicators
"""

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ParameterRange:
    """Defines a parameter range for optimization"""

    name: str
    min_val: float
    max_val: float
    param_type: str = "float"  # 'float', 'int', 'bool'
    step: Optional[float] = None

    def generate_random(self):
        """Generate a random value within the range"""
        if self.param_type == "int":
            return random.randint(int(self.min_val), int(self.max_val))
        elif self.param_type == "bool":
            return random.choice([True, False])
        else:  # float
            if self.step:
                steps = int((self.max_val - self.min_val) / self.step)
                return self.min_val + random.randint(0, steps) * self.step
            return random.uniform(self.min_val, self.max_val)


@dataclass
class Individual:
    """Represents an individual in the genetic algorithm"""

    genes: Dict[str, Any] = field(default_factory=dict)
    fitness: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Results from genetic algorithm optimization"""

    best_individual: Individual
    generation_stats: List[Dict[str, float]]
    convergence_data: Dict[str, List[float]]
    optimization_time: float
    total_evaluations: int


class FitnessEvaluator(ABC):
    """Abstract base class for fitness evaluation"""

    @abstractmethod
    def evaluate(self, individual: Individual, data: pd.DataFrame) -> Dict[str, float]:
        pass


class BacktestFitnessEvaluator(FitnessEvaluator):
    """Evaluates fitness using backtesting results"""

    def __init__(
        self, strategy_class, initial_cash: float = 10000, commission: float = 0.001
    ):
        self.strategy_class = strategy_class
        self.initial_cash = initial_cash
        self.commission = commission

    def evaluate(self, individual: Individual, data: pd.DataFrame) -> Dict[str, float]:
        """Evaluate individual using backtesting"""
        try:
            import os
            import sys

            sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
            from src.backtesting.backtest_engine import BacktestEngine

            engine = BacktestEngine(
                initial_cash=self.initial_cash, commission=self.commission
            )

            engine.add_data(data)
            engine.add_strategy(self.strategy_class, **individual.genes)
            engine.setup_broker()

            results = engine.run_backtest()
            metrics = self._calculate_fitness_metrics(results)

            individual.fitness = self._calculate_composite_fitness(metrics)
            individual.metrics = metrics

            return metrics

        except Exception as e:
            logger.error(f"Error evaluating individual: {e}")
            individual.fitness = -1000
            individual.metrics = {"total_return": -100, "max_drawdown": 100}
            return individual.metrics

    def _calculate_fitness_metrics(self, results: Dict) -> Dict[str, float]:
        """Calculate comprehensive fitness metrics"""
        metrics = {}

        metrics["total_return"] = results.get("total_return", 0)
        metrics["sharpe_ratio"] = results.get("sharpe_ratio", 0) or 0
        metrics["max_drawdown"] = abs(results.get("max_drawdown", 0))

        trades = results.get("trades", {})
        if trades:
            total_trades = trades.get("total", {}).get("total", 0)
            won_trades = trades.get("won", {}).get("total", 0)

            metrics["total_trades"] = total_trades
            metrics["win_rate"] = (
                (won_trades / total_trades * 100) if total_trades > 0 else 0
            )

            total_profit = trades.get("won", {}).get("pnl", {}).get("total", 0)
            total_loss = abs(trades.get("lost", {}).get("pnl", {}).get("total", 0))
            metrics["profit_factor"] = (
                total_profit / total_loss if total_loss > 0 else 0
            )
        else:
            metrics.update({"total_trades": 0, "win_rate": 0, "profit_factor": 0})

        return metrics

    def _calculate_composite_fitness(self, metrics: Dict[str, float]) -> float:
        """Calculate composite fitness score"""
        return_score = metrics["total_return"] * 0.4
        sharpe_score = metrics["sharpe_ratio"] * 20 * 0.3
        drawdown_penalty = -metrics["max_drawdown"] * 0.2
        trade_bonus = min(metrics["total_trades"] / 10, 1) * 0.1

        return return_score + sharpe_score + drawdown_penalty + trade_bonus


class GeneticOptimizer:
    """Genetic Algorithm for Strategy Optimization"""

    def __init__(
        self,
        parameter_ranges: List[ParameterRange],
        fitness_evaluator: FitnessEvaluator,
        population_size: int = 30,
        generations: int = 15,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        elite_size: int = 3,
    ):

        self.parameter_ranges = {pr.name: pr for pr in parameter_ranges}
        self.fitness_evaluator = fitness_evaluator
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size

        self.population: List[Individual] = []
        self.generation_stats: List[Dict[str, float]] = []
        self.convergence_data: Dict[str, List[float]] = {
            "best_fitness": [],
            "avg_fitness": [],
        }

    def initialize_population(self) -> List[Individual]:
        """Initialize random population"""
        population = []

        for _ in range(self.population_size):
            individual = Individual()

            for param_name, param_range in self.parameter_ranges.items():
                individual.genes[param_name] = param_range.generate_random()

            population.append(individual)

        logger.info(f"Initialized population of {len(population)} individuals")
        return population

    def evaluate_population(
        self, population: List[Individual], data: pd.DataFrame
    ) -> List[Individual]:
        """Evaluate fitness for entire population"""
        logger.info(f"Evaluating population of {len(population)} individuals")

        for i, individual in enumerate(population):
            try:
                self.fitness_evaluator.evaluate(individual, data)
                if (i + 1) % 5 == 0:
                    logger.info(f"Evaluated {i+1}/{len(population)} individuals")
            except Exception as e:
                logger.error(f"Error evaluating individual {i}: {e}")
                individual.fitness = -1000

        return population

    def tournament_selection(
        self, population: List[Individual], tournament_size: int = 3
    ) -> Individual:
        """Tournament selection"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)

    def crossover(
        self, parent1: Individual, parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """Single-point crossover"""
        child1 = Individual()
        child2 = Individual()

        genes = list(self.parameter_ranges.keys())

        # Handle single-gene case
        if len(genes) <= 1:
            # Just copy genes directly (no crossover point possible)
            for gene in genes:
                child1.genes[gene] = parent1.genes[gene]
                child2.genes[gene] = parent2.genes[gene]
        else:
            crossover_point = random.randint(1, len(genes) - 1)
            for i, gene in enumerate(genes):
                if i < crossover_point:
                    child1.genes[gene] = parent1.genes[gene]
                    child2.genes[gene] = parent2.genes[gene]
                else:
                    child1.genes[gene] = parent2.genes[gene]
                    child2.genes[gene] = parent1.genes[gene]

        return child1, child2

    def mutate(self, individual: Individual) -> Individual:
        """Mutate individual genes"""
        for gene_name in individual.genes.keys():
            if random.random() < self.mutation_rate:
                param_range = self.parameter_ranges[gene_name]
                individual.genes[gene_name] = param_range.generate_random()

        return individual

    def optimize(self, data: pd.DataFrame) -> OptimizationResult:
        """Run genetic algorithm optimization"""
        import time

        start_time = time.time()

        logger.info(f"Starting genetic algorithm optimization")
        logger.info(
            f"Population: {self.population_size}, Generations: {self.generations}"
        )

        # Initialize population
        self.population = self.initialize_population()
        self.population = self.evaluate_population(self.population, data)

        total_evaluations = len(self.population)

        for generation in range(self.generations):
            logger.info(f"Generation {generation + 1}/{self.generations}")

            # Sort population by fitness
            self.population.sort(key=lambda x: x.fitness, reverse=True)

            # Calculate statistics
            fitnesses = [ind.fitness for ind in self.population]
            stats = {
                "generation": generation + 1,
                "best_fitness": max(fitnesses),
                "avg_fitness": np.mean(fitnesses),
                "worst_fitness": min(fitnesses),
            }

            self.generation_stats.append(stats)
            self.convergence_data["best_fitness"].append(stats["best_fitness"])
            self.convergence_data["avg_fitness"].append(stats["avg_fitness"])

            logger.info(
                f"Best fitness: {stats['best_fitness']:.4f}, "
                f"Avg: {stats['avg_fitness']:.4f}"
            )

            # Create next generation
            new_population = []

            # Elitism - keep best individuals
            new_population.extend(self.population[: self.elite_size])

            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(self.population)
                parent2 = self.tournament_selection(self.population)

                if random.random() < self.crossover_rate:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = Individual(), Individual()
                    child1.genes = parent1.genes.copy()
                    child2.genes = parent2.genes.copy()

                child1 = self.mutate(child1)
                child2 = self.mutate(child2)

                # Add children, but don't exceed population size
                if len(new_population) < self.population_size:
                    new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)

            # Trim to population size
            new_population = new_population[: self.population_size]

            # Evaluate new individuals
            new_individuals = new_population[self.elite_size :]
            new_individuals = self.evaluate_population(new_individuals, data)
            total_evaluations += len(new_individuals)

            self.population = new_population

        # Final sort
        self.population.sort(key=lambda x: x.fitness, reverse=True)

        optimization_time = time.time() - start_time

        result = OptimizationResult(
            best_individual=self.population[0],
            generation_stats=self.generation_stats,
            convergence_data=self.convergence_data,
            optimization_time=optimization_time,
            total_evaluations=total_evaluations,
        )

        logger.info(f"Optimization completed in {optimization_time:.2f} seconds")
        logger.info(f"Best fitness: {result.best_individual.fitness:.4f}")
        logger.info(f"Best parameters: {result.best_individual.genes}")

        return result
