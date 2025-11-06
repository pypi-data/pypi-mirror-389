"""
Tests for the genetic algorithm optimization module.
"""

import numpy as np
import pandas as pd
import pytest

from python_optimizer.genetic import (
    BacktestFitnessEvaluator,
    FitnessEvaluator,
    GeneticOptimizer,
    Individual,
    OptimizationResult,
    ParameterRange,
)


class TestParameterRange:
    """Tests for ParameterRange class"""

    def test_parameter_range_initialization(self):
        """Test ParameterRange initialization"""
        param = ParameterRange("test_param", 0.0, 1.0, "float")
        assert param.name == "test_param"
        assert param.min_val == 0.0
        assert param.max_val == 1.0
        assert param.param_type == "float"
        assert param.step is None

    def test_generate_random_float(self):
        """Test random float generation"""
        param = ParameterRange("float_param", 0.0, 10.0, "float")
        for _ in range(100):
            value = param.generate_random()
            assert isinstance(value, float)
            assert 0.0 <= value <= 10.0

    def test_generate_random_int(self):
        """Test random integer generation"""
        param = ParameterRange("int_param", 1, 10, "int")
        for _ in range(100):
            value = param.generate_random()
            assert isinstance(value, int)
            assert 1 <= value <= 10

    def test_generate_random_bool(self):
        """Test random boolean generation"""
        param = ParameterRange("bool_param", 0, 1, "bool")
        values = [param.generate_random() for _ in range(100)]
        assert all(isinstance(v, bool) for v in values)
        assert True in values and False in values  # Should generate both

    def test_generate_random_float_with_step(self):
        """Test float generation with step size"""
        param = ParameterRange("step_param", 0.0, 1.0, "float", step=0.1)
        for _ in range(50):
            value = param.generate_random()
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0
            # Check if value is close to a multiple of step
            assert abs(value - round(value / 0.1) * 0.1) < 1e-10


class TestIndividual:
    """Tests for Individual class"""

    def test_individual_initialization(self):
        """Test Individual initialization"""
        ind = Individual()
        assert isinstance(ind.genes, dict)
        assert len(ind.genes) == 0
        assert ind.fitness == 0.0
        assert isinstance(ind.metrics, dict)

    def test_individual_with_genes(self):
        """Test Individual with custom genes"""
        genes = {"param1": 1.5, "param2": 10, "param3": True}
        ind = Individual(genes=genes, fitness=100.5)
        assert ind.genes == genes
        assert ind.fitness == 100.5

    def test_individual_metrics(self):
        """Test Individual with metrics"""
        metrics = {"return": 15.5, "sharpe": 1.2, "drawdown": -10.0}
        ind = Individual(metrics=metrics)
        assert ind.metrics == metrics


class SimpleFitnessEvaluator(FitnessEvaluator):
    """Simple fitness evaluator for testing"""

    def evaluate(self, individual: Individual, data: pd.DataFrame) -> dict:
        """Simple evaluation: fitness = sum of gene values"""
        fitness = sum(individual.genes.values())
        individual.fitness = fitness
        individual.metrics = {"total": fitness}
        return individual.metrics


