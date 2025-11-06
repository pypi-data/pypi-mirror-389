#!/usr/bin/env python3
"""
Test the complete specialization flow with all fixes.
"""

from python_optimizer import optimize, get_specialization_stats, configure_specialization, clear_specialization_cache

# Clear cache and configure
clear_specialization_cache()
configure_specialization(
    min_calls_for_specialization=3,
    min_performance_gain=0.05,  # Lower threshold 
    enable_adaptive_learning=True
)

@optimize(jit=False, specialize=True)
def test_function(x):
    """Simple test function."""
    return x * 2 + 1

print("🔍 Testing Complete Specialization Flow")
print("=" * 50)

# Call function multiple times to trigger specialization
print("Calling function 10 times...")
for i in range(10):
    result = test_function(i)
    
    # Show progress every few calls
    if i % 3 == 2:
        engine = test_function.__specialization_engine__
        stats = engine.optimization_stats.get('test_function', {})
        runtime_types = dict(engine.dispatcher.type_analyzer.runtime_types)
        print(f"  Call {i+1}: result={result}")
        print(f"    Stats: {stats}")
        print(f"    Runtime types: {runtime_types}")
        
        # Test direct dispatch
        original_func = test_function.__original_function__
        param_types = {'arg_0': int}
        should_spec, reason = engine.dispatcher._should_specialize('test_function', param_types)
        print(f"    Should specialize: {should_spec}, Reason: {reason}")
        print()

print("\nFinal specialization stats:")
stats = get_specialization_stats('test_function')
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\nGlobal stats:")
global_stats = get_specialization_stats()
print(f"  Total dispatches: {global_stats.get('dispatcher_stats', {}).get('total_dispatches', 0)}")
print(f"  Functions analyzed: {global_stats.get('dispatcher_stats', {}).get('functions_analyzed', 0)}")
print(f"  Cache entries: {global_stats.get('cache_stats', {}).get('total_entries', 0)}")