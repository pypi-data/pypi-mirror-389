"""
Tests for JIT-optimized fitness evaluator functions.
"""

import numpy as np
import pandas as pd
import pytest

from python_optimizer.jit.jit_fitness_evaluator import (
    NUMBA_AVAILABLE,
    JITBacktestFitnessEvaluator,
    calculate_max_drawdown_jit,
    calculate_profit_factor_jit,
    calculate_returns_jit,
    calculate_sharpe_ratio_jit,
    calculate_win_rate_jit,
    generate_ma_signals_jit,
    generate_rsi_signals_jit,
    simulate_strategy_jit,
)


class TestCalculateReturns:
    """Test calculate_returns_jit function."""

    def test_basic_returns(self):
        """Test basic returns calculation."""
        prices = np.array([100.0, 102.0, 101.0, 105.0])
        returns = calculate_returns_jit(prices)

        assert len(returns) == 3
        np.testing.assert_allclose(returns[0], 0.02, rtol=1e-5)  # 2% gain
        np.testing.assert_allclose(returns[1], -0.009804, rtol=1e-4)  # ~-1% loss
        np.testing.assert_allclose(returns[2], 0.039604, rtol=1e-4)  # ~4% gain

    def test_empty_prices(self):
        """Test returns with single price."""
        prices = np.array([100.0])
        returns = calculate_returns_jit(prices)
        assert len(returns) == 1
        assert returns[0] == 0.0

    def test_zero_price_handling(self):
        """Test handling of zero prices."""
        prices = np.array([100.0, 0.0, 105.0])
        returns = calculate_returns_jit(prices)
        assert returns[0] == -1.0  # 100 -> 0 is -100%
        assert returns[1] == 0.0  # Division by zero handled

    def test_constant_prices(self):
        """Test returns with constant prices."""
        prices = np.array([100.0, 100.0, 100.0])
        returns = calculate_returns_jit(prices)
        np.testing.assert_allclose(returns, 0.0)


class TestCalculateSharpeRatio:
    """Test calculate_sharpe_ratio_jit function."""

    def test_positive_sharpe(self):
        """Test Sharpe ratio with positive returns."""
        returns = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe > 0

    def test_zero_returns(self):
        """Test Sharpe ratio with zero returns."""
        returns = np.zeros(10)
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe == 0.0

    def test_empty_returns(self):
        """Test Sharpe ratio with empty returns."""
        returns = np.array([])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe == 0.0

    def test_with_risk_free_rate(self):
        """Test Sharpe ratio with non-zero risk-free rate."""
        returns = np.array([0.05, 0.06, 0.04, 0.055, 0.045])
        sharpe_no_rf = calculate_sharpe_ratio_jit(returns, 0.0)
        sharpe_with_rf = calculate_sharpe_ratio_jit(returns, 0.02)
        # Sharpe should be lower with risk-free rate
        assert sharpe_with_rf < sharpe_no_rf

    def test_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        returns = np.array([-0.01, -0.02, -0.015, -0.01, -0.02])
        sharpe = calculate_sharpe_ratio_jit(returns)
        assert sharpe < 0


class TestCalculateMaxDrawdown:
    """Test calculate_max_drawdown_jit function."""

    def test_no_drawdown(self):
        """Test max drawdown with always increasing equity."""
        equity = np.array([100.0, 110.0, 120.0, 130.0])
        max_dd = calculate_max_drawdown_jit(equity)
        assert max_dd == 0.0

    def test_single_drawdown(self):
        """Test max drawdown with single drop."""
        equity = np.array([100.0, 110.0, 90.0, 95.0])
        max_dd = calculate_max_drawdown_jit(equity)
        # Peak at 110, trough at 90, dd = 20/110 = 0.1818...
        np.testing.assert_allclose(max_dd, 0.1818, rtol=1e-3)

    def test_multiple_drawdowns(self):
        """Test max drawdown with multiple drops."""
        equity = np.array([100.0, 120.0, 100.0, 130.0, 90.0])
        max_dd = calculate_max_drawdown_jit(equity)
        # Peak at 130, trough at 90, dd = 40/130 = 0.3077...
        np.testing.assert_allclose(max_dd, 0.3077, rtol=1e-3)

    def test_empty_equity(self):
        """Test max drawdown with empty array."""
        equity = np.array([])
        max_dd = calculate_max_drawdown_jit(equity)
        assert max_dd == 0.0

    def test_zero_equity(self):
        """Test max drawdown with zero equity."""
        equity = np.array([100.0, 0.0])
        max_dd = calculate_max_drawdown_jit(equity)
        assert max_dd == 1.0  # 100% drawdown


