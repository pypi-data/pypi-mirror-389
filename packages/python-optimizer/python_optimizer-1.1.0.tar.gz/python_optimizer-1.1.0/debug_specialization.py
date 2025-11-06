#!/usr/bin/env python3
"""
Debug script to test the specialization system.
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

print("🔍 Testing Specialization System")
print("=" * 40)

# Test the function multiple times
print("Calling function 10 times with integers...")
for i in range(10):
    result = test_function(i)
    print(f"test_function({i}) = {result}")

# Check if the function is marked as optimized
print("\nFunction attributes:")
print(f"  _has_specialization: {getattr(test_function, '_has_specialization', 'Not found')}")
print(f"  __specialized__: {getattr(test_function, '__specialized__', 'Not found')}")
print(f"  __specialization_engine__: {getattr(test_function, '__specialization_engine__', 'Not found')}")

print("\nSpecialization stats:")
stats = get_specialization_stats('test_function')
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\nFull specialization stats:")
full_stats = get_specialization_stats()
for key, value in full_stats.items():
    print(f"  {key}: {value}")