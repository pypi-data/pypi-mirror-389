#!/usr/bin/env python3
"""
Real-World Trading Strategy Optimization

This example demonstrates how to use Python Optimizer for high-performance
trading strategy backtesting and optimization.
"""

import time
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from python_optimizer import (
    configure_specialization,
    get_specialization_stats,
    optimize,
)

# Configure for high-performance trading
configure_specialization(
    min_calls_for_specialization=1,  # Quick specialization for trading
    enable_adaptive_learning=True,  # Adapt to market patterns
    max_cache_size=1000,  # Large cache for strategy variants
    max_memory_mb=100,  # Sufficient memory for trading data
)


@optimize(jit=True, specialize=True, fastmath=True)
def calculate_technical_indicators(
    prices: np.ndarray, volume: np.ndarray = None
) -> Dict:
    """
    Calculate technical indicators with high-performance optimization.
    Specialized versions for different market data formats.
    """
    n = len(prices)

    # Moving averages (vectorized for speed)
    sma_20 = np.convolve(prices, np.ones(20) / 20, mode="valid")
    sma_50 = np.convolve(prices, np.ones(50) / 50, mode="valid")

    # Pad the shorter arrays to match price length
    sma_20_padded = np.concatenate([np.full(19, np.nan), sma_20])
    sma_50_padded = np.concatenate([np.full(49, np.nan), sma_50])

    # RSI Calculation
    rsi = np.zeros(n)
    if n > 14:
        price_changes = np.diff(prices)
        gains = np.maximum(price_changes, 0)
        losses = np.maximum(-price_changes, 0)

        # Initial average gain/loss
        avg_gain = np.mean(gains[:14])
        avg_loss = np.mean(losses[:14])

        for i in range(14, n - 1):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14

            if avg_loss != 0:
                rs = avg_gain / avg_loss
                rsi[i + 1] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    bb_upper = np.zeros(n)
    bb_lower = np.zeros(n)
    bb_middle = sma_20_padded

    for i in range(19, n):
        window = prices[i - 19 : i + 1]
        std = np.std(window)
        bb_upper[i] = bb_middle[i] + 2 * std
        bb_lower[i] = bb_middle[i] - 2 * std

    # MACD
    ema_12 = np.zeros(n)
    ema_26 = np.zeros(n)

    if n > 0:
        ema_12[0] = prices[0]
        ema_26[0] = prices[0]

        alpha_12 = 2.0 / 13.0
        alpha_26 = 2.0 / 27.0

        for i in range(1, n):
            ema_12[i] = alpha_12 * prices[i] + (1 - alpha_12) * ema_12[i - 1]
            ema_26[i] = alpha_26 * prices[i] + (1 - alpha_26) * ema_26[i - 1]

    macd_line = ema_12 - ema_26

    # Volume indicators (if volume provided)
    volume_indicators = {}
    if volume is not None and len(volume) == n:
        # Volume Moving Average
        vma_20 = np.convolve(volume, np.ones(20) / 20, mode="valid")
        vma_20_padded = np.concatenate([np.full(19, np.nan), vma_20])

        # Volume-Price Trend
        vpt = np.zeros(n)
        for i in range(1, n):
            price_change_pct = (prices[i] - prices[i - 1]) / prices[i - 1]
            vpt[i] = vpt[i - 1] + volume[i] * price_change_pct

        volume_indicators = {"vma_20": vma_20_padded, "vpt": vpt}

    return {
        "sma_20": sma_20_padded,
        "sma_50": sma_50_padded,
        "rsi": rsi,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_middle": bb_middle,
        "macd": macd_line,
        "ema_12": ema_12,
        "ema_26": ema_26,
        **volume_indicators,
    }


