# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Python Optimizer is a high-performance optimization toolkit that accelerates Python code execution by 10-500x through JIT compilation (Numba), intelligent variable specialization, adaptive caching, and runtime optimizations—all without changing language syntax.

**Core Technologies:**
- **JIT Compilation Engine**: Numba-powered optimization with custom passes
- **Variable Specialization**: Type-aware automatic specialization with caching (up to 400x speedup)
- **Intelligent Caching System**: Multi-policy cache (LRU, LFU, TTL, Adaptive) with memory management
- **Performance Profiling**: Runtime profiling with minimal overhead and adaptive optimization

## Development Commands

### Testing
```bash
# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=python_optimizer --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_specialization.py
pytest tests/test_genetic.py
pytest tests/test_jit_profiling.py

# Run benchmarks (marked as slow)
pytest -m benchmark
```

### Test Coverage by Module
- **Core & Specialization:** `test_basic.py`, `test_specialization.py`, `test_specialization_cache.py`, `test_specialization_performance.py`
- **Genetic Algorithm:** `test_genetic.py` (40+ tests)
- **JIT & Profiling:** `test_jit_profiling.py` (50+ tests)
- **Total Test Files:** 6 files with 150+ test cases

### Code Quality
```bash
# Format code (must run before committing)
black python_optimizer/ tests/ examples/
isort python_optimizer/ tests/ examples/

# Check formatting
black --check --diff python_optimizer/

# Linting
flake8 python_optimizer/
flake8 tests/ --ignore=F401,F811

# Type checking
mypy python_optimizer/
```

### Makefile Shortcuts
```bash
make test           # Run test suite
make test-cov       # Run with coverage
make format         # Format code with black + isort
make lint           # Run flake8
make type-check     # Run mypy
make pre-commit     # Run all pre-commit hooks
make benchmark      # Run performance benchmarks
make clean          # Clean build artifacts
```

### Benchmarking
```bash
# JIT performance tests
python python_optimizer/benchmarks/test_jit_performance.py

# Run all benchmarks
make benchmark-all
```

## Architecture

### Core Module Structure

```
python_optimizer/
├── core/               # Main optimization engine
│   ├── decorator.py    # @optimize decorator - entry point for optimization
│   └── engine.py       # OptimizationEngine - coordinates JIT, profiling
│
├── specialization/     # Variable specialization system (key differentiator)
│   ├── engine.py       # SpecializationEngine - main coordinator
│   ├── analyzer.py     # TypeAnalyzer - analyzes function argument patterns
│   ├── dispatcher.py   # AdaptiveDispatcher/RuntimeDispatcher - selects optimal version
│   ├── generators.py   # SpecializationCodeGenerator - generates specialized code
│   └── cache.py        # SpecializationCache - manages specialized versions
│
├── jit/                # Pre-built JIT-optimized functions
│   └── jit_fitness_evaluator.py  # Financial/trading functions
│
├── genetic/            # Genetic algorithm optimization
│   └── genetic_optimizer.py
│
└── profiling/          # Performance profiling
    └── profiler.py
```

### Optimization Flow

1. **Function decorated with @optimize**
   - Parameters: `jit`, `specialize`, `profile`, `aggressiveness`, `cache`, `parallel`, `nogil`, `fastmath`
   
2. **If jit=True**: OptimizationEngine applies Numba JIT compilation
   - Creates njit-wrapped function with specified parameters
   - Caches compiled version for reuse

3. **If specialize=True**: SpecializationEngine creates adaptive wrapper
   - TypeAnalyzer analyzes function on first calls
   - RuntimeDispatcher/AdaptiveDispatcher selects best version
   - SpecializationCache stores type-specific optimized versions
   - Generates new specializations when beneficial (>20% gain threshold)

4. **Dispatching**: On each call, dispatcher selects optimal version
   - Cache hit: Use cached specialized version
   - Pattern match: Generate new specialization
   - Fallback: Use original function

### Key Design Patterns

**Specialization System**:
- Functions get specialized per unique type signature
- Cache entries track: type signature, usage count, performance gain, last access
- Adaptive learning adjusts specialization thresholds based on effectiveness
- Thread-safe concurrent access via RLock

**Caching Strategy**:
- Multiple eviction policies: LRU, LFU, TTL, Size-based, Adaptive
- Memory-bounded with weak references to prevent leaks
- Configurable via `configure_specialization()`

## Important Implementation Details

### JIT Compilation
- **Requires Numba**: Functions must be Numba-compatible (no arbitrary Python objects)
- **First call is slow**: JIT compilation happens on first execution
- **Cache location**: `~/.python_optimizer/cache` (configurable)
- **Parallel execution**: Use `parallel=True` for parallelizable loops
- **GIL release**: Use `nogil=True` for GIL-free execution (Numba-compatible code only)

### Variable Specialization
- **Threshold**: Min 5 calls before creating specialization (configurable via `min_calls_for_specialization`)
- **Performance requirement**: Must provide >20% gain (configurable via `min_performance_gain`)
- **Type hashing**: Uses custom TypeHasher for stable, type-aware cache keys
- **Specialization key format**: `f"{func_name}_{type_signature}_{usage_pattern_hash}"`

