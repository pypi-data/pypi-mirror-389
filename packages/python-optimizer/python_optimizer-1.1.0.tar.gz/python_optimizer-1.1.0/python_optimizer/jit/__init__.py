"""
JIT compilation module with Numba-optimized functions for high-performance computing.
"""

from .jit_fitness_evaluator import (
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

__all__ = [
    "calculate_returns_jit",
    "calculate_sharpe_ratio_jit",
    "calculate_max_drawdown_jit",
    "calculate_profit_factor_jit",
    "calculate_win_rate_jit",
    "simulate_strategy_jit",
    "generate_ma_signals_jit",
    "generate_rsi_signals_jit",
    "JITBacktestFitnessEvaluator",
    "NUMBA_AVAILABLE",
]
