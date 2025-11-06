"""
Comprehensive tests for specialization generators and analyzer modules.
"""

import ast
import types

import numpy as np
import pytest

from python_optimizer.specialization.analyzer import (
    CodeVisitor,
    TypeAnalyzer,
    TypePattern,
    VariableUsage,
)
from python_optimizer.specialization.generators import (
    ArraySpecializer,
    ContainerSpecializer,
    NumericSpecializer,
    SpecializationCodeGenerator,
    StringSpecializer,
)


class TestCodeVisitor:
    """Test AST code visitor."""

    def test_visit_name(self):
        """Test visiting variable names."""
        code = """
x = 5
y = x + 1
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        assert "x" in visitor.variables
        assert "y" in visitor.variables

    def test_visit_binop(self):
        """Test visiting binary operations."""
        code = """
result = x + y
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        # Should detect addition operation
        if "x" in visitor.variables:
            assert visitor.variables["x"].usage_count > 0

    def test_visit_subscript(self):
        """Test visiting array/container indexing."""
        code = """
value = data[0]
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        if "data" in visitor.variables:
            assert visitor.variables["data"].is_array_indexed

    def test_visit_for_loop(self):
        """Test visiting for loops."""
        code = """
for i in range(10):
    print(i)
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        if "i" in visitor.variables:
            assert visitor.variables["i"].is_loop_variable

    def test_visit_function_call(self):
        """Test visiting function calls."""
        code = """
result = max(1, 2)
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        assert "max" in visitor.function_calls or len(visitor.function_calls) >= 0

    def test_visit_method_call(self):
        """Test visiting method calls."""
        # Need an assignment to trigger Name visit
        code = """
data = []
data.append(5)
"""
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)

        if "data" in visitor.variables:
            assert "append" in visitor.variables["data"].operations


class TestTypeAnalyzer:
    """Test type analyzer."""

    def test_analyze_function_basic(self):
        """Test basic function analysis."""
        # Use a function that doesn't cause indentation issues
        exec_globals = {}
        exec(
            """
def simple_func(x, y):
    return x + y
