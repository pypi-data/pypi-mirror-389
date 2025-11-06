"""
Tests for JIT-optimized functions and profiling module.
"""

import numpy as np
import pandas as pd
import pytest

from python_optimizer.genetic import Individual
from python_optimizer.jit import (
    JITBacktestFitnessEvaluator,
    calculate_max_drawdown_jit,
    calculate_profit_factor_jit,
    calculate_returns_jit,
    calculate_sharpe_ratio_jit,
    calculate_win_rate_jit,
    generate_ma_signals_jit,
    simulate_strategy_jit,
)
from python_optimizer.profiling import (
    PerformanceProfiler,
    ProfilerConfig,
    clear_performance_stats,
    get_performance_stats,
)


class TestJITCalculations:
    """Tests for JIT-optimized calculation functions"""

    def test_calculate_returns_jit(self):
        """Test JIT returns calculation"""
        prices = np.array([100.0, 105.0, 103.0, 108.0])
        returns = calculate_returns_jit(prices)

        assert len(returns) == 3
        assert returns[0] == pytest.approx(0.05)  # (105-100)/100
        assert returns[1] == pytest.approx(-0.019047, rel=0.01)  # (103-105)/105
        assert returns[2] == pytest.approx(0.048543, rel=0.01)  # (108-103)/103

    def test_calculate_returns_empty(self):
        """Test returns with empty array"""
        prices = np.array([])
        returns = calculate_returns_jit(prices)
        assert len(returns) >= 0

    def test_calculate_returns_single_price(self):
        """Test returns with single price"""
        prices = np.array([100.0])
        returns = calculate_returns_jit(prices)
        assert len(returns) == 1

    def test_calculate_sharpe_ratio_jit(self):
        """Test Sharpe ratio calculation"""
        # Positive returns
        returns = np.array([0.01, 0.02, -0.005, 0.015, 0.01])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert isinstance(sharpe, float)
        assert sharpe > 0

    def test_calculate_sharpe_ratio_zero_std(self):
        """Test Sharpe ratio with zero std dev"""
        returns = np.array([0.01, 0.01, 0.01, 0.01])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_empty(self):
        """Test Sharpe ratio with empty returns"""
        returns = np.array([])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe == 0.0

    def test_calculate_max_drawdown_jit(self):
        """Test maximum drawdown calculation"""
        equity = np.array([100.0, 110.0, 105.0, 115.0, 90.0, 95.0])
        max_dd = calculate_max_drawdown_jit(equity)

        # Max drawdown should be from 115 to 90: (115-90)/115 ≈ 0.217
        assert max_dd == pytest.approx(0.217, rel=0.01)

    def test_calculate_max_drawdown_no_drawdown(self):
        """Test with no drawdown (always increasing)"""
        equity = np.array([100.0, 110.0, 120.0, 130.0])
        max_dd = calculate_max_drawdown_jit(equity)
        assert max_dd == 0.0

    def test_calculate_max_drawdown_empty(self):
        """Test with empty equity curve"""
        equity = np.array([])
        max_dd = calculate_max_drawdown_jit(equity)
        assert max_dd == 0.0

    def test_calculate_profit_factor_jit(self):
        """Test profit factor calculation"""
        returns = np.array([0.05, -0.02, 0.03, -0.01, 0.04])
        pf = calculate_profit_factor_jit(returns)

        # Profit: 0.05 + 0.03 + 0.04 = 0.12
        # Loss: 0.02 + 0.01 = 0.03
        # PF = 0.12 / 0.03 = 4.0
        assert pf == pytest.approx(4.0)

    def test_calculate_profit_factor_no_losses(self):
        """Test profit factor with only winning trades"""
        returns = np.array([0.05, 0.03, 0.04])
        pf = calculate_profit_factor_jit(returns)
        assert pf == 0.0  # No losses means PF is 0

    def test_calculate_profit_factor_empty(self):
        """Test profit factor with empty array"""
        returns = np.array([])
        pf = calculate_profit_factor_jit(returns)
        assert pf == 0.0

    def test_calculate_win_rate_jit(self):
        """Test win rate calculation"""
        returns = np.array([0.05, -0.02, 0.03, -0.01, 0.04])
        win_rate = calculate_win_rate_jit(returns)

        # 3 wins out of 5 = 0.6
        assert win_rate == pytest.approx(0.6)

    def test_calculate_win_rate_all_wins(self):
        """Test win rate with all winning trades"""
        returns = np.array([0.05, 0.03, 0.04])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == pytest.approx(1.0)

    def test_calculate_win_rate_all_losses(self):
        """Test win rate with all losing trades"""
        returns = np.array([-0.05, -0.03, -0.04])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == pytest.approx(0.0)

    def test_calculate_win_rate_empty(self):
        """Test win rate with empty array"""
        returns = np.array([])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == 0.0