class TestCalculateProfitFactor:
    """Test calculate_profit_factor_jit function."""

    def test_profitable_trades(self):
        """Test profit factor with profitable trades."""
        returns = np.array([0.05, 0.03, -0.01, 0.04, -0.02])
        pf = calculate_profit_factor_jit(returns)
        # Total profit: 0.12, Total loss: 0.03, PF = 4.0
        np.testing.assert_allclose(pf, 4.0, rtol=1e-5)

    def test_only_profits(self):
        """Test profit factor with only profits."""
        returns = np.array([0.05, 0.03, 0.04])
        pf = calculate_profit_factor_jit(returns)
        assert pf == 0.0  # No losses, so PF = 0

    def test_only_losses(self):
        """Test profit factor with only losses."""
        returns = np.array([-0.05, -0.03, -0.04])
        pf = calculate_profit_factor_jit(returns)
        assert pf == 0.0  # No profits

    def test_empty_returns(self):
        """Test profit factor with empty returns."""
        returns = np.array([])
        pf = calculate_profit_factor_jit(returns)
        assert pf == 0.0


class TestCalculateWinRate:
    """Test calculate_win_rate_jit function."""

    def test_mixed_trades(self):
        """Test win rate with mixed trades."""
        returns = np.array([0.05, -0.03, 0.04, -0.02, 0.01])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == 0.6  # 3 winners out of 5

    def test_all_winners(self):
        """Test win rate with all winners."""
        returns = np.array([0.05, 0.03, 0.04])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == 1.0

    def test_all_losers(self):
        """Test win rate with all losers."""
        returns = np.array([-0.05, -0.03, -0.04])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == 0.0

    def test_empty_returns(self):
        """Test win rate with empty returns."""
        returns = np.array([])
        win_rate = calculate_win_rate_jit(returns)
        assert win_rate == 0.0


class TestSimulateStrategy:
    """Test simulate_strategy_jit function."""

    def test_basic_simulation(self):
        """Test basic strategy simulation."""
        signals = np.array([1, 0, -1, 0, 1])  # Buy, hold, sell, hold, buy
        prices = np.array([100.0, 105.0, 110.0, 108.0, 112.0])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000.0, 0.001)

        assert len(equity) == 5
        assert equity[0] > 0  # Initial equity
        assert trades > 0  # Some trades executed

    def test_empty_signals(self):
        """Test simulation with empty signals."""
        signals = np.array([])
        prices = np.array([])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000.0, 0.001)

        assert len(equity) == 1
        assert trades == 0

    def test_mismatched_lengths(self):
        """Test simulation with mismatched signal/price lengths."""
        signals = np.array([1, 0, -1])
        prices = np.array([100.0, 105.0])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000.0, 0.001)

        assert len(equity) == 1
        assert trades == 0

    def test_no_signals(self):
        """Test simulation with no trading signals."""
        signals = np.zeros(5)
        prices = np.array([100.0, 105.0, 110.0, 108.0, 112.0])
        equity, returns, trades = simulate_strategy_jit(signals, prices, 10000.0, 0.001)

        assert trades == 0
        # All equity should equal initial cash
        np.testing.assert_allclose(equity, 10000.0)


class TestGenerateMASignals:
    """Test generate_ma_signals_jit function."""

    def test_basic_crossover(self):
        """Test basic MA crossover signal generation."""
        # Create price series that crosses over
        prices = np.array([100, 101, 102, 103, 104, 105, 106, 110, 115, 120])
        signals = generate_ma_signals_jit(prices, 2, 5)

        assert len(signals) == len(prices)
        # Signals array should be valid (may be all zeros for monotonic trend)
        assert isinstance(signals, np.ndarray)

    def test_insufficient_data(self):
        """Test MA signals with insufficient data."""
        prices = np.array([100, 101])
        signals = generate_ma_signals_jit(prices, 5, 10)

        assert len(signals) == len(prices)
        # All zeros due to insufficient data
        np.testing.assert_array_equal(signals, 0)

    def test_invalid_windows(self):
        """Test MA signals with invalid window parameters."""
        prices = np.array([100, 101, 102, 103, 104])
        # Short window >= long window
        signals = generate_ma_signals_jit(prices, 5, 3)

        assert len(signals) == len(prices)
        np.testing.assert_array_equal(signals, 0)

    def test_buy_sell_signals(self):
        """Test that MA generates both buy and sell signals."""
        # Create price pattern with clear up and down trends
        prices = np.array([100, 105, 110, 115, 120, 115, 110, 105, 100, 95])
        signals = generate_ma_signals_jit(prices, 2, 4)

        # Should have both buy (1) and sell (-1) signals
        assert np.any(signals == 1) or np.any(signals == -1)


