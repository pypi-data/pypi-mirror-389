"""
Tests for the Python Optimizer CLI.
"""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from python_optimizer import __version__
from python_optimizer.cli import main, run_benchmark, run_example, show_stats


class TestCLIFunctions:
    """Test individual CLI functions."""

    def test_run_example_success(self):
        """Test run_example when example is available."""
        with patch("examples.basic_optimization.main") as mock_main:
            mock_main.return_value = None
            result = run_example()
            assert result == 0

    def test_run_example_import_error(self, capsys):
        """Test run_example when example is not available."""
        with patch(
            "examples.basic_optimization.main",
            side_effect=ImportError("No module"),
        ):
            result = run_example()
            captured = capsys.readouterr()
            assert result == 1
            assert "Example not found" in captured.out

    def test_run_benchmark_success(self):
        """Test run_benchmark when benchmark is available."""
        # Mock the import itself since trading_optimizer isn't available
        import sys
        from unittest.mock import MagicMock

        mock_module = MagicMock()
        mock_module.run_comprehensive_test = MagicMock(return_value=None)
        sys.modules["trading_optimizer"] = MagicMock()
        sys.modules["trading_optimizer.genetic_optimizer"] = MagicMock()
        sys.modules["trading_optimizer.jit_fitness_evaluator"] = MagicMock()

        try:
            with patch(
                "python_optimizer.benchmarks.test_jit_performance.run_comprehensive_test"
            ) as mock_bench:
                mock_bench.return_value = None
                result = run_benchmark()
                assert result == 0
        finally:
            # Clean up mocked modules
            sys.modules.pop("trading_optimizer", None)
            sys.modules.pop("trading_optimizer.genetic_optimizer", None)
            sys.modules.pop("trading_optimizer.jit_fitness_evaluator", None)

    def test_run_benchmark_import_error(self, capsys):
        """Test run_benchmark when benchmark is not available."""
        # Ensure trading_optimizer isn't available
        import sys

        modules_to_remove = [
            "trading_optimizer",
            "trading_optimizer.genetic_optimizer",
            "trading_optimizer.jit_fitness_evaluator",
            "python_optimizer.benchmarks.test_jit_performance",
        ]
        removed_modules = {}
        for mod in modules_to_remove:
            if mod in sys.modules:
                removed_modules[mod] = sys.modules.pop(mod)

        try:
            result = run_benchmark()
            captured = capsys.readouterr()
            assert result == 1
            assert "Benchmark not available" in captured.out
        finally:
            # Restore modules
            sys.modules.update(removed_modules)

    def test_show_stats_empty(self, capsys):
        """Test show_stats with no performance data."""
        with patch(
            "python_optimizer.core.decorator.get_optimization_stats"
        ) as mock_opt_stats:
            with patch(
                "python_optimizer.profiling.get_performance_stats"
            ) as mock_perf_stats:
                mock_opt_stats.return_value = {
                    "optimized_functions": 0,
                    "jit_compilations": 0,
                }
                mock_perf_stats.return_value = {}

                result = show_stats()
                captured = capsys.readouterr()

                assert result == 0
                assert "Optimization Statistics" in captured.out
                assert "Performance Statistics" in captured.out
                assert "No performance data available" in captured.out

    def test_show_stats_with_data(self, capsys):
        """Test show_stats with performance data."""
        with patch(
            "python_optimizer.core.decorator.get_optimization_stats"
        ) as mock_opt_stats:
            with patch(
                "python_optimizer.profiling.get_performance_stats"
            ) as mock_perf_stats:
                mock_opt_stats.return_value = {
                    "optimized_functions": 5,
                    "jit_compilations": 3,
                    "cache_hits": 10,
                }
                mock_perf_stats.return_value = {
                    "test_function": {
                        "call_count": 100,
                        "avg_time": 0.001,
                    }
                }

                result = show_stats()
                captured = capsys.readouterr()

                assert result == 0
                assert "Optimization Statistics" in captured.out
                assert "optimized_functions: 5" in captured.out
                assert "test_function" in captured.out
                assert "call_count: 100" in captured.out


class TestCLIMain:
    """Test main CLI entry point."""

    def test_main_no_args(self, capsys):
        """Test main with no arguments (shows help)."""
        with patch.object(sys, "argv", ["python-optimizer"]):
            result = main()
            captured = capsys.readouterr()
            assert result == 0
            assert "Python Optimizer" in captured.out

    def test_main_version(self, capsys):
        """Test --version flag."""
        with patch.object(sys, "argv", ["python-optimizer", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_example_command(self):
        """Test 'example' command."""
        with patch.object(sys, "argv", ["python-optimizer", "example"]):
            with patch("python_optimizer.cli.run_example") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_benchmark_command(self):
        """Test 'benchmark' command."""
        with patch.object(sys, "argv", ["python-optimizer", "benchmark"]):
            with patch("python_optimizer.cli.run_benchmark") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_stats_command(self):
        """Test 'stats' command."""
        with patch.object(sys, "argv", ["python-optimizer", "stats"]):
            with patch("python_optimizer.cli.show_stats") as mock_show:
                mock_show.return_value = 0
                result = main()
                assert result == 0
                mock_show.assert_called_once()

    def test_main_example_command_failure(self):
        """Test 'example' command when it fails."""
        with patch.object(sys, "argv", ["python-optimizer", "example"]):
            with patch("python_optimizer.cli.run_example") as mock_run:
                mock_run.return_value = 1
                result = main()
                assert result == 1

    def test_main_benchmark_command_failure(self):
        """Test 'benchmark' command when it fails."""
        with patch.object(sys, "argv", ["python-optimizer", "benchmark"]):
            with patch("python_optimizer.cli.run_benchmark") as mock_run:
                mock_run.return_value = 1
                result = main()
                assert result == 1


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_cli_stats_integration(self, capsys):
        """Test stats command with actual imports."""
        # Import the actual functions
        from python_optimizer.core.decorator import get_optimization_stats
        from python_optimizer.profiling import get_performance_stats

        # Call show_stats
        result = show_stats()
        captured = capsys.readouterr()

        assert result == 0
        assert "Optimization Statistics" in captured.out
        assert "Performance Statistics" in captured.out

    def test_argparse_help_content(self, capsys):
        """Test that argparse help contains expected content."""
        with patch.object(sys, "argv", ["python-optimizer", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            captured = capsys.readouterr()
            assert "Python Optimizer" in captured.out
            assert "High-performance optimization toolkit" in captured.out
            assert "example" in captured.out
            assert "benchmark" in captured.out
            assert "stats" in captured.out
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