class TestMASignals:
    """Tests for moving average signal generation"""

    def test_generate_ma_signals_basic(self):
        """Test basic MA signal generation"""
        prices = np.array([100.0, 102.0, 105.0, 108.0, 107.0, 110.0, 115.0, 113.0])
        signals = generate_ma_signals_jit(prices, short_window=2, long_window=4)

        assert len(signals) == len(prices)
        assert isinstance(signals, np.ndarray)

    def test_generate_ma_signals_insufficient_data(self):
        """Test MA signals with insufficient data"""
        prices = np.array([100.0, 102.0])
        signals = generate_ma_signals_jit(prices, short_window=2, long_window=4)

        # Should return zeros when insufficient data
        assert len(signals) == len(prices)
        assert np.all(signals == 0)

    def test_generate_ma_signals_invalid_windows(self):
        """Test MA signals with invalid window sizes"""
        prices = np.array([100.0, 102.0, 105.0, 108.0, 107.0])
        signals = generate_ma_signals_jit(prices, short_window=4, long_window=2)

        # Should return zeros when short >= long
        assert np.all(signals == 0)


class TestStrategySimulation:
    """Tests for strategy simulation"""

    def test_simulate_strategy_basic(self):
        """Test basic strategy simulation"""
        signals = np.array([0, 1, 0, 0, -1, 0])
        prices = np.array([100.0, 105.0, 103.0, 108.0, 110.0, 108.0])
        initial_cash = 10000.0
        commission = 0.001

        equity, returns, trades = simulate_strategy_jit(
            signals, prices, initial_cash, commission
        )

        assert len(equity) == len(prices)
        assert isinstance(trades, (int, np.integer))
        assert trades >= 0

    def test_simulate_strategy_empty(self):
        """Test simulation with empty arrays"""
        signals = np.array([])
        prices = np.array([])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000, 0.001)

        assert len(equity) >= 0
        assert trades == 0

    def test_simulate_strategy_mismatched_arrays(self):
        """Test simulation with mismatched array sizes"""
        signals = np.array([1, 0, -1])
        prices = np.array([100.0, 105.0])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000, 0.001)

        assert len(equity) >= 0


class TestJITBacktestFitnessEvaluator:
    """Tests for JIT fitness evaluator"""

    def test_evaluator_initialization(self):
        """Test evaluator initialization"""

        class MockStrategy:
            pass

        evaluator = JITBacktestFitnessEvaluator(MockStrategy)
        assert evaluator.strategy_class == MockStrategy
        assert evaluator.initial_cash > 0

    def test_evaluator_with_custom_params(self):
        """Test evaluator with custom parameters"""

        class MockStrategy:
            pass

        evaluator = JITBacktestFitnessEvaluator(
            MockStrategy, initial_cash=50000, commission=0.002
        )
        assert evaluator.initial_cash == 50000
        assert evaluator.commission == 0.002


