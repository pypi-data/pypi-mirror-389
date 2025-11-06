#!/usr/bin/env python3
"""
High-Frequency Trading Simulation

Demonstrates JIT optimization for latency-critical HFT systems including:
- Order book processing
- Market data feed handling
- Risk management calculations
- Portfolio optimization
- Latency measurement and optimization
"""

import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from python_optimizer import optimize

# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class Order:
    """Trading order representation."""

    order_id: int
    symbol: str
    side: int  # 1 for buy, -1 for sell
    price: float
    quantity: int
    timestamp: float


@dataclass
class Trade:
    """Trade execution representation."""

    symbol: str
    price: float
    quantity: int
    timestamp: float
    aggressor_side: int


@dataclass
class MarketData:
    """Market data tick."""

    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: float


# =============================================================================
# Order Book Management (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def process_order_book_update(
    prices, quantities, sides, new_price, new_quantity, new_side
):
    """JIT-optimized order book update processing."""
    n_levels = len(prices)

    # Find insertion point
    insert_idx = -1
    if new_side == 1:  # Buy order - descending price order
        for i in range(n_levels):
            if prices[i] <= new_price:
                insert_idx = i
                break
    else:  # Sell order - ascending price order
        for i in range(n_levels):
            if prices[i] >= new_price:
                insert_idx = i
                break

    if insert_idx == -1:
        insert_idx = n_levels

    # Check if price level exists
    existing_idx = -1
    for i in range(n_levels):
        if abs(prices[i] - new_price) < 1e-6:  # Price match
            existing_idx = i
            break

    if existing_idx >= 0:
        # Update existing level
        quantities[existing_idx] += new_quantity
        if quantities[existing_idx] <= 0:
            # Remove level
            for i in range(existing_idx, n_levels - 1):
                prices[i] = prices[i + 1]
                quantities[i] = quantities[i + 1]
                sides[i] = sides[i + 1]
            return n_levels - 1
    else:
        # Insert new level
        if insert_idx < n_levels:
            # Shift existing levels
            for i in range(n_levels - 1, insert_idx - 1, -1):
                if i + 1 < len(prices):
                    prices[i + 1] = prices[i]
                    quantities[i + 1] = quantities[i]
                    sides[i + 1] = sides[i]

        if insert_idx < len(prices):
            prices[insert_idx] = new_price
            quantities[insert_idx] = new_quantity
            sides[insert_idx] = new_side

    return n_levels


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_vwap(prices, quantities, max_levels=10):
    """JIT-optimized Volume Weighted Average Price calculation."""
    total_value = 0.0
    total_volume = 0.0

    for i in range(min(len(prices), max_levels)):
        if quantities[i] > 0:
            total_value += prices[i] * quantities[i]
            total_volume += quantities[i]

    if total_volume > 0:
        return total_value / total_volume
    return 0.0


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_spread_metrics(bid_prices, bid_quantities, ask_prices, ask_quantities):
    """JIT-optimized spread and liquidity metrics."""
    if len(bid_prices) == 0 or len(ask_prices) == 0:
        return 0.0, 0.0, 0.0, 0.0

    best_bid = bid_prices[0] if bid_quantities[0] > 0 else 0.0
    best_ask = ask_prices[0] if ask_quantities[0] > 0 else 0.0

    if best_bid <= 0 or best_ask <= 0:
        return 0.0, 0.0, 0.0, 0.0

    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2.0
    spread_bps = (spread / mid_price) * 10000.0 if mid_price > 0 else 0.0

    # Calculate liquidity depth
    liquidity_depth = 0.0
    max_levels = min(len(bid_prices), len(ask_prices), 5)
    for i in range(max_levels):
        if bid_quantities[i] > 0:
            liquidity_depth += bid_quantities[i]
        if ask_quantities[i] > 0:
            liquidity_depth += ask_quantities[i]

    return spread, mid_price, spread_bps, liquidity_depth