@optimize(jit=True, specialize=True, cache=True)
def backtest_strategy(
    prices: np.ndarray,
    indicators: Dict,
    strategy_params: Dict,
    initial_capital: float = 10000.0,
) -> Dict:
    """
    High-performance strategy backtesting with specialization for different parameter sets.
    Each unique strategy configuration gets its own optimized version.
    """
    n = len(prices)

    # Strategy parameters
    sma_short = strategy_params.get("sma_short", 20)
    sma_long = strategy_params.get("sma_long", 50)
    rsi_oversold = strategy_params.get("rsi_oversold", 30)
    rsi_overbought = strategy_params.get("rsi_overbought", 70)
    stop_loss_pct = strategy_params.get("stop_loss", 0.05)
    take_profit_pct = strategy_params.get("take_profit", 0.10)

    # Trading state
    position = 0.0  # Current position (0 = no position, 1 = long, -1 = short)
    cash = initial_capital
    shares = 0.0
    entry_price = 0.0

    # Track performance
    portfolio_values = np.zeros(n)
    trades = []

    # Get indicators
    sma_20 = indicators["sma_20"]
    sma_50 = indicators["sma_50"]
    rsi = indicators["rsi"]
    bb_upper = indicators["bb_upper"]
    bb_lower = indicators["bb_lower"]

    for i in range(1, n):
        current_price = prices[i]

        # Calculate portfolio value
        portfolio_values[i] = cash + shares * current_price

        # Skip if not enough data for indicators
        if i < 50 or np.isnan(sma_20[i]) or np.isnan(sma_50[i]) or np.isnan(rsi[i]):
            continue

        # Entry signals
        if position == 0:  # No position
            # Long entry: SMA crossover + RSI oversold + price near lower Bollinger Band
            if (
                sma_20[i] > sma_50[i]
                and sma_20[i - 1] <= sma_50[i - 1]
                and rsi[i] < rsi_oversold
                and current_price < bb_lower[i] * 1.02
            ):

                # Enter long position
                shares = cash / current_price
                cash = 0.0
                position = 1.0
                entry_price = current_price

                trades.append(
                    {"day": i, "type": "BUY", "price": current_price, "shares": shares}
                )

        else:  # Have position
            # Exit conditions
            should_exit = False
            exit_reason = ""

            # Stop loss
            if position > 0 and current_price < entry_price * (1 - stop_loss_pct):
                should_exit = True
                exit_reason = "STOP_LOSS"

            # Take profit
            elif position > 0 and current_price > entry_price * (1 + take_profit_pct):
                should_exit = True
                exit_reason = "TAKE_PROFIT"

            # RSI overbought
            elif position > 0 and rsi[i] > rsi_overbought:
                should_exit = True
                exit_reason = "RSI_OVERBOUGHT"

            # SMA crossover down
            elif (
                position > 0
                and sma_20[i] < sma_50[i]
                and sma_20[i - 1] >= sma_50[i - 1]
            ):
                should_exit = True
                exit_reason = "SMA_CROSSOVER_DOWN"

            if should_exit:
                # Exit position
                cash = shares * current_price
                profit = (
                    cash - initial_capital
                    if len(trades) == 1
                    else cash - trades[-1]["price"] * shares
                )

                trades.append(
                    {
                        "day": i,
                        "type": "SELL",
                        "price": current_price,
                        "shares": shares,
                        "profit": profit,
                        "reason": exit_reason,
                    }
                )

                shares = 0.0
                position = 0.0
                entry_price = 0.0

    # Final portfolio value
    final_value = cash + shares * prices[-1]

    # Calculate performance metrics
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    returns = returns[portfolio_values[:-1] > 0]  # Remove zeros

    if len(returns) > 0:
        total_return = (final_value - initial_capital) / initial_capital
        annual_return = total_return * (252 / n)  # Assuming daily data
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # Maximum drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = np.min(drawdown)
    else:
        total_return = annual_return = volatility = sharpe_ratio = max_drawdown = 0

    # Win rate
    profitable_trades = [t for t in trades if t.get("profit", 0) > 0]
    win_rate = (
        len(profitable_trades) / len([t for t in trades if "profit" in t])
        if trades
        else 0
    )

    return {
        "final_value": final_value,
        "total_return": total_return,
        "annual_return": annual_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "num_trades": len(trades),
        "win_rate": win_rate,
        "trades": trades,
        "portfolio_values": portfolio_values,
    }


@optimize(jit=True, specialize=True)
def optimize_strategy_parameters(
    prices: np.ndarray, indicators: Dict, param_ranges: Dict
) -> Tuple[Dict, List]:
    """
    Optimize strategy parameters using grid search with JIT acceleration.
    Specialized for different parameter space configurations.
    """

    best_sharpe = -999
    best_params = {}
    all_results = []

    # Generate parameter combinations
    sma_short_range = param_ranges.get("sma_short", [10, 15, 20])
    sma_long_range = param_ranges.get("sma_long", [40, 50, 60])
    rsi_oversold_range = param_ranges.get("rsi_oversold", [25, 30, 35])
    rsi_overbought_range = param_ranges.get("rsi_overbought", [65, 70, 75])

    total_combinations = (
        len(sma_short_range)
        * len(sma_long_range)
        * len(rsi_oversold_range)
        * len(rsi_overbought_range)
    )

    print(f"Testing {total_combinations} parameter combinations...")

    combination_count = 0

    for sma_short in sma_short_range:
        for sma_long in sma_long_range:
            if sma_short >= sma_long:
                continue  # Skip invalid combinations

            for rsi_oversold in rsi_oversold_range:
                for rsi_overbought in rsi_overbought_range:
                    if rsi_oversold >= rsi_overbought:
                        continue

                    combination_count += 1

                    params = {
                        "sma_short": sma_short,
                        "sma_long": sma_long,
                        "rsi_oversold": rsi_oversold,
                        "rsi_overbought": rsi_overbought,
                        "stop_loss": 0.05,
                        "take_profit": 0.10,
                    }

                    # Backtest with these parameters
                    result = backtest_strategy(prices, indicators, params)
                    result["params"] = params

                    all_results.append(result)

                    # Track best result
                    if result["sharpe_ratio"] > best_sharpe:
                        best_sharpe = result["sharpe_ratio"]
                        best_params = params.copy()

                    # Progress update
                    if combination_count % 50 == 0:
                        print(
                            f"  Tested {combination_count} combinations... "
                            f"Best Sharpe: {best_sharpe:.3f}"
                        )

    return best_params, all_results


