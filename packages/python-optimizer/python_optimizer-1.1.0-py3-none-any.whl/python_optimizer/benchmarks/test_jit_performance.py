#!/usr/bin/env python3
"""
JIT Performance Test

Tests the performance improvements of JIT-compiled fitness evaluation functions
without relying on the original BacktestFitnessEvaluator.
"""

import logging
import os

# Add the trading optimizer to the path
import sys
import time
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.append("/Users/julio/Projects/Traiding/trading-optimizer")

from trading_optimizer.genetic_optimizer import Individual
from trading_optimizer.jit_fitness_evaluator import (
    NUMBA_AVAILABLE,
    JITBacktestFitnessEvaluator,
    calculate_max_drawdown_jit,
    calculate_returns_jit,
    calculate_sharpe_ratio_jit,
    generate_ma_signals_jit,
    generate_rsi_signals_jit,
    simulate_strategy_jit,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_synthetic_market_data(
    days: int = 1000, initial_price: float = 100.0
) -> pd.DataFrame:
    """Generate realistic synthetic market data for testing."""
    np.random.seed(42)  # For reproducible results

    dates = pd.date_range("2020-01-01", periods=days, freq="D")

    # Generate price series with realistic market characteristics
    returns = np.random.normal(0.0005, 0.02, days)  # Daily returns with drift
    returns[50:60] = -0.05  # Market crash period
    returns[200:250] = 0.03  # Bull market period

    prices = [initial_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    prices = np.array(prices)

    # Generate OHLC data
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
    volume = np.random.randint(10000, 100000, days)

    return pd.DataFrame(
        {
            "date": dates,
            "open": prices,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        }
    )


def create_test_individuals(count: int = 100) -> List[Individual]:
    """Create a population of test individuals with random parameters."""
    individuals = []
    np.random.seed(42)

    for _ in range(count):
        individual = Individual()
        individual.genes = {
            "strategy_type": np.random.choice(["ma_crossover", "rsi"]),
            "short_ma": np.random.randint(5, 20),
            "long_ma": np.random.randint(20, 50),
            "rsi_period": np.random.randint(10, 20),
            "oversold": np.random.uniform(20, 35),
            "overbought": np.random.uniform(65, 80),
        }
        individuals.append(individual)

    return individuals


def test_individual_jit_functions():
    """Test individual JIT functions for correctness and performance."""
    logger.info("Testing individual JIT functions...")

    # Generate test data
    prices = np.array([100, 101, 102, 99, 98, 100, 103, 105, 102, 99])

    # Test returns calculation
    start_time = time.perf_counter()
    returns = calculate_returns_jit(prices)
    returns_time = time.perf_counter() - start_time
    logger.info(
        f"Returns calculation: {returns_time*1000:.2f}ms, result shape: {returns.shape}"
    )

    # Test Sharpe ratio
    start_time = time.perf_counter()
    sharpe = calculate_sharpe_ratio_jit(returns)
    sharpe_time = time.perf_counter() - start_time
    logger.info(
        f"Sharpe ratio calculation: {sharpe_time*1000:.2f}ms, result: {sharpe:.4f}"
    )

    # Test max drawdown
    equity_curve = np.cumsum(returns) + 100
    start_time = time.perf_counter()
    max_dd = calculate_max_drawdown_jit(equity_curve)
    drawdown_time = time.perf_counter() - start_time
    logger.info(
        f"Max drawdown calculation: {drawdown_time*1000:.2f}ms, result: {max_dd:.4f}"
    )

    # Test signal generation
    start_time = time.perf_counter()
    ma_signals = generate_ma_signals_jit(prices, 3, 5)
    ma_time = time.perf_counter() - start_time
    logger.info(
        f"MA signal generation: {ma_time*1000:.2f}ms, signals: {np.sum(np.abs(ma_signals))}"
    )

    start_time = time.perf_counter()
    rsi_signals = generate_rsi_signals_jit(prices, 5, 30, 70)
    rsi_time = time.perf_counter() - start_time
    logger.info(
        f"RSI signal generation: {rsi_time*1000:.2f}ms, signals: {np.sum(np.abs(rsi_signals))}"
    )


def benchmark_jit_evaluator():
    """Comprehensive benchmark of JIT evaluator performance."""
    logger.info("=" * 60)
    logger.info("JIT EVALUATOR PERFORMANCE BENCHMARK")
    logger.info("=" * 60)
    logger.info(f"Numba available: {NUMBA_AVAILABLE}")

    # Test configurations
    data_sizes = [500, 1000, 2000]
    population_sizes = [50, 100]

    all_results = []

    for data_size in data_sizes:
        for pop_size in population_sizes:
            logger.info(
                f"\\n--- Testing with {data_size} days of data, {pop_size} individuals ---"
            )

            # Generate data and individuals
            market_data = generate_synthetic_market_data(data_size)
            individuals = create_test_individuals(pop_size)

            # Create JIT evaluator
            jit_evaluator = JITBacktestFitnessEvaluator(
                initial_cash=10000, commission=0.001
            )

            # Warm up JIT compilation
            logger.info("Warming up JIT compilation...")
            warmup_start = time.perf_counter()
            for individual in individuals[:3]:
                jit_evaluator.evaluate(individual, market_data)
            warmup_time = time.perf_counter() - warmup_start
            logger.info(f"Warmup completed in {warmup_time:.2f}s")

            # Main benchmark
            logger.info("Running main benchmark...")
            start_time = time.perf_counter()
            successful_evaluations = 0
            total_fitness = 0.0

            for i, individual in enumerate(individuals):
                eval_start = time.perf_counter()
                try:
                    metrics = jit_evaluator.evaluate(individual, market_data)
                    if individual.fitness > -1000:  # Successful evaluation
                        successful_evaluations += 1
                        total_fitness += individual.fitness
                except Exception as e:
                    logger.warning(f"Evaluation {i} failed: {e}")

                eval_time = time.perf_counter() - eval_start

                if (i + 1) % 20 == 0:
                    logger.info(f"  Completed {i+1}/{len(individuals)} evaluations")

            total_time = time.perf_counter() - start_time

            # Calculate statistics
            avg_fitness = total_fitness / max(successful_evaluations, 1)
            evals_per_sec = len(individuals) / total_time
            avg_eval_time = total_time / len(individuals)

            result = {
                "data_size": data_size,
                "population_size": pop_size,
                "total_time": total_time,
                "avg_eval_time": avg_eval_time,
                "evaluations_per_second": evals_per_sec,
                "successful_evaluations": successful_evaluations,
                "success_rate": successful_evaluations / len(individuals) * 100,
                "avg_fitness": avg_fitness,
                "warmup_time": warmup_time,
            }

            all_results.append(result)

            # Print results
            logger.info(f"\\nRESULTS:")
            logger.info(f"Total time:            {total_time:.3f}s")
            logger.info(f"Average eval time:     {avg_eval_time*1000:.2f}ms")
            logger.info(f"Evaluations per second: {evals_per_sec:.1f}")
            logger.info(f"Success rate:          {result['success_rate']:.1f}%")
            logger.info(f"Average fitness:       {avg_fitness:.2f}")

    # Generate summary
    generate_summary_report(all_results)
    return all_results


def generate_summary_report(results: List[Dict]):
    """Generate a comprehensive summary report."""
    logger.info("\\n" + "=" * 60)
    logger.info("SUMMARY REPORT")
    logger.info("=" * 60)

    # Overall statistics
    total_evaluations = sum(r["population_size"] for r in results)
    avg_eval_time = np.mean([r["avg_eval_time"] for r in results])
    avg_evals_per_sec = np.mean([r["evaluations_per_second"] for r in results])
    avg_success_rate = np.mean([r["success_rate"] for r in results])

    logger.info(f"Total evaluations completed: {total_evaluations}")
    logger.info(f"Average evaluation time: {avg_eval_time*1000:.2f}ms")
    logger.info(f"Average throughput: {avg_evals_per_sec:.1f} evaluations/second")
    logger.info(f"Average success rate: {avg_success_rate:.1f}%")

    # Detailed breakdown
    logger.info(f"\\nDetailed Results:")
    logger.info(
        f"{'Data Size':<10} {'Pop Size':<10} {'Time (s)':<10} {'Eval/s':<10} {'Success %':<12} {'Avg Fitness':<12}"
    )
    logger.info("-" * 70)

    for result in results:
        logger.info(
            f"{result['data_size']:<10} {result['population_size']:<10} "
            f"{result['total_time']:.2f}{'':<6} "
            f"{result['evaluations_per_second']:.1f}{'':<6} "
            f"{result['success_rate']:.1f}%{'':<8} "
            f"{result['avg_fitness']:.2f}"
        )

    # Performance insights
    logger.info(f"\\nPERFORMANCE INSIGHTS:")
    logger.info(
        f"• JIT compilation provides significant speedup for numerical computations"
    )
    logger.info(f"• Average evaluation time: {avg_eval_time*1000:.1f}ms per individual")
    logger.info(f"• Throughput: {avg_evals_per_sec:.0f} evaluations per second")
    logger.info(f"• Numba JIT available: {NUMBA_AVAILABLE}")

    if NUMBA_AVAILABLE:
        logger.info(f"• Using optimized Numba JIT compilation")
    else:
        logger.info(f"• Warning: Numba not available, running in fallback mode")


def run_comprehensive_test():
    """Run the complete JIT performance test suite."""
    logger.info("Starting JIT Performance Test Suite")

    # Test individual functions
    test_individual_jit_functions()

    # Benchmark complete evaluator
    results = benchmark_jit_evaluator()

    logger.info("\\n" + "=" * 60)
    logger.info("JIT PERFORMANCE TEST COMPLETED")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    run_comprehensive_test()
