"""
Type Analysis and Detection for Variable Specialization

This module analyzes Python code to detect variable usage patterns, types,
and optimization opportunities for specialization.
"""

import ast
import inspect
import types
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np


@dataclass
class VariableUsage:
    """Represents how a variable is used in code."""

    name: str
    operations: Set[str] = field(default_factory=set)
    types_seen: Set[type] = field(default_factory=set)
    is_loop_variable: bool = False
    is_array_indexed: bool = False
    is_numeric_heavy: bool = False
    is_container: bool = False
    usage_count: int = 0

    def add_operation(self, op: str):
        """Add an operation performed on this variable."""
        self.operations.add(op)
        self.usage_count += 1

        # Classify operation types
        numeric_ops = {"+", "-", "*", "/", "//", "%", "**", "&", "|", "^", "<<", ">>"}
        if op in numeric_ops:
            self.is_numeric_heavy = True

        container_ops = {
            "append",
            "extend",
            "pop",
            "remove",
            "insert",
            "__getitem__",
            "__setitem__",
        }
        if op in container_ops:
            self.is_container = True

    def add_type(self, type_obj: type):
        """Add a type that this variable has been observed to have."""
        self.types_seen.add(type_obj)

    def get_dominant_type(self) -> Optional[type]:
        """Get the most likely type for this variable."""
        if not self.types_seen:
            return None

        # Prioritize numeric types for numeric operations
        if self.is_numeric_heavy:
            numeric_types = {int, float, complex, np.ndarray}
            for t in numeric_types:
                if t in self.types_seen:
                    return t

        # Return most common type
        return max(self.types_seen, key=lambda t: str(t))


@dataclass
class TypePattern:
    """Represents a detected type specialization pattern."""

    function_name: str
    parameter_types: Dict[str, type]
    return_type: Optional[type] = None
    optimization_potential: float = 0.0
    suggested_specializations: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.optimization_potential = self._calculate_potential()

    def _calculate_potential(self) -> float:
        """Calculate optimization potential score (0-1)."""
        score = 0.0

        # Numeric types have high optimization potential
        numeric_types = {int, float, complex, np.integer, np.floating}
        for param_type in self.parameter_types.values():
            if param_type in numeric_types or (
                hasattr(param_type, "__module__")
                and "numpy" in str(param_type.__module__)
            ):
                score += 0.3

        # Array operations have very high potential
        if np.ndarray in self.parameter_types.values():
            score += 0.4

        # Multiple parameters increase complexity benefit
        if len(self.parameter_types) > 1:
            score += 0.2

        return min(score, 1.0)


class CodeVisitor(ast.NodeVisitor):
    """AST visitor to analyze variable usage patterns."""

    def __init__(self):
        self.variables: Dict[str, VariableUsage] = {}
        self.function_calls: List[str] = []
        self.current_loops: List[str] = []
        self.imports: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        """Visit variable name usage."""
        if node.id not in self.variables:
            self.variables[node.id] = VariableUsage(node.id)

        var = self.variables[node.id]
        var.usage_count += 1

        # Check if in loop
        if self.current_loops:
            var.is_loop_variable = True

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operations."""
        # Extract variable names from left and right operands
        vars_in_op = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                vars_in_op.append(child.id)

        # Add operation to variables
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
            ast.LShift: "<<",
            ast.RShift: ">>",
        }

        op_name = op_map.get(type(node.op), "unknown")
        for var_name in vars_in_op:
            if var_name in self.variables:
                self.variables[var_name].add_operation(op_name)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        """Visit array/container indexing."""
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if var_name not in self.variables:
                self.variables[var_name] = VariableUsage(var_name)

            self.variables[var_name].is_array_indexed = True
            self.variables[var_name].add_operation("__getitem__")

        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """Visit for loops."""
        if isinstance(node.target, ast.Name):
            self.current_loops.append(node.target.id)

        self.generic_visit(node)

        if isinstance(node.target, ast.Name):
            self.current_loops.pop()

    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            self.function_calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method calls
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                method_name = node.func.attr
                if var_name in self.variables:
                    self.variables[var_name].add_operation(method_name)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements."""
        if node.module:
            self.imports.add(node.module)


