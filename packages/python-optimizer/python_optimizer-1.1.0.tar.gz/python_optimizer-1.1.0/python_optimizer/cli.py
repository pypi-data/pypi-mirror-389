#!/usr/bin/env python3
"""
Command-line interface for Python Optimizer.
"""

import argparse
import sys

from python_optimizer import __version__


def run_example():
    """Run the basic optimization example."""
    try:
        from examples.basic_optimization import main

        main()
    except ImportError:
        print("Example not found. Please install python-optimizer with examples.")
        return 1
    return 0


def run_benchmark():
    """Run JIT performance benchmarks."""
    try:
        from python_optimizer.benchmarks.test_jit_performance import (
            run_comprehensive_test,
        )

        run_comprehensive_test()
    except ImportError as e:
        print(f"Benchmark not available: {e}")
        return 1
    return 0


def show_stats():
    """Show optimization statistics."""
    from python_optimizer.core.decorator import get_optimization_stats
    from python_optimizer.profiling import get_performance_stats

    print("=== Optimization Statistics ===")
    opt_stats = get_optimization_stats()
    for key, value in opt_stats.items():
        print(f"{key}: {value}")

    print("\n=== Performance Statistics ===")
    perf_stats = get_performance_stats()
    if perf_stats:
        for func_name, stats in perf_stats.items():
            print(f"\n{func_name}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
    else:
        print("No performance data available.")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Python Optimizer - High-performance optimization toolkit",
        prog="python-optimizer",
    )

    parser.add_argument(
        "--version", action="version", version=f"python-optimizer {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Example command
    example_parser = subparsers.add_parser(
        "example", help="Run basic optimization examples"
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Run performance benchmarks"
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show optimization and performance statistics"
    )

    args = parser.parse_args()

    if args.command == "example":
        return run_example()
    elif args.command == "benchmark":
        return run_benchmark()
    elif args.command == "stats":
        return show_stats()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
