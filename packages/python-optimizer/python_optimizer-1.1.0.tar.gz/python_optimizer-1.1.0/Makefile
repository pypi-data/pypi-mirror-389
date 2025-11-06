.PHONY: help install install-dev test test-cov lint format type-check clean benchmark docs build publish

# Default target
help:
	@echo "Python Optimizer Development Commands"
	@echo "===================================="
	@echo "install          Install package"
	@echo "install-dev      Install package with development dependencies"
	@echo "test            Run test suite"
	@echo "test-cov        Run tests with coverage"
	@echo "lint            Run linting (flake8)"
	@echo "format          Format code (black + isort)"
	@echo "type-check      Run type checking (mypy)"
	@echo "pre-commit      Run pre-commit hooks"
	@echo "clean           Clean up build artifacts"
	@echo "benchmark       Run performance benchmarks"
	@echo "docs            Build documentation"
	@echo "build           Build package"
	@echo "publish         Publish package to PyPI"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/

test-cov:
	pytest tests/ --cov=python_optimizer --cov-report=html --cov-report=term-missing

test-all:
	pytest tests/ --cov=python_optimizer --cov-report=html --cov-report=xml --junitxml=test-results.xml

# Code quality
lint:
	flake8 python_optimizer/
	flake8 tests/ --ignore=F401,F811

format:
	black python_optimizer/ tests/ examples/
	isort python_optimizer/ tests/ examples/

type-check:
	mypy python_optimizer/

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

# Benchmarks
benchmark:
	python python_optimizer/benchmarks/test_jit_performance.py

benchmark-all:
	python examples/ml_optimization.py
	python examples/hft_simulation.py
	python examples/distributed_computing.py

# Documentation
docs:
	@echo "Documentation build not yet implemented"
	# sphinx-build -b html docs/ docs/_build/

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build and publish
build: clean
	python -m build

publish: build
	twine check dist/*
	twine upload dist/*

publish-test: build
	twine check dist/*
	twine upload --repository testpypi dist/*

# Development environment setup
setup-dev: install-dev pre-commit-install
	@echo "Development environment set up successfully!"
	@echo "Run 'make test' to verify installation"

# Git hooks
install-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Performance profiling
profile:
	python -m cProfile -o profile.stats examples/basic_optimization.py
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('tottime').print_stats(20)"

# Security checks
security:
	safety check
	bandit -r python_optimizer/

# CI/CD helper
ci-check:
	python3 scripts/ci_cd_helper.py --step all

ci-lint:
	python3 scripts/ci_cd_helper.py --step lint

ci-format-check:
	python3 scripts/ci_cd_helper.py --step format

ci-format-fix:
	python3 scripts/ci_cd_helper.py --fix

ci-test:
	python3 scripts/ci_cd_helper.py --step test

ci-build:
	python3 scripts/ci_cd_helper.py --step build
