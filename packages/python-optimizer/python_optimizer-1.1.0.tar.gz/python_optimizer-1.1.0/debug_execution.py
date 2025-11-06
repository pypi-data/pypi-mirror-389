#!/usr/bin/env python3
"""
Debug execution path in specialization system.
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
    print(f"  --> Inside test_function with x={x}")
    return x * 2 + 1

print("🔍 Testing Execution Path")
print("=" * 40)

print("Calling test_function(5)...")
result = test_function(5)
print(f"Result: {result}")

# Check what the wrapper actually is
print(f"\nFunction details:")
print(f"  Type: {type(test_function)}")
print(f"  Name: {test_function.__name__}")
print(f"  Module: {test_function.__module__}")
print(f"  Code object: {test_function.__code__.co_name}")

# Check if wrapper is being called
print(f"\nWrapper attributes:")
print(f"  __wrapped__: {getattr(test_function, '__wrapped__', 'None')}")
print(f"  __original_function__: {getattr(test_function, '__original_function__', 'None')}")

# Add some instrumentation
engine = test_function.__specialization_engine__

print(f"\nEngine details:")
print(f"  Dispatcher: {engine.dispatcher}")
print(f"  Dispatcher type: {type(engine.dispatcher)}")
print(f"  Has dispatch method: {hasattr(engine.dispatcher, 'dispatch')}")

# Try calling dispatcher directly  
if hasattr(engine.dispatcher, 'dispatch'):
    print(f"\nTesting direct dispatch...")
    original_func = test_function.__original_function__
    dispatch_result = engine.dispatcher.dispatch(original_func, (5,), {})
    print(f"  Dispatch result: {dispatch_result}")
    print(f"  Selected function: {dispatch_result.selected_function}")
    print(f"  Selection reason: {dispatch_result.selection_reason}")
    print(f"  Is specialized: {dispatch_result.is_specialized}")