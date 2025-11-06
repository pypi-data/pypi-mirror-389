#!/usr/bin/env python3
"""
Detailed debug script for specialization system.
"""

from python_optimizer import optimize, get_specialization_stats, configure_specialization, clear_specialization_cache

# Clear cache and configure
clear_specialization_cache()
configure_specialization(
    min_calls_for_specialization=3,
    min_performance_gain=0.1,
    enable_adaptive_learning=True
)

@optimize(jit=False, specialize=True)
def test_function(x):
    """Simple test function."""
    return x * 2 + 1

print("🔍 Testing Specialization System - Detailed")
print("=" * 50)

# Get the engine and dispatcher
engine = test_function.__specialization_engine__
dispatcher = engine.dispatcher
type_analyzer = dispatcher.type_analyzer

print("Initial state:")
print(f"  Engine: {engine}")
print(f"  Dispatcher: {dispatcher}")  
print(f"  Type analyzer: {type_analyzer}")
print(f"  Runtime types: {dict(type_analyzer.runtime_types)}")

# Test function once and check what happens
print("\nCalling test_function(5)...")
result = test_function(5)
print(f"Result: {result}")

print(f"\nAfter 1 call:")
print(f"  Runtime types: {dict(type_analyzer.runtime_types)}")
print(f"  Engine stats: {engine.optimization_stats}")

# Call a few more times to trigger specialization threshold
print("\nCalling function 5 more times...")
for i in range(6, 11):
    result = test_function(i)
    print(f"test_function({i}) = {result}")

print(f"\nAfter 6 calls:")
print(f"  Runtime types: {dict(type_analyzer.runtime_types)}")
print(f"  Engine stats: {engine.optimization_stats}")

# Check dispatcher stats
print("\nDispatcher details:")
print(f"  Min calls for specialization: {dispatcher.min_calls_for_specialization}")
print(f"  Min performance gain: {dispatcher.min_performance_gain}")
print(f"  Max specializations per function: {dispatcher.max_specializations_per_function}")
print(f"  Dispatch stats: {dispatcher.dispatch_stats}")
print(f"  Selection history: {dispatcher.selection_history}")

# Check cache
print("\nCache state:")
cache_stats = dispatcher.cache.get_stats()
print(f"  Cache stats: {cache_stats}")

# Test the _should_specialize method directly
print("\nTesting _should_specialize logic:")
param_types = {'arg_0': int}
should_spec, reason = dispatcher._should_specialize('test_function', param_types)
print(f"  Should specialize: {should_spec}, Reason: {reason}")
print(f"  Total calls in type analyzer: {sum(len(type_list) for type_list in type_analyzer.runtime_types.get('test_function', {}).values())}")

# Test the code generation directly
print("\nTesting code generation:")
original_func = test_function.__original_function__
usage_patterns = dispatcher._get_usage_patterns('test_function', param_types)
print(f"  Usage patterns: {usage_patterns}")
specialized_func = dispatcher._create_specialization(original_func, param_types, usage_patterns)
print(f"  Generated specialization: {specialized_func}")

print("\nFinal specialization stats:")
stats = get_specialization_stats('test_function')
for key, value in stats.items():
    print(f"  {key}: {value}")