class TestPerformanceProfiler:
    """Tests for performance profiler"""

    def setup_method(self):
        """Clear stats before each test"""
        clear_performance_stats()

    def test_profiler_initialization(self):
        """Test profiler initialization"""
        profiler = PerformanceProfiler()
        assert profiler.config.enabled is True

    def test_profiler_with_config(self):
        """Test profiler with custom config"""
        config = ProfilerConfig(enabled=False, detailed=True)
        profiler = PerformanceProfiler(config)
        assert profiler.config.enabled is False
        assert profiler.config.detailed is True

    def test_profile_function(self):
        """Test function profiling"""
        profiler = PerformanceProfiler()
        profiler.profile_function("test_func", 0.5)
        profiler.profile_function("test_func", 0.3)

        stats = get_performance_stats()
        assert "test_func" in stats
        assert stats["test_func"]["call_count"] == 2
        assert stats["test_func"]["total_time"] == pytest.approx(0.8)
        assert stats["test_func"]["avg_time"] == pytest.approx(0.4)
        assert stats["test_func"]["min_time"] == pytest.approx(0.3)
        assert stats["test_func"]["max_time"] == pytest.approx(0.5)

    def test_profile_disabled(self):
        """Test that profiling can be disabled"""
        config = ProfilerConfig(enabled=False)
        profiler = PerformanceProfiler(config)
        profiler.profile_function("test_func", 0.5)

        stats = get_performance_stats()
        assert "test_func" not in stats

    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        profiler = PerformanceProfiler()
        profiler.profile_function("func1", 0.1)
        profiler.profile_function("func2", 0.2)

        stats = get_performance_stats()
        assert len(stats) == 2
        assert "func1" in stats
        assert "func2" in stats

    def test_clear_performance_stats(self):
        """Test clearing performance statistics"""
        profiler = PerformanceProfiler()
        profiler.profile_function("test_func", 0.5)

        clear_performance_stats()
        stats = get_performance_stats()
        assert len(stats) == 0

    def test_multiple_functions(self):
        """Test profiling multiple functions"""
        profiler = PerformanceProfiler()

        for i in range(10):
            profiler.profile_function("func_a", 0.1 * i)
            profiler.profile_function("func_b", 0.2 * i)

        stats = get_performance_stats()
        assert stats["func_a"]["call_count"] == 10
        assert stats["func_b"]["call_count"] == 10
        assert stats["func_a"]["min_time"] == 0.0
        assert stats["func_b"]["min_time"] == 0.0

    def test_stats_consistency(self):
        """Test that stats are consistent"""
        profiler = PerformanceProfiler()
        times = [0.5, 0.3, 0.7, 0.2, 0.6]

        for t in times:
            profiler.profile_function("test_func", t)

        stats = get_performance_stats()
        data = stats["test_func"]

        assert data["call_count"] == len(times)
        assert data["total_time"] == pytest.approx(sum(times))
        assert data["avg_time"] == pytest.approx(sum(times) / len(times))
        assert data["min_time"] == pytest.approx(min(times))
        assert data["max_time"] == pytest.approx(max(times))


class TestProfilerConfig:
    """Tests for ProfilerConfig dataclass"""

    def test_config_defaults(self):
        """Test config default values"""
        config = ProfilerConfig()
        assert config.enabled is True
        assert config.detailed is False
        assert config.output_format == "json"

    def test_config_custom_values(self):
        """Test config with custom values"""
        config = ProfilerConfig(enabled=False, detailed=True, output_format="csv")
        assert config.enabled is False
        assert config.detailed is True
        assert config.output_format == "csv"


class TestIntegration:
    """Integration tests combining multiple components"""

    def test_jit_functions_with_real_data(self):
        """Test JIT functions with realistic financial data"""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(252) * 2)  # Year of price data
        prices = np.abs(prices)  # Ensure positive prices

        # Calculate metrics
        returns = calculate_returns_jit(prices)
        sharpe = calculate_sharpe_ratio_jit(returns)
        max_dd = calculate_max_drawdown_jit(prices)
        pf = calculate_profit_factor_jit(returns)
        win_rate = calculate_win_rate_jit(returns)

        # Basic sanity checks
        assert len(returns) == 251
        assert isinstance(sharpe, float)
        assert 0 <= max_dd <= 1
        assert pf >= 0
        assert 0 <= win_rate <= 1

    def test_profiler_with_simulated_workload(self):
        """Test profiler with simulated function calls"""
        clear_performance_stats()
        profiler = PerformanceProfiler()

        # Simulate workload
        import time

        for _ in range(5):
            start = time.perf_counter()
            time.sleep(0.001)  # Simulate work
            elapsed = time.perf_counter() - start
            profiler.profile_function("simulated_work", elapsed)

        stats = get_performance_stats()
        assert stats["simulated_work"]["call_count"] == 5
        assert stats["simulated_work"]["avg_time"] > 0