# =============================================================================
# Market Data Processing (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def process_market_data_tick(
    prices_buffer,
    volumes_buffer,
    timestamps_buffer,
    new_price,
    new_volume,
    new_timestamp,
    buffer_size,
):
    """JIT-optimized market data tick processing with circular buffer."""
    # Find insertion index (circular buffer)
    insert_idx = 0
    latest_time = 0.0

    for i in range(buffer_size):
        if timestamps_buffer[i] > latest_time:
            latest_time = timestamps_buffer[i]
            insert_idx = (i + 1) % buffer_size

    # Insert new data
    prices_buffer[insert_idx] = new_price
    volumes_buffer[insert_idx] = new_volume
    timestamps_buffer[insert_idx] = new_timestamp

    return insert_idx


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_technical_indicators(prices, volumes, window_size):
    """JIT-optimized technical indicator calculation."""
    n = len(prices)
    if n < window_size:
        return 0.0, 0.0, 0.0, 0.0

    # Moving averages
    sma = 0.0
    volume_sma = 0.0
    for i in range(window_size):
        sma += prices[n - 1 - i]
        volume_sma += volumes[n - 1 - i]
    sma /= window_size
    volume_sma /= window_size

    # Volatility (standard deviation)
    variance = 0.0
    for i in range(window_size):
        diff = prices[n - 1 - i] - sma
        variance += diff * diff
    volatility = np.sqrt(variance / window_size)

    # Momentum (price change)
    momentum = prices[n - 1] - prices[n - window_size] if n >= window_size else 0.0

    return sma, volatility, momentum, volume_sma


# =============================================================================
# Risk Management (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_portfolio_risk(positions, prices, position_limits, price_volatilities):
    """JIT-optimized portfolio risk calculation."""
    n_positions = len(positions)

    total_exposure = 0.0
    total_var = 0.0  # Value at Risk
    max_exposure_breach = 0.0

    for i in range(n_positions):
        if positions[i] != 0:
            exposure = abs(positions[i] * prices[i])
            total_exposure += exposure

            # Position limit breach
            if abs(positions[i]) > position_limits[i]:
                breach = abs(positions[i]) - position_limits[i]
                max_exposure_breach = max(max_exposure_breach, breach)

            # VaR calculation (simplified)
            volatility = price_volatilities[i] if i < len(price_volatilities) else 0.01
            position_var = exposure * volatility * 2.33  # 99% confidence
            total_var += position_var * position_var

    total_var = np.sqrt(total_var)

    return total_exposure, total_var, max_exposure_breach


@optimize(jit=True, fastmath=True, nogil=True)
def validate_order_risk(position, new_quantity, price, position_limit, max_order_value):
    """JIT-optimized order risk validation."""
    new_position = position + new_quantity

    # Position limit check
    if abs(new_position) > position_limit:
        return False, 1  # Position limit exceeded

    # Order value check
    order_value = abs(new_quantity * price)
    if order_value > max_order_value:
        return False, 2  # Order value exceeded

    return True, 0


# =============================================================================
# Latency Optimization
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def ultra_fast_price_calculation(base_price, adjustments, weights, n_adjustments):
    """Ultra-fast price calculation for latency-critical operations."""
    adjusted_price = base_price

    for i in range(n_adjustments):
        adjusted_price += adjustments[i] * weights[i]

    return adjusted_price


@optimize(jit=True, fastmath=True, nogil=True)
def fast_order_matching(
    buy_prices, buy_quantities, sell_prices, sell_quantities, max_levels
):
    """JIT-optimized order matching engine."""
    matched_volume = 0.0
    matched_value = 0.0

    buy_idx = 0
    sell_idx = 0

    while buy_idx < max_levels and sell_idx < max_levels:
        if buy_quantities[buy_idx] <= 0:
            buy_idx += 1
            continue
        if sell_quantities[sell_idx] <= 0:
            sell_idx += 1
            continue

        if buy_prices[buy_idx] >= sell_prices[sell_idx]:
            # Match possible
            match_quantity = min(buy_quantities[buy_idx], sell_quantities[sell_idx])
            match_price = (buy_prices[buy_idx] + sell_prices[sell_idx]) / 2.0

            matched_volume += match_quantity
            matched_value += match_quantity * match_price

            buy_quantities[buy_idx] -= match_quantity
            sell_quantities[sell_idx] -= match_quantity
        else:
            break

    return matched_volume, matched_value