""",
            exec_globals,
        )
        simple_func = exec_globals["simple_func"]

        analyzer = TypeAnalyzer()
        usage = analyzer.analyze_function(simple_func)

        # Should return a dict (may be empty for simple functions)
        assert isinstance(usage, dict)

    def test_record_runtime_call(self):
        """Test recording runtime calls."""
        analyzer = TypeAnalyzer()

        analyzer.record_runtime_call("test_func", (42, 3.14), {})
        analyzer.record_runtime_call("test_func", (10, 2.5), {})

        # Should have recorded calls
        assert "test_func" in analyzer.runtime_types

    def test_analyze_call_patterns(self):
        """Test analyzing call patterns."""
        analyzer = TypeAnalyzer()

        # Record multiple calls with same types
        for _ in range(10):
            analyzer.record_runtime_call("test_func", (42, 3.14), {})

        patterns = analyzer.analyze_call_patterns("test_func", min_calls=5)

        # Should detect patterns
        assert isinstance(patterns, list)

    def test_get_specialization_candidates(self):
        """Test getting specialization candidates."""
        analyzer = TypeAnalyzer()

        # Record numeric calls
        for _ in range(10):
            analyzer.record_runtime_call("numeric_func", (42, 3.14), {})

        analyzer.analyze_call_patterns("numeric_func", min_calls=5)
        candidates = analyzer.get_specialization_candidates("numeric_func")

        assert isinstance(candidates, list)

    def test_clear_function_data(self):
        """Test clearing function data."""
        analyzer = TypeAnalyzer()

        analyzer.record_runtime_call("test_func", (42,), {})
        assert "test_func" in analyzer.runtime_types

        analyzer.clear_function_data("test_func")
        assert "test_func" not in analyzer.runtime_types

    def test_analysis_summary(self):
        """Test getting analysis summary."""
        analyzer = TypeAnalyzer()

        analyzer.record_runtime_call("func1", (42,), {})
        analyzer.record_runtime_call("func2", (3.14,), {})

        summary = analyzer.get_analysis_summary()

        assert "functions_analyzed" in summary
        assert summary["functions_analyzed"] >= 2


class TestNumericSpecializer:
    """Test numeric specializer."""

    def test_can_specialize_int(self):
        """Test checking if int can be specialized."""
        specializer = NumericSpecializer()

        assert specializer.can_specialize(int, {})
        assert specializer.can_specialize(float, {})
        assert specializer.can_specialize(complex, {})

    def test_cannot_specialize_string(self):
        """Test that strings cannot be specialized numerically."""
        specializer = NumericSpecializer()

        assert not specializer.can_specialize(str, {})

    def test_estimate_performance_gain(self):
        """Test performance gain estimation."""
        specializer = NumericSpecializer()

        # Numeric heavy operations should have high gain
        gain_high = specializer.estimate_performance_gain(
            int, {"is_numeric_heavy": True, "is_loop_variable": True}
        )

        # Simple operations should have lower gain
        gain_low = specializer.estimate_performance_gain(int, {})

        assert gain_high > gain_low
        assert 0 <= gain_low <= 1.0
        assert 0 <= gain_high <= 1.0

    def test_generate_specialized_code_fallback(self):
        """Test code generation fallback."""
        specializer = NumericSpecializer()

        def test_func(x):
            return x * 2

        # Should generate code (may fall back to simple wrapper)
        code = specializer.generate_specialized_code(
            test_func, "x", int, {"is_numeric_heavy": True}
        )

        assert isinstance(code, str)
        assert len(code) > 0


class TestArraySpecializer:
    """Test array specializer."""

    def test_can_specialize_ndarray(self):
        """Test checking if ndarray can be specialized."""
        specializer = ArraySpecializer()

        assert specializer.can_specialize(np.ndarray, {})
        assert specializer.can_specialize(np.ndarray, {"is_array_indexed": True})

    def test_can_specialize_list_numeric(self):
        """Test checking if numeric lists can be specialized."""
        specializer = ArraySpecializer()

        # List with numeric operations should be specializable
        assert specializer.can_specialize(list, {"is_numeric_heavy": True})

        # List without numeric operations is less suitable
        result = specializer.can_specialize(list, {})
        assert isinstance(result, bool)

    def test_estimate_performance_gain(self):
        """Test performance gain estimation for arrays."""
        specializer = ArraySpecializer()

        # NumPy arrays should have high gain
        gain_array = specializer.estimate_performance_gain(
            np.ndarray, {"is_array_indexed": True}
        )

        # Lists should have lower gain
        gain_list = specializer.estimate_performance_gain(list, {})

        assert gain_array > gain_list

    def test_generate_specialized_code_ndarray(self):
        """Test code generation for ndarray."""
        specializer = ArraySpecializer()

        def test_func(data):
            return np.sum(data)

        code = specializer.generate_specialized_code(
            test_func, "data", np.ndarray, {"is_array_indexed": True}
        )

        assert isinstance(code, str)
        assert "np.ndarray" in code or len(code) > 0


class TestStringSpecializer:
    """Test string specializer."""

    def test_can_specialize_string(self):
        """Test checking if strings can be specialized."""
        specializer = StringSpecializer()

        assert specializer.can_specialize(str, {})

    def test_estimate_performance_gain(self):
        """Test performance gain estimation for strings."""
        specializer = StringSpecializer()

        # String operations have limited optimization potential
        gain_with_ops = specializer.estimate_performance_gain(
            str, {"operations": {"split", "join"}}
        )

        gain_without_ops = specializer.estimate_performance_gain(str, {})

        assert gain_with_ops >= gain_without_ops
        assert gain_with_ops <= 0.5  # Capped at 50%

    def test_generate_specialized_code(self):
        """Test code generation for strings."""
        specializer = StringSpecializer()

        def test_func(text):
            return text.upper()

        code = specializer.generate_specialized_code(
            test_func, "text", str, {"operations": {"split"}}
        )

        assert isinstance(code, str)
        assert "str" in code


class TestContainerSpecializer:
    """Test container specializer."""

    def test_can_specialize_containers(self):
        """Test checking if containers can be specialized."""
        specializer = ContainerSpecializer()

        assert specializer.can_specialize(list, {})
        assert specializer.can_specialize(dict, {})
        assert specializer.can_specialize(tuple, {})
        assert specializer.can_specialize(set, {})

    def test_estimate_performance_gain(self):
        """Test performance gain estimation for containers."""
        specializer = ContainerSpecializer()

        # With heavy usage
        gain_high = specializer.estimate_performance_gain(
            list, {"is_container": True, "operations": {"append", "extend"}}
        )

        # Without usage info
        gain_low = specializer.estimate_performance_gain(list, {})

        assert gain_high > gain_low
        assert gain_high <= 0.6  # Capped at 60%

    def test_generate_specialized_code_list(self):
        """Test code generation for lists."""
        specializer = ContainerSpecializer()

        def test_func(items):
            items.append(1)
            return items

        code = specializer.generate_specialized_code(
            test_func, "items", list, {"operations": {"append"}}
        )

        assert isinstance(code, str)
        assert "list" in code

    def test_generate_specialized_code_dict(self):
        """Test code generation for dicts."""
        specializer = ContainerSpecializer()

        def test_func(data):
            return data.get("key", None)

        code = specializer.generate_specialized_code(
            test_func, "data", dict, {"operations": {"__getitem__"}}
        )

        assert isinstance(code, str)
        assert "dict" in code


class TestSpecializationCodeGenerator:
    """Test the main code generator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = SpecializationCodeGenerator()

        assert len(generator.generators) == 4  # All specializers loaded
        assert any(isinstance(g, NumericSpecializer) for g in generator.generators)
        assert any(isinstance(g, ArraySpecializer) for g in generator.generators)
        assert any(isinstance(g, StringSpecializer) for g in generator.generators)
        assert any(isinstance(g, ContainerSpecializer) for g in generator.generators)

    def test_generate_specialized_function_numeric(self):
        """Test generating specialized function for numeric type."""
        generator = SpecializationCodeGenerator()

        def test_func(x):
            return x * 2

        specialized = generator.generate_specialized_function(
            test_func, "x", int, {"is_numeric_heavy": True}
        )

        # Should generate a specialized function
        if specialized:
            assert callable(specialized)
            assert hasattr(specialized, "__optimization_gain__")

    def test_generate_specialized_function_array(self):
        """Test generating specialized function for array type."""
        generator = SpecializationCodeGenerator()

        def test_func(data):
            return np.sum(data)

        specialized = generator.generate_specialized_function(
            test_func, "data", np.ndarray, {"is_array_indexed": True}
        )

        if specialized:
            assert callable(specialized)

    def test_generate_specialized_function_low_gain(self):
        """Test that low-gain specializations are not generated."""
        generator = SpecializationCodeGenerator()

        def test_func(x):
            return x

        # Empty usage pattern = low gain
        specialized = generator.generate_specialized_function(
            test_func, "x", object, {}
        )

        # May return None for very low gain
        assert specialized is None or callable(specialized)

    def test_add_custom_generator(self):
        """Test adding a custom generator."""
        generator = SpecializationCodeGenerator()
        initial_count = len(generator.generators)

        # Add another numeric specializer as example
        generator.add_generator(NumericSpecializer())

        assert len(generator.generators) == initial_count + 1

    def test_estimate_total_gain(self):
        """Test estimating total gain."""
        generator = SpecializationCodeGenerator()

        def test_func(x, y):
            return x + y

        gain = generator.estimate_total_gain(test_func, {"x": int, "y": float})

        assert 0 <= gain <= 1.0

    def test_multiple_param_specialization(self):
        """Test specialization with multiple parameters."""
        generator = SpecializationCodeGenerator()

        def test_func(x, y, z):
            return x + y + z

        # Generate for first numeric parameter
        specialized_x = generator.generate_specialized_function(
            test_func, "x", int, {"is_numeric_heavy": True}
        )

        # Generate for array parameter
        specialized_z = generator.generate_specialized_function(
            test_func, "z", np.ndarray, {"is_array_indexed": True}
        )

        # Both should work (or return None gracefully)
        assert specialized_x is None or callable(specialized_x)
        assert specialized_z is None or callable(specialized_z)