class TestGeneticOptimizer:
    """Tests for GeneticOptimizer class"""

    @pytest.fixture
    def parameter_ranges(self):
        """Create sample parameter ranges"""
        return [
            ParameterRange("param1", 0.0, 10.0, "float"),
            ParameterRange("param2", 1, 20, "int"),
            ParameterRange("param3", 0, 1, "bool"),
        ]

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "close": np.random.randn(100).cumsum() + 100,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )
        return data

    @pytest.fixture
    def optimizer(self, parameter_ranges):
        """Create optimizer instance"""
        evaluator = SimpleFitnessEvaluator()
        return GeneticOptimizer(
            parameter_ranges=parameter_ranges,
            fitness_evaluator=evaluator,
            population_size=10,
            generations=3,
            crossover_rate=0.8,
            mutation_rate=0.2,
            elite_size=2,
        )

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.population_size == 10
        assert optimizer.generations == 3
        assert optimizer.crossover_rate == 0.8
        assert optimizer.mutation_rate == 0.2
        assert optimizer.elite_size == 2
        assert len(optimizer.parameter_ranges) == 3

    def test_initialize_population(self, optimizer):
        """Test population initialization"""
        population = optimizer.initialize_population()
        assert len(population) == 10
        assert all(isinstance(ind, Individual) for ind in population)
        assert all(len(ind.genes) == 3 for ind in population)
        assert all("param1" in ind.genes for ind in population)
        assert all("param2" in ind.genes for ind in population)
        assert all("param3" in ind.genes for ind in population)

    def test_evaluate_population(self, optimizer, sample_data):
        """Test population evaluation"""
        population = optimizer.initialize_population()
        evaluated_pop = optimizer.evaluate_population(population, sample_data)
        assert len(evaluated_pop) == len(population)
        assert all(ind.fitness != 0.0 for ind in evaluated_pop)

    def test_tournament_selection(self, optimizer):
        """Test tournament selection"""
        population = [
            Individual(genes={"param1": i}, fitness=float(i)) for i in range(10)
        ]
        selected = optimizer.tournament_selection(population, tournament_size=3)
        assert isinstance(selected, Individual)
        assert selected.fitness >= 0

    def test_crossover(self, optimizer):
        """Test crossover operation"""
        parent1 = Individual(genes={"param1": 1.0, "param2": 5, "param3": True})
        parent2 = Individual(genes={"param1": 9.0, "param2": 15, "param3": False})

        child1, child2 = optimizer.crossover(parent1, parent2)

        assert isinstance(child1, Individual)
        assert isinstance(child2, Individual)
        assert len(child1.genes) == 3
        assert len(child2.genes) == 3

        # Check that genes come from parents
        all_parent_values = set()
        for parent in [parent1, parent2]:
            for key in parent.genes:
                all_parent_values.add((key, parent.genes[key]))

        for child in [child1, child2]:
            for key, value in child.genes.items():
                # Each gene should come from one of the parents
                assert (key, value) in all_parent_values

    def test_mutate(self, optimizer):
        """Test mutation operation"""
        original = Individual(genes={"param1": 5.0, "param2": 10, "param3": True})
        mutated = optimizer.mutate(original)

        assert isinstance(mutated, Individual)
        assert len(mutated.genes) == 3
        # Genes should still be valid types
        assert isinstance(mutated.genes["param1"], float)
        assert isinstance(mutated.genes["param2"], int)
        assert isinstance(mutated.genes["param3"], bool)

    def test_optimize_runs_successfully(self, optimizer, sample_data):
        """Test that optimization runs without errors"""
        result = optimizer.optimize(sample_data)

        assert isinstance(result, OptimizationResult)
        assert isinstance(result.best_individual, Individual)
        assert len(result.generation_stats) == 3  # 3 generations
        assert result.optimization_time >= 0  # Allow 0 on fast systems
        assert result.total_evaluations > 0

    def test_optimize_improves_fitness(self, optimizer, sample_data):
        """Test that optimization improves fitness over generations"""
        result = optimizer.optimize(sample_data)

        # Get fitness values across generations
        best_fitnesses = result.convergence_data["best_fitness"]
        avg_fitnesses = result.convergence_data["avg_fitness"]

        assert len(best_fitnesses) == 3
        assert len(avg_fitnesses) == 3

        # Best fitness should generally improve or stay the same (due to elitism)
        assert best_fitnesses[-1] >= best_fitnesses[0]

    def test_optimize_returns_valid_best_individual(self, optimizer, sample_data):
        """Test that best individual has valid genes"""
        result = optimizer.optimize(sample_data)
        best = result.best_individual

        assert len(best.genes) == 3
        assert 0.0 <= best.genes["param1"] <= 10.0
        assert 1 <= best.genes["param2"] <= 20
        assert isinstance(best.genes["param3"], bool)

    def test_elitism_preserves_best(self, optimizer, sample_data):
        """Test that elitism preserves best individuals"""
        result = optimizer.optimize(sample_data)

        # Check that generation stats show non-decreasing best fitness
        for i in range(1, len(result.generation_stats)):
            current_best = result.generation_stats[i]["best_fitness"]
            previous_best = result.generation_stats[i - 1]["best_fitness"]
            assert current_best >= previous_best

    def test_population_size_maintained(self, optimizer, sample_data):
        """Test that population size is maintained throughout optimization"""
        optimizer.optimize(sample_data)
        assert len(optimizer.population) == optimizer.population_size

    def test_convergence_data_structure(self, optimizer, sample_data):
        """Test convergence data structure"""
        result = optimizer.optimize(sample_data)

        assert "best_fitness" in result.convergence_data
        assert "avg_fitness" in result.convergence_data
        assert len(result.convergence_data["best_fitness"]) == optimizer.generations
        assert len(result.convergence_data["avg_fitness"]) == optimizer.generations