class TypeAnalyzer:
    """Analyzes code to detect type patterns and specialization opportunities."""

    def __init__(self):
        self.runtime_types: Dict[str, Dict[str, List[type]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.call_patterns: Dict[str, List[TypePattern]] = defaultdict(list)

    def analyze_function(self, func: types.FunctionType) -> Dict[str, VariableUsage]:
        """Analyze a function's code for variable usage patterns."""
        try:
            # Get source code
            source = inspect.getsource(func)
            tree = ast.parse(source)

            # Visit AST
            visitor = CodeVisitor()
            visitor.visit(tree)

            # Enhance with type hints if available
            self._enhance_with_type_hints(func, visitor.variables)

            return visitor.variables

        except (OSError, TypeError) as e:
            # Can't get source (built-in functions, etc.)
            return {}

    def _enhance_with_type_hints(
        self, func: types.FunctionType, variables: Dict[str, VariableUsage]
    ):
        """Enhance variable analysis with type hints."""
        try:
            type_hints = getattr(func, "__annotations__", {})
            for param_name, type_hint in type_hints.items():
                if param_name in variables and param_name != "return":
                    if isinstance(type_hint, type):
                        variables[param_name].add_type(type_hint)
        except:
            pass

    def record_runtime_call(self, func_name: str, args: Tuple, kwargs: Dict):
        """Record a runtime function call with actual types."""
        # Use generic parameter names for now - this is more reliable
        param_names = [f"arg_{i}" for i in range(len(args))]

        # Record argument types
        for i, arg in enumerate(args):
            param_name = param_names[i] if i < len(param_names) else f"arg_{i}"
            self.runtime_types[func_name][param_name].append(type(arg))

        # Record keyword argument types
        for param_name, value in kwargs.items():
            self.runtime_types[func_name][param_name].append(type(value))

    def analyze_call_patterns(
        self, func_name: str, min_calls: int = 5
    ) -> List[TypePattern]:
        """Analyze recorded call patterns to detect specialization opportunities."""
        if func_name not in self.runtime_types:
            return []

        call_data = self.runtime_types[func_name]
        patterns = []

        # Group calls by type combinations
        type_combinations = defaultdict(int)

        for param_name, type_list in call_data.items():
            if len(type_list) < min_calls:
                continue

            # Find most common types for this parameter
            type_counts = defaultdict(int)
            for t in type_list:
                type_counts[t] += 1

            # Only consider types that appear frequently
            dominant_types = {
                t: count for t, count in type_counts.items() if count >= min_calls * 0.3
            }  # At least 30% of calls

            for t, count in dominant_types.items():
                key = (param_name, t)
                type_combinations[key] = count

        # Generate type patterns
        if type_combinations:
            # Group by parameter sets
            param_groups = defaultdict(dict)
            for (param_name, param_type), count in type_combinations.items():
                param_groups[param_name][param_type] = count

            # Create patterns for dominant type combinations
            for param_name, type_counts in param_groups.items():
                dominant_type = max(type_counts.keys(), key=lambda t: type_counts[t])

                pattern = TypePattern(
                    function_name=func_name, parameter_types={param_name: dominant_type}
                )

                # Add specialization suggestions
                pattern.suggested_specializations = self._suggest_specializations(
                    param_name, dominant_type
                )

                patterns.append(pattern)

        self.call_patterns[func_name] = patterns
        return patterns

    def _suggest_specializations(self, param_name: str, param_type: type) -> List[str]:
        """Suggest specialization strategies for a parameter type."""
        suggestions = []

        # Numeric specializations
        if param_type in {int, float}:
            suggestions.extend(
                [
                    f"numeric_{param_type.__name__}_ops",
                    f"vectorized_{param_type.__name__}_operations",
                    f"inline_{param_type.__name__}_calculations",
                ]
            )

        # Array specializations
        if param_type == np.ndarray:
            suggestions.extend(
                [
                    f"numpy_array_optimization",
                    f"vectorized_array_operations",
                    f"memory_efficient_array_ops",
                ]
            )

        # Container specializations
        if param_type in {list, tuple, dict}:
            suggestions.extend(
                [
                    f"{param_type.__name__}_specialized_access",
                    f"optimized_{param_type.__name__}_operations",
                ]
            )

        return suggestions

    def get_specialization_candidates(self, func_name: str) -> List[TypePattern]:
        """Get the best specialization candidates for a function."""
        if func_name not in self.call_patterns:
            return []

        patterns = self.call_patterns[func_name]

        # Sort by optimization potential
        candidates = sorted(
            patterns, key=lambda p: p.optimization_potential, reverse=True
        )

        # Filter by minimum potential
        return [p for p in candidates if p.optimization_potential >= 0.3]

    def clear_function_data(self, func_name: str):
        """Clear recorded data for a specific function."""
        self.runtime_types.pop(func_name, None)
        self.call_patterns.pop(func_name, None)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis results."""
        return {
            "functions_analyzed": len(self.runtime_types),
            "total_calls_recorded": sum(
                sum(len(type_list) for type_list in param_data.values())
                for param_data in self.runtime_types.values()
            ),
            "specialization_patterns": sum(
                len(patterns) for patterns in self.call_patterns.values()
            ),
            "high_potential_candidates": sum(
                len([p for p in patterns if p.optimization_potential >= 0.5])
                for patterns in self.call_patterns.values()
            ),
        }