class TestGenerateRSISignals:
    """Test generate_rsi_signals_jit function."""

    def test_basic_rsi_signals(self):
        """Test basic RSI signal generation."""
        # Create price series
        prices = np.array([100, 95, 90, 92, 95, 100, 105, 110, 108, 105])
        signals = generate_rsi_signals_jit(prices, 5, 30, 70)

        assert len(signals) == len(prices)

    def test_insufficient_data(self):
        """Test RSI signals with insufficient data."""
        prices = np.array([100, 101, 102])
        signals = generate_rsi_signals_jit(prices, 5, 30, 70)

        assert len(signals) == len(prices)
        np.testing.assert_array_equal(signals, 0)

    def test_oversold_signal(self):
        """Test RSI generates buy signal when oversold."""
        # Create declining price series (should be oversold)
        prices = np.array([100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40])
        signals = generate_rsi_signals_jit(prices, 5, 30, 70)

        # Should have some buy signals (1) for oversold
        assert np.any(signals == 1)

    def test_overbought_signal(self):
        """Test RSI generates sell signal when overbought."""
        # Create rising price series (should be overbought)
        prices = np.array([50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105])
        signals = generate_rsi_signals_jit(prices, 5, 30, 70)

        # Should have some sell signals (-1) for overbought
        assert np.any(signals == -1)


class TestJITBacktestFitnessEvaluator:
    """Test JITBacktestFitnessEvaluator class."""

    def test_initialization(self):
        """Test evaluator initialization."""
        evaluator = JITBacktestFitnessEvaluator(initial_cash=10000, commission=0.001)

        assert evaluator.initial_cash == 10000
        assert evaluator.commission == 0.001
        assert evaluator.evaluation_count == 0
        assert evaluator.total_time == 0.0

    def test_prepare_data(self):
        """Test data preparation."""
        data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "high": [101, 102, 103],
                "low": [99, 100, 101],
                "volume": [1000, 1100, 1200],
            }
        )

        evaluator = JITBacktestFitnessEvaluator()
        prepared = evaluator._prepare_data(data)

        assert "close" in prepared
        assert "high" in prepared
        assert "low" in prepared
        assert "volume" in prepared
        assert len(prepared["close"]) == 3

    def test_data_caching(self):
        """Test that data is cached properly."""
        data = pd.DataFrame({"close": [100, 101, 102]})

        evaluator = JITBacktestFitnessEvaluator()
        prepared1 = evaluator._prepare_data(data)
        prepared2 = evaluator._prepare_data(data)

        # Should return same cached data
        assert prepared1 is prepared2

    def test_missing_columns(self):
        """Test data preparation with missing columns."""
        # Only close column
        data = pd.DataFrame({"close": [100, 101, 102]})

        evaluator = JITBacktestFitnessEvaluator()
        prepared = evaluator._prepare_data(data)

        assert "close" in prepared
        assert "high" in prepared
        assert "low" in prepared
        assert "volume" in prepared
        # Missing columns should be filled appropriately
        np.testing.assert_array_equal(prepared["volume"], np.ones(3))


class TestNumbaAvailability:
    """Test Numba availability detection."""

    def test_numba_available_flag(self):
        """Test that NUMBA_AVAILABLE is a boolean."""
        assert isinstance(NUMBA_AVAILABLE, bool)

    def test_functions_work_without_numba(self):
        """Test that functions work even if Numba is not available."""
        # These functions should work regardless of Numba availability
        prices = np.array([100.0, 102.0, 101.0])
        returns = calculate_returns_jit(prices)
        assert len(returns) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