### Testing Specialization Changes
When modifying specialization system:
1. Run `tests/test_specialization.py` - core functionality
2. Run `tests/test_specialization_cache.py` - cache behavior
3. Run `tests/test_specialization_performance.py` - performance regression tests
4. Check with `debug_specialization_detailed.py` for detailed analysis

### Common Pitfalls
- **Don't use @optimize(jit=True) on non-numeric code**: Numba only works with numeric types
- **Specialization needs multiple calls**: First few calls gather type info before specializing
- **Memory limits**: Default 100MB cache limit; configure with `configure_specialization(max_memory_mb=...)`
- **Thread safety overhead**: Minimal but present; consider for ultra-high-frequency calls

## Configuration

### Global Specialization Config
```python
from python_optimizer import configure_specialization

configure_specialization(
    min_calls_for_specialization=5,    # Calls before specializing
    min_performance_gain=0.2,          # 20% gain threshold
    enable_adaptive_learning=True,     # Learn from patterns
    max_cache_size=1000,               # Max cached entries
    max_memory_mb=100                  # Memory limit
)
```

### Environment Variables
```bash
export PYTHON_OPTIMIZER_JIT_CACHE=1     # Enable JIT cache
export PYTHON_OPTIMIZER_PROFILE=1       # Enable profiling
export PYTHON_OPTIMIZER_PARALLEL=1      # Enable parallel execution
```

### Config File (optional)
Create `python_optimizer.toml` in project root:
```toml
[jit]
cache_dir = "~/.python_optimizer/cache"
compile_timeout = 30

[specialization]
max_variants = 5
threshold = 100
```

## Examples & Documentation

- **Basic usage**: `examples/basic_optimization.py` - Simple JIT examples
- **Advanced features**: `examples/advanced_optimization.py` - Comprehensive specialization demos
- **Financial computing**: `examples/trading_strategy_example.py` - Trading backtesting
- **ML optimization**: `examples/ml_optimization.py` - Machine learning scenarios

**Documentation**: See `docs/` directory
- `optimization_overview.md` - Comprehensive feature overview
- `specialization_cache.md` - Deep dive into caching system
- `performance_guide.md` - Best practices

## CI/CD

### GitHub Actions Workflow
- **Matrix testing**: Python 3.11, 3.12, 3.13 across Ubuntu, macOS, Windows
- **Linting**: flake8 (critical errors fail), black, isort
- **Type checking**: mypy (continue-on-error for now)
- **Coverage**: Codecov integration (80% target)
- **Benchmarks**: Automated performance testing
- **Security**: Safety and Bandit scans

### Pre-commit Hooks
Configured in `.pre-commit-config.yaml`:
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- trailing whitespace removal

Install with: `pre-commit install`

## Dependencies

**Core**:
- numpy >= 1.24.0
- numba >= 0.58.0 (JIT compilation)
- pandas >= 2.0.0
- scipy >= 1.10.0

**Dev**:
- pytest >= 7.4.0
- black >= 23.0.0
- isort >= 5.12.0
- flake8 >= 6.0.0
- mypy >= 1.5.0

**Optional**:
- GPU: cupy-cuda12x, numba[cuda] (not yet implemented)
- ML: torch, tensorflow, scikit-learn, optuna (future integration)

## Performance Characteristics

**Expected Speedups**:
- Numerical computation (JIT): 50-200x
- Financial metrics (JIT): 50-100x
- Specialized polymorphic functions: 100-400x
- Array operations: 100-500x
- Genetic algorithms: 100-300x

**Cache Performance**:
- Hit rate: 85-97% typical
- Memory overhead: ~200-500 bytes per specialization
- Dispatch overhead: <1μs typically

**When to Use What**:
- `jit=True` only: Pure numerical code, no type variations
- `specialize=True` only: Polymorphic functions with type variations, non-Numba code
- Both: Numerical functions with multiple input types (e.g., list vs. ndarray)

## Troubleshooting

### Low Specialization Performance
Check stats: `get_specialization_stats('func_name')`
- If hit_rate < 70%: Increase cache size or reduce min_calls
- If specializations_created == 0: Function may not have clear type patterns
- If avg_performance_gain < 1.2: Function may not benefit from specialization

### Memory Issues
Check cache: `get_cache_stats()`
- If memory near limit: Increase `max_memory_mb` or enable more aggressive eviction
- If high evictions: Increase `max_cache_size`
- Clear cache: `clear_specialization_cache()`

### JIT Compilation Failures
- Check Numba compatibility: Function must use only numeric types
- Inspect error: Numba provides detailed compilation errors
- Fallback: Optimizer automatically falls back to original function on JIT failure

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite: `make test-all`
4. Create git tag: `git tag v0.x.x`
5. Push tag: `git push origin v0.x.x`
6. GitHub Actions automatically builds and publishes to PyPI (on release creation)
