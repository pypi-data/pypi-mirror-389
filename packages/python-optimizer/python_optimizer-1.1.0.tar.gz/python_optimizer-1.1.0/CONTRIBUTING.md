# Contributing to Python Optimizer

Thank you for your interest in contributing to Python Optimizer! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Development Environment Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/thinmanj/python-optimizer.git
   cd python-optimizer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## 🛠 Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

Run all checks:
```bash
black python_optimizer/
isort python_optimizer/
flake8 python_optimizer/
mypy python_optimizer/
```

### Testing

We use pytest for testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=python_optimizer

# Run specific test file
pytest tests/test_jit.py

# Run benchmarks (marked as slow)
pytest -m benchmark
```

Test guidelines:
- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Include both unit and integration tests

### Performance Testing

For performance-critical changes:

```bash
# Run JIT performance tests
python python_optimizer/benchmarks/test_jit_performance.py

# Run genetic algorithm benchmarks  
python python_optimizer/benchmarks/genetic_benchmark.py
```

## 📝 Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Run the test suite:**
   ```bash
   pytest
   black python_optimizer/
   flake8 python_optimizer/
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We follow conventional commits:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/modifications
- `perf:` - Performance improvements
- `refactor:` - Code refactoring
- `ci:` - CI/CD changes

## 🎯 Areas for Contribution

### High Priority
- **GPU acceleration** - CUDA support for JIT functions
- **More JIT functions** - Additional financial/numerical computations
- **ML integration** - PyTorch/TensorFlow optimization hooks
- **Documentation** - API docs, tutorials, examples

### Medium Priority  
- **CLI tools** - Command-line interface for benchmarking
- **Configuration system** - Better config file support
- **Profiling improvements** - More detailed performance analytics
- **Type annotations** - Complete type coverage

### Low Priority
- **Web interface** - Browser-based optimization dashboard
- **Distributed computing** - Multi-node optimization
- **Alternative backends** - JAX, CuPy support

## 🧪 Testing New Optimizations

When adding new JIT functions:

1. **Create the JIT version:**
   ```python
   @njit(cache=True, fastmath=True)
   def your_function_jit(data: np.ndarray) -> float:
       # Numba-compatible implementation
       pass
   ```

2. **Add comprehensive tests:**
   ```python
   def test_your_function_jit():
       data = np.random.random(1000)
       expected = your_function_reference(data)
       result = your_function_jit(data)
       np.testing.assert_allclose(result, expected)
   ```

3. **Add benchmark:**
   ```python
   def benchmark_your_function():
       # Compare JIT vs non-JIT performance
       pass
   ```

## 🐛 Bug Reports

When reporting bugs, please include:

- **Python version** and OS
- **Minimal reproducible example**
- **Error messages and stack traces**
- **Expected vs actual behavior**
- **Performance context** if applicable

Use the bug report template in GitHub issues.

## 💡 Feature Requests

For new features:

- **Check existing issues** first
- **Provide clear use case** and motivation
- **Consider performance implications**
- **Suggest implementation approach**

## 📚 Documentation

Documentation improvements are always welcome:

- **API documentation** - Docstring improvements
- **Tutorials** - Step-by-step guides
- **Examples** - Real-world usage scenarios
- **Performance guides** - Optimization best practices

## ⚡ Performance Standards

All contributions should maintain performance standards:

- **JIT functions** should be 10x+ faster than pure Python
- **Memory usage** should not increase significantly
- **Compilation time** should be reasonable (< 5s for typical functions)
- **Benchmark results** should be included for performance changes

## 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Share knowledge** about optimization techniques
- **Credit contributions** appropriately

## 📞 Getting Help

- **GitHub Discussions** - General questions and ideas
- **GitHub Issues** - Bug reports and feature requests
- **Code reviews** - Detailed feedback on contributions

Thank you for contributing to Python Optimizer! 🚀