def generate_market_data(
    n_days: int = 500,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate realistic market data for testing."""

    np.random.seed(42)  # For reproducible results

    # Generate price movements with trend and volatility
    base_trend = 0.0005  # Daily trend
    volatility = 0.02  # Daily volatility

    # Add some regime changes (bull/bear markets)
    regime_changes = np.random.choice([0.8, 1.0, 1.2], n_days)

    returns = np.random.normal(base_trend, volatility, n_days) * regime_changes

    # Generate prices from returns
    initial_price = 100.0
    prices = np.zeros(n_days)
    prices[0] = initial_price

    for i in range(1, n_days):
        prices[i] = prices[i - 1] * (1 + returns[i])

    # Add some realistic patterns
    # Occasional large moves (simulate news events)
    large_moves = np.random.choice([0, 1], n_days, p=[0.95, 0.05])
    large_move_size = np.random.normal(0, 0.05, n_days)
    prices = prices * (1 + large_moves * large_move_size)

    # Generate volume (correlated with volatility)
    base_volume = 1000000
    volume_volatility = np.abs(returns) * 5  # Higher volume on volatile days
    volume = np.random.lognormal(np.log(base_volume), 0.3 + volume_volatility)

    # Create dates
    dates = pd.date_range("2022-01-01", periods=n_days, freq="D")

    return prices, volume, dates


def visualize_results(
    prices: np.ndarray,
    portfolio_values: np.ndarray,
    indicators: Dict,
    trades: List,
    dates: np.ndarray,
):
    """Create comprehensive visualization of trading results."""

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Trading Strategy Performance Analysis", fontsize=16)

    # Plot 1: Price chart with indicators
    ax1.plot(dates, prices, label="Price", alpha=0.7)
    ax1.plot(dates, indicators["sma_20"], label="SMA 20", alpha=0.8)
    ax1.plot(dates, indicators["sma_50"], label="SMA 50", alpha=0.8)
    ax1.fill_between(
        dates,
        indicators["bb_lower"],
        indicators["bb_upper"],
        alpha=0.2,
        label="Bollinger Bands",
    )

    # Mark trades
    for trade in trades:
        if trade["type"] == "BUY":
            ax1.scatter(
                dates[trade["day"]],
                trade["price"],
                color="green",
                marker="^",
                s=100,
                alpha=0.7,
            )
        else:
            ax1.scatter(
                dates[trade["day"]],
                trade["price"],
                color="red",
                marker="v",
                s=100,
                alpha=0.7,
            )

    ax1.set_title("Price Chart with Indicators")
    ax1.set_ylabel("Price ($)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Portfolio value vs buy-and-hold
    initial_price = prices[0]
    buy_hold_values = prices * (portfolio_values[0] / initial_price)

    ax2.plot(dates, portfolio_values, label="Strategy", linewidth=2)
    ax2.plot(dates, buy_hold_values, label="Buy & Hold", alpha=0.7)
    ax2.set_title("Portfolio Performance Comparison")
    ax2.set_ylabel("Portfolio Value ($)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: RSI
    ax3.plot(dates, indicators["rsi"])
    ax3.axhline(y=70, color="r", linestyle="--", alpha=0.7, label="Overbought")
    ax3.axhline(y=30, color="g", linestyle="--", alpha=0.7, label="Oversold")
    ax3.set_title("RSI Indicator")
    ax3.set_ylabel("RSI")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Drawdown
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - peak) / peak * 100

    ax4.fill_between(dates, drawdown, 0, alpha=0.5, color="red")
    ax4.set_title("Portfolio Drawdown")
    ax4.set_ylabel("Drawdown (%)")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the plot
    output_path = (
        "/Users/julio/Projects/python-optimizer/examples/trading_strategy_analysis.png"
    )
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Trading analysis chart saved to: {output_path}")

    try:
        plt.show()
    except:
        print("Chart created but not displayed (non-interactive environment)")


def main():
    """Run the complete trading strategy optimization example."""

    print("📈 TRADING STRATEGY OPTIMIZATION")
    print("=" * 60)
    print(
        "Demonstrating high-performance trading strategy backtesting with Python Optimizer"
    )
    print()

    # Generate market data
    print("🏗️  Generating market data...")
    prices, volume, dates = generate_market_data(n_days=500)
    print(f"Generated {len(prices)} days of market data")
    print(f"Price range: ${prices.min():.2f} - ${prices.max():.2f}")

    # Calculate technical indicators
    print("\n📊 Calculating technical indicators...")
    start_time = time.perf_counter()
    indicators = calculate_technical_indicators(prices, volume)
    indicator_time = time.perf_counter() - start_time
    print(f"Technical indicators calculated in {indicator_time*1000:.2f}ms")

    # Test single strategy
    print("\n🧪 Testing single strategy configuration...")
    test_params = {
        "sma_short": 20,
        "sma_long": 50,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss": 0.05,
        "take_profit": 0.10,
    }

    start_time = time.perf_counter()
    single_result = backtest_strategy(prices, indicators, test_params)
    backtest_time = time.perf_counter() - start_time

    print(f"Single backtest completed in {backtest_time*1000:.2f}ms")
    print(f"Results:")
    print(f"  Total Return: {single_result['total_return']:8.2%}")
    print(f"  Annual Return: {single_result['annual_return']:8.2%}")
    print(f"  Volatility: {single_result['volatility']:8.2%}")
    print(f"  Sharpe Ratio: {single_result['sharpe_ratio']:8.2f}")
    print(f"  Max Drawdown: {single_result['max_drawdown']:8.2%}")
    print(f"  Number of Trades: {single_result['num_trades']}")
    print(f"  Win Rate: {single_result['win_rate']:8.1%}")

    # Parameter optimization
    print("\n🔧 Optimizing strategy parameters...")
    param_ranges = {
        "sma_short": [10, 15, 20, 25],
        "sma_long": [40, 50, 60, 70],
        "rsi_oversold": [25, 30, 35],
        "rsi_overbought": [65, 70, 75],
    }

    start_time = time.perf_counter()
    best_params, all_results = optimize_strategy_parameters(
        prices, indicators, param_ranges
    )
    optimization_time = time.perf_counter() - start_time

    print(f"\nParameter optimization completed in {optimization_time:.2f} seconds")
    print(f"Tested {len(all_results)} parameter combinations")

    # Find best result
    best_result = max(all_results, key=lambda x: x["sharpe_ratio"])

    print(f"\n🏆 Best Strategy Configuration:")
    print(f"Parameters: {best_params}")
    print(f"Performance:")
    print(f"  Total Return: {best_result['total_return']:8.2%}")
    print(f"  Annual Return: {best_result['annual_return']:8.2%}")
    print(f"  Sharpe Ratio: {best_result['sharpe_ratio']:8.2f}")
    print(f"  Max Drawdown: {best_result['max_drawdown']:8.2%}")
    print(f"  Win Rate: {best_result['win_rate']:8.1%}")

    # Performance statistics
    print(f"\n⚡ Performance Statistics:")

    # Technical indicators
    stats = get_specialization_stats("calculate_technical_indicators")
    print(f"Technical Indicators:")
    print(f"  Specializations: {stats.get('specializations_created', 0)}")
    print(f"  Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    # Backtesting
    stats = get_specialization_stats("backtest_strategy")
    print(f"Strategy Backtesting:")
    print(f"  Specializations: {stats.get('specializations_created', 0)}")
    print(f"  Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    print(f"  Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    # Parameter optimization
    stats = get_specialization_stats("optimize_strategy_parameters")
    print(f"Parameter Optimization:")
    print(f"  Specializations: {stats.get('specializations_created', 0)}")
    print(f"  Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")

    # Calculate throughput
    total_backtests = len(all_results) + 1  # +1 for single test
    throughput = total_backtests / (optimization_time + backtest_time)
    print(f"\n📊 Throughput: {throughput:.1f} backtests/second")

    # Create visualization
    print(f"\n📊 Creating performance visualization...")
    visualize_results(
        prices,
        best_result["portfolio_values"],
        indicators,
        best_result["trades"],
        dates,
    )

    print(f"\n✅ Trading strategy optimization completed successfully!")
    print(
        f"🚀 Achieved {throughput:.1f} backtests per second with specialized optimization"
    )


if __name__ == "__main__":
    main()