# =============================================================================
# High-Frequency Trading Strategy
# =============================================================================


class HFTStrategy:
    """High-frequency trading strategy implementation."""

    def __init__(self):
        self.positions = {}
        self.pnl = 0.0
        self.trade_count = 0
        self.latency_stats = []

    @optimize(jit=True, fastmath=True, nogil=True)
    def _calculate_signal(self, price_history, volume_history, window_size):
        """JIT-optimized signal calculation."""
        if len(price_history) < window_size:
            return 0.0

        # Simple mean reversion signal
        recent_prices = price_history[-window_size:]
        mean_price = 0.0
        for i in range(window_size):
            mean_price += recent_prices[i]
        mean_price /= window_size

        current_price = price_history[-1]
        deviation = (current_price - mean_price) / mean_price

        # Mean reversion signal
        if deviation > 0.002:  # Price too high, sell signal
            return -1.0
        elif deviation < -0.002:  # Price too low, buy signal
            return 1.0
        else:
            return 0.0

    def process_market_data(self, market_data: MarketData):
        """Process market data and generate signals."""
        start_time = time.perf_counter()

        # Simulate price history (in real implementation, this would be maintained)
        price_history = np.array([market_data.bid + i * 0.01 for i in range(50)])
        volume_history = np.array([1000 + i * 10 for i in range(50)])

        signal = self._calculate_signal(price_history, volume_history, 20)

        # Execute if signal is strong enough
        if abs(signal) > 0.5:
            self._execute_trade(market_data.symbol, signal, market_data)

        end_time = time.perf_counter()
        latency_us = (end_time - start_time) * 1_000_000
        self.latency_stats.append(latency_us)

    def _execute_trade(self, symbol: str, signal: float, market_data: MarketData):
        """Execute trade based on signal."""
        if signal > 0:  # Buy
            price = market_data.ask
            quantity = 100
        else:  # Sell
            price = market_data.bid
            quantity = -100

        # Update position
        current_position = self.positions.get(symbol, 0)
        self.positions[symbol] = current_position + quantity

        # Update PnL (simplified)
        self.pnl += -quantity * price  # Cost basis
        self.trade_count += 1


# =============================================================================
# Simulation and Benchmarking
# =============================================================================


def generate_synthetic_market_data(n_ticks: int = 10000) -> List[MarketData]:
    """Generate synthetic market data for testing."""
    market_data = []
    base_price = 100.0

    for i in range(n_ticks):
        # Random walk with some trend
        price_change = np.random.normal(0, 0.01)
        base_price += price_change

        spread = 0.02 + np.random.exponential(0.01)
        bid = base_price - spread / 2
        ask = base_price + spread / 2

        bid_size = np.random.poisson(1000)
        ask_size = np.random.poisson(1000)

        tick = MarketData(
            symbol="AAPL",
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            timestamp=time.time() + i * 0.001,
        )
        market_data.append(tick)

    return market_data