class TestBacktestFitnessEvaluator:
    """Tests for BacktestFitnessEvaluator class"""

    def test_calculate_fitness_metrics_basic(self):
        """Test basic fitness metrics calculation"""

        class MockStrategy:
            pass

        evaluator = BacktestFitnessEvaluator(MockStrategy, initial_cash=10000)

        results = {
            "total_return": 25.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": -15.2,
            "trades": {
                "total": {"total": 50},
                "won": {"total": 35, "pnl": {"total": 5000}},
                "lost": {"total": 15, "pnl": {"total": -1500}},
            },
        }

        metrics = evaluator._calculate_fitness_metrics(results)

        assert metrics["total_return"] == 25.5
        assert metrics["sharpe_ratio"] == 1.8
        assert metrics["max_drawdown"] == 15.2  # Should be absolute value
        assert metrics["total_trades"] == 50
        assert metrics["win_rate"] == 70.0  # 35/50 * 100
        assert metrics["profit_factor"] == pytest.approx(3.333, rel=0.01)

    def test_calculate_fitness_metrics_no_trades(self):
        """Test fitness metrics with no trades"""

        class MockStrategy:
            pass

        evaluator = BacktestFitnessEvaluator(MockStrategy)

        results = {
            "total_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "trades": {},
        }

        metrics = evaluator._calculate_fitness_metrics(results)

        assert metrics["total_trades"] == 0
        assert metrics["win_rate"] == 0
        assert metrics["profit_factor"] == 0

    def test_calculate_composite_fitness(self):
        """Test composite fitness calculation"""

        class MockStrategy:
            pass

        evaluator = BacktestFitnessEvaluator(MockStrategy)

        metrics = {
            "total_return": 25.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": 10.0,
            "total_trades": 50,
        }

        fitness = evaluator._calculate_composite_fitness(metrics)

        # Check that fitness is calculated correctly
        expected = 25.0 * 0.4 + 1.5 * 20 * 0.3 - 10.0 * 0.2 + min(50 / 10, 1) * 0.1
        assert fitness == pytest.approx(expected)

    def test_composite_fitness_weights(self):
        """Test that composite fitness uses correct weights"""

        class MockStrategy:
            pass

        evaluator = BacktestFitnessEvaluator(MockStrategy)

        # Test with extreme values
        metrics = {
            "total_return": 100.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_trades": 0,
        }

        fitness = evaluator._calculate_composite_fitness(metrics)
        assert fitness == pytest.approx(100.0 * 0.4)  # Only return component


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass"""

    def test_optimization_result_creation(self):
        """Test OptimizationResult creation"""
        best_ind = Individual(genes={"param1": 5.0}, fitness=100.0)
        stats = [
            {"generation": 1, "best_fitness": 50.0},
            {"generation": 2, "best_fitness": 100.0},
        ]
        convergence = {"best_fitness": [50.0, 100.0], "avg_fitness": [30.0, 60.0]}

        result = OptimizationResult(
            best_individual=best_ind,
            generation_stats=stats,
            convergence_data=convergence,
            optimization_time=10.5,
            total_evaluations=200,
        )

        assert result.best_individual == best_ind
        assert result.generation_stats == stats
        assert result.convergence_data == convergence
        assert result.optimization_time == 10.5
        assert result.total_evaluations == 200


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_small_population(self):
        """Test with very small population"""
        param_ranges = [ParameterRange("param1", 0.0, 10.0, "float")]
        evaluator = SimpleFitnessEvaluator()
        optimizer = GeneticOptimizer(
            parameter_ranges=param_ranges,
            fitness_evaluator=evaluator,
            population_size=2,
            generations=2,
            elite_size=1,
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = optimizer.optimize(data)

        assert isinstance(result, OptimizationResult)
        assert result.best_individual is not None

    def test_single_generation(self):
        """Test with single generation"""
        param_ranges = [ParameterRange("param1", 0.0, 10.0, "float")]
        evaluator = SimpleFitnessEvaluator()
        optimizer = GeneticOptimizer(
            parameter_ranges=param_ranges,
            fitness_evaluator=evaluator,
            population_size=5,
            generations=1,
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = optimizer.optimize(data)

        assert len(result.generation_stats) == 1
        assert len(result.convergence_data["best_fitness"]) == 1

    def test_high_mutation_rate(self):
        """Test with high mutation rate"""
        param_ranges = [ParameterRange("param1", 0.0, 10.0, "float")]
        evaluator = SimpleFitnessEvaluator()
        optimizer = GeneticOptimizer(
            parameter_ranges=param_ranges,
            fitness_evaluator=evaluator,
            population_size=10,
            generations=3,
            mutation_rate=0.9,  # Very high
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = optimizer.optimize(data)

        assert isinstance(result, OptimizationResult)

    def test_no_crossover(self):
        """Test with crossover rate of 0"""
        param_ranges = [ParameterRange("param1", 0.0, 10.0, "float")]
        evaluator = SimpleFitnessEvaluator()
        optimizer = GeneticOptimizer(
            parameter_ranges=param_ranges,
            fitness_evaluator=evaluator,
            population_size=10,
            generations=3,
            crossover_rate=0.0,  # No crossover
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = optimizer.optimize(data)

        assert isinstance(result, OptimizationResult)