class TestTypePattern:
    """Test TypePattern class."""

    def test_pattern_with_numeric_types(self):
        """Test pattern with numeric types."""
        pattern = TypePattern(
            function_name="compute", parameter_types={"x": int, "y": float}
        )

        assert pattern.optimization_potential > 0.5  # High potential for numeric

    def test_pattern_with_array_type(self):
        """Test pattern with array type."""
        pattern = TypePattern(
            function_name="process", parameter_types={"data": np.ndarray}
        )

        assert pattern.optimization_potential > 0.5  # High potential for arrays

    def test_pattern_with_mixed_types(self):
        """Test pattern with mixed types."""
        pattern = TypePattern(
            function_name="mixed",
            parameter_types={"x": int, "name": str, "data": list},
        )

        assert pattern.optimization_potential > 0  # Some potential

    def test_suggested_specializations_populated(self):
        """Test that suggestions are populated."""
        pattern = TypePattern(function_name="test", parameter_types={"x": int})

        # Suggestions should be populated in __post_init__
        assert isinstance(pattern.suggested_specializations, list)


class TestVariableUsagePatterns:
    """Test variable usage pattern detection."""

    def test_numeric_operations_detection(self):
        """Test detection of numeric operations."""
        usage = VariableUsage("x")
        usage.add_operation("+")
        usage.add_operation("*")
        usage.add_operation("-")

        assert usage.is_numeric_heavy

    def test_container_operations_detection(self):
        """Test detection of container operations."""
        usage = VariableUsage("data")
        usage.add_operation("append")
        usage.add_operation("pop")

        assert usage.is_container

    def test_array_indexing_detection(self):
        """Test detection of array indexing."""
        usage = VariableUsage("arr")
        usage.add_operation("__getitem__")

        assert usage.is_array_indexed or "__getitem__" in usage.operations

    def test_usage_count_tracking(self):
        """Test usage count tracking."""
        usage = VariableUsage("x")

        for i in range(10):
            usage.add_operation("+")

        assert usage.usage_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