def benchmark_hft_system():
    """Comprehensive HFT system benchmark."""
    print("🚀 High-Frequency Trading System Benchmark")
    print("=" * 60)

    # Generate market data
    print("\n📊 Generating synthetic market data...")
    market_data = generate_synthetic_market_data(10000)
    print(f"Generated {len(market_data)} market data ticks")

    # Initialize strategy
    strategy = HFTStrategy()

    # Benchmark order book operations
    print("\n📈 Order Book Processing")
    print("-" * 30)

    prices = np.array([100.1, 100.0, 99.9, 99.8, 99.7])
    quantities = np.array([1000, 1500, 2000, 1200, 800])
    sides = np.array([1, 1, 1, 1, 1])  # All buy orders

    start_time = time.perf_counter()
    for _ in range(1000):
        new_price = 99.95 + np.random.normal(0, 0.05)
        new_quantity = np.random.poisson(1000)
        process_order_book_update(prices, quantities, sides, new_price, new_quantity, 1)
    orderbook_time = time.perf_counter() - start_time

    print(f"Order book updates: {orderbook_time:.4f}s (1000 updates)")
    print(f"Average per update: {orderbook_time/1000*1000:.2f}μs")

    # Benchmark market data processing
    print("\n📡 Market Data Processing")
    print("-" * 30)

    start_time = time.perf_counter()
    processed_count = 0

    for tick in market_data[:5000]:  # Process subset for timing
        strategy.process_market_data(tick)
        processed_count += 1

    processing_time = time.perf_counter() - start_time
    avg_latency = np.mean(strategy.latency_stats)
    p99_latency = np.percentile(strategy.latency_stats, 99)

    print(f"Market data processing: {processing_time:.4f}s ({processed_count} ticks)")
    print(f"Throughput:            {processed_count/processing_time:.0f} ticks/second")
    print(f"Average latency:       {avg_latency:.2f}μs")
    print(f"99th percentile:       {p99_latency:.2f}μs")

    # Benchmark risk calculations
    print("\n⚖️ Risk Management")
    print("-" * 30)

    positions = np.array([1000, -500, 2000, -1000, 800])
    prices = np.array([100.0, 50.0, 200.0, 150.0, 75.0])
    limits = np.array([2000, 1000, 3000, 1500, 1200])
    volatilities = np.array([0.02, 0.03, 0.025, 0.015, 0.035])

    start_time = time.perf_counter()
    for _ in range(10000):
        exposure, var, breach = calculate_portfolio_risk(
            positions, prices, limits, volatilities
        )
    risk_time = time.perf_counter() - start_time

    print(f"Risk calculations:     {risk_time:.4f}s (10000 calculations)")
    print(f"Average per calc:      {risk_time/10000*1000:.2f}μs")

    # Benchmark order matching
    print("\n🔄 Order Matching")
    print("-" * 30)

    buy_prices = np.array([100.05, 100.04, 100.03, 100.02, 100.01])
    buy_quantities = np.array([1000, 1500, 2000, 1200, 800])
    sell_prices = np.array([100.06, 100.07, 100.08, 100.09, 100.10])
    sell_quantities = np.array([900, 1100, 1800, 1400, 700])

    start_time = time.perf_counter()
    for _ in range(10000):
        volume, value = fast_order_matching(
            buy_prices.copy(),
            buy_quantities.copy(),
            sell_prices.copy(),
            sell_quantities.copy(),
            5,
        )
    matching_time = time.perf_counter() - start_time

    print(f"Order matching:        {matching_time:.4f}s (10000 matches)")
    print(f"Average per match:     {matching_time/10000*1000:.2f}μs")

    # Strategy performance
    print("\n🎯 Strategy Performance")
    print("-" * 30)
    print(f"Total trades:          {strategy.trade_count}")
    print(f"Final PnL:             ${strategy.pnl:.2f}")
    print(
        f"Positions:             {len([p for p in strategy.positions.values() if p != 0])} active"
    )

    # Summary
    print("\n🏆 HFT System Performance Summary")
    print("=" * 60)
    print(
        f"Market Data Throughput:    {processed_count/processing_time:.0f} ticks/second"
    )
    print(f"Average Processing Latency: {avg_latency:.2f}μs")
    print(f"Order Book Update Speed:   {1000/orderbook_time:.0f} updates/second")
    print(f"Risk Calculation Speed:    {10000/risk_time:.0f} calculations/second")
    print(f"Order Matching Speed:      {10000/matching_time:.0f} matches/second")

    return {
        "throughput": processed_count / processing_time,
        "avg_latency_us": avg_latency,
        "p99_latency_us": p99_latency,
        "trades_executed": strategy.trade_count,
        "final_pnl": strategy.pnl,
    }


if __name__ == "__main__":
    results = benchmark_hft_system()
    print("\n✨ High-frequency trading simulation complete!")
