"""
Variable Specialization Module

This module implements intelligent variable type specialization for Python functions.
It analyzes code patterns, detects variable types, and generates optimized specialized
versions of functions for different type combinations.

Key Components:
- TypeAnalyzer: Analyzes code and detects variable types and patterns
- SpecializationEngine: Creates specialized versions of functions
- RuntimeDispatcher: Selects optimal specialized version at runtime
- SpecializationCache: Manages cached specialized functions
"""

from .analyzer import TypeAnalyzer, TypePattern, VariableUsage
from .cache import CacheEntry, SpecializationCache
from .dispatcher import DispatchResult, RuntimeDispatcher
from .engine import SpecializationConfig, SpecializationEngine
from .generators import (
    ArraySpecializer,
    ContainerSpecializer,
    NumericSpecializer,
    SpecializationGenerator,
    StringSpecializer,
)

__all__ = [
    # Core components
    "TypeAnalyzer",
    "SpecializationEngine",
    "RuntimeDispatcher",
    "SpecializationCache",
    # Data structures
    "VariableUsage",
    "TypePattern",
    "SpecializationConfig",
    "DispatchResult",
    "CacheEntry",
    # Specialized generators
    "NumericSpecializer",
    "ArraySpecializer",
    "StringSpecializer",
    "ContainerSpecializer",
    "SpecializationGenerator",
]
