"""Tests for ML model optimization with PyTorch.

Tests PyTorchModelOptimizer, TrainingOptimizer, InferenceOptimizer, and
graceful degradation when PyTorch is not available.
"""

import pytest
from unittest.mock import Mock, patch


# Test PyTorch availability
class TestPyTorchAvailability:
    """Tests for PyTorch framework availability detection."""

    def test_pytorch_available_flag(self):
        """Test PYTORCH_AVAILABLE flag is boolean."""
        from python_optimizer.ml import PYTORCH_AVAILABLE

        assert isinstance(PYTORCH_AVAILABLE, bool)

    def test_check_framework_availability(self):
        """Test framework availability checker."""
        from python_optimizer.ml import check_framework_availability

        info = check_framework_availability()
        assert isinstance(info, dict)
        assert "pytorch" in info
        assert "available" in info["pytorch"]
        assert isinstance(info["pytorch"]["available"], bool)

    def test_pytorch_version_when_available(self):
        """Test PyTorch version is set when available."""
        from python_optimizer.ml import PYTORCH_AVAILABLE, PYTORCH_VERSION

        if PYTORCH_AVAILABLE:
            assert PYTORCH_VERSION is not None
            assert isinstance(PYTORCH_VERSION, str)
        else:
            assert PYTORCH_VERSION is None


# Skip PyTorch tests if not available
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("torch", reason="PyTorch not available"),
    reason="PyTorch not available",
)


class TestPyTorchModelOptimizer:
    """Tests for PyTorchModelOptimizer class."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple PyTorch model for testing."""
        import torch.nn as nn

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = nn.Linear(10, 20)
                self.relu = nn.ReLU()
                self.linear2 = nn.Linear(20, 1)

            def forward(self, x):
                x = self.linear1(x)
                x = self.relu(x)
                x = self.linear2(x)
                return x

        return SimpleModel()

    def test_model_optimizer_initialization(self, simple_model):
        """Test PyTorchModelOptimizer initialization."""
        from python_optimizer.ml import PyTorchModelOptimizer

        optimizer = PyTorchModelOptimizer(simple_model)
        assert optimizer.model is not None
        assert optimizer.device is not None
        assert optimizer.mixed_precision is False
        assert optimizer.memory_efficient is True

    def test_model_optimizer_with_device_selection(self, simple_model):
        """Test model optimizer with explicit device."""
        import torch

        from python_optimizer.ml import PyTorchModelOptimizer

        optimizer = PyTorchModelOptimizer(simple_model, device="cpu")
        assert optimizer.device.type == "cpu"

        # Test with torch.device
        optimizer2 = PyTorchModelOptimizer(simple_model, device=torch.device("cpu"))
        assert optimizer2.device.type == "cpu"

    def test_model_optimizer_mixed_precision(self, simple_model):
        """Test model optimizer with mixed precision."""
        from python_optimizer.ml import PyTorchModelOptimizer

        optimizer = PyTorchModelOptimizer(
            simple_model, device="cpu", mixed_precision=True
        )
        assert optimizer.mixed_precision is True
        # Scaler should be None on CPU
        assert optimizer.scaler is None

    def test_model_optimizer_forward_pass(self, simple_model):
        """Test optimized forward pass."""
        import torch

        from python_optimizer.ml import PyTorchModelOptimizer

        optimizer = PyTorchModelOptimizer(simple_model, device="cpu", compile=False)

        # Create dummy input
        x = torch.randn(5, 10)
        output = optimizer.forward(x)

        assert output is not None
        assert output.shape == (5, 1)
        assert optimizer.stats["forward_passes"] == 1
        assert optimizer.stats["total_forward_time"] > 0

    def test_model_optimizer_statistics(self, simple_model):
        """Test optimizer statistics tracking."""
        import torch

        from python_optimizer.ml import PyTorchModelOptimizer

        optimizer = PyTorchModelOptimizer(simple_model, device="cpu", compile=False)

        # Run multiple forward passes
        x = torch.randn(5, 10)
        for _ in range(3):
            optimizer.forward(x)

        stats = optimizer.get_stats()
        assert stats["forward_passes"] == 3
        assert stats["total_forward_time"] > 0
        assert stats["avg_forward_time"] > 0
        assert "device" in stats
        assert stats["mixed_precision"] is False

    def test_model_optimizer_compile_fallback(self, simple_model):
        """Test torch.compile fallback behavior."""
        import torch

        from python_optimizer.ml import PyTorchModelOptimizer

        # Should handle compile=True gracefully even if not supported
        optimizer = PyTorchModelOptimizer(simple_model, device="cpu", compile=True)
        assert optimizer.model is not None

        # Test forward pass works
        x = torch.randn(5, 10)
        output = optimizer.forward(x)
        assert output is not None

    def test_model_optimizer_without_pytorch_raises(self):
        """Test that optimizer raises RuntimeError without PyTorch."""
        # Mock PYTORCH_AVAILABLE as False
        with patch("python_optimizer.ml.pytorch_optimizer.PYTORCH_AVAILABLE", False):
            from python_optimizer.ml.pytorch_optimizer import PyTorchModelOptimizer

            with pytest.raises(RuntimeError, match="PyTorch is not installed"):
                PyTorchModelOptimizer(Mock())


class TestTrainingOptimizer:
    """Tests for TrainingOptimizer class."""

    @pytest.fixture
    def training_setup(self):
        """Create model, optimizer, and data for training tests."""
        import torch
        import torch.nn as nn
        import torch.optim as optim

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        # Generate random data
        inputs = torch.randn(8, 10)
        targets = torch.randn(8, 1)

        return model, optimizer, criterion, inputs, targets

    def test_training_optimizer_initialization(self, training_setup):
        """Test TrainingOptimizer initialization."""
        from python_optimizer.ml import TrainingOptimizer

        model, optimizer, _, _, _ = training_setup

        training_opt = TrainingOptimizer(
            model, optimizer, device="cpu", mixed_precision=False
        )

        assert training_opt.model is not None
        assert training_opt.optimizer is not None
        assert training_opt.device.type == "cpu"
        assert training_opt.gradient_accumulation_steps == 1
        assert training_opt.max_grad_norm == 1.0

    def test_training_optimizer_with_options(self, training_setup):
        """Test TrainingOptimizer with custom options."""
        from python_optimizer.ml import TrainingOptimizer

        model, optimizer, _, _, _ = training_setup

        training_opt = TrainingOptimizer(
            model,
            optimizer,
            device="cpu",
            mixed_precision=False,
            gradient_accumulation_steps=4,
            max_grad_norm=0.5,
        )

        assert training_opt.gradient_accumulation_steps == 4
        assert training_opt.max_grad_norm == 0.5

    def test_training_optimizer_training_step(self, training_setup):
        """Test optimized training step."""
        from python_optimizer.ml import TrainingOptimizer

        model, optimizer, criterion, inputs, targets = training_setup

        training_opt = TrainingOptimizer(
            model, optimizer, device="cpu", mixed_precision=False
        )

        # Run training step
        result = training_opt.training_step(inputs, targets, criterion, step=0)

        assert isinstance(result, dict)
        assert "loss" in result
        assert "step_time" in result
        assert "gpu_memory_used" in result
        assert result["loss"] > 0
        assert result["step_time"] > 0

    def test_training_optimizer_gradient_accumulation(self, training_setup):
        """Test gradient accumulation."""
        from python_optimizer.ml import TrainingOptimizer

        model, optimizer, criterion, inputs, targets = training_setup

        training_opt = TrainingOptimizer(
            model,
            optimizer,
            device="cpu",
            mixed_precision=False,
            gradient_accumulation_steps=2,
        )

        # Step 0 should not update optimizer
        result1 = training_opt.training_step(inputs, targets, criterion, step=0)
        assert "loss" in result1

        # Step 1 should update optimizer
        result2 = training_opt.training_step(inputs, targets, criterion, step=1)
        assert "loss" in result2

        stats = training_opt.get_stats()
        assert stats["steps"] == 2

    def test_training_optimizer_statistics(self, training_setup):
        """Test training statistics tracking."""
        from python_optimizer.ml import TrainingOptimizer

        model, optimizer, criterion, inputs, targets = training_setup

        training_opt = TrainingOptimizer(
            model, optimizer, device="cpu", mixed_precision=False
        )

        # Run multiple steps
        for step in range(5):
            training_opt.training_step(inputs, targets, criterion, step=step)

        stats = training_opt.get_stats()
        assert stats["steps"] == 5
        assert stats["total_time"] > 0
        assert stats["avg_step_time"] > 0
        assert "device" in stats
        assert "mixed_precision" in stats

    def test_training_optimizer_without_pytorch_raises(self):
        """Test that TrainingOptimizer raises RuntimeError without PyTorch."""
        with patch("python_optimizer.ml.pytorch_optimizer.PYTORCH_AVAILABLE", False):
            from python_optimizer.ml.pytorch_optimizer import TrainingOptimizer

            with pytest.raises(RuntimeError, match="PyTorch is not installed"):
                TrainingOptimizer(Mock(), Mock())


class TestInferenceOptimizer:
    """Tests for InferenceOptimizer class."""

    @pytest.fixture
    def inference_model(self):
        """Create a simple model for inference testing."""
        import torch.nn as nn

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        return SimpleModel()

    def test_inference_optimizer_initialization(self, inference_model):
        """Test InferenceOptimizer initialization."""
        from python_optimizer.ml import InferenceOptimizer

        inf_opt = InferenceOptimizer(inference_model, device="cpu", compile=False)

        assert inf_opt.model is not None
        assert inf_opt.device.type == "cpu"
        assert inf_opt.batch_size is None

    def test_inference_optimizer_with_batch_size(self, inference_model):
        """Test InferenceOptimizer with explicit batch size."""
        from python_optimizer.ml import InferenceOptimizer

        inf_opt = InferenceOptimizer(
            inference_model, device="cpu", compile=False, batch_size=32
        )

        assert inf_opt.batch_size == 32

    def test_inference_optimizer_predict(self, inference_model):
        """Test inference prediction."""
        import torch

        from python_optimizer.ml import InferenceOptimizer

        inf_opt = InferenceOptimizer(inference_model, device="cpu", compile=False)

        # Single prediction
        x = torch.randn(1, 10)
        output = inf_opt.predict(x)

        assert output is not None
        assert output.shape == (1, 1)
        assert inf_opt.stats["predictions"] == 1

    def test_inference_optimizer_batch_predict(self, inference_model):
        """Test batch prediction."""
        import torch

        from python_optimizer.ml import InferenceOptimizer

        inf_opt = InferenceOptimizer(
            inference_model, device="cpu", compile=False, batch_size=4
        )

        # Create list of inputs
        inputs = [torch.randn(1, 10) for _ in range(10)]
        outputs = inf_opt.batch_predict(inputs)

        assert len(outputs) == 10
        assert all(o.shape == (1, 1) for o in outputs)
        assert inf_opt.stats["predictions"] == 10

    def test_inference_optimizer_statistics(self, inference_model):
        """Test inference statistics tracking."""
        import torch

        from python_optimizer.ml import InferenceOptimizer

        inf_opt = InferenceOptimizer(inference_model, device="cpu", compile=False)

        # Run multiple predictions
        for _ in range(5):
            x = torch.randn(1, 10)
            inf_opt.predict(x)

        stats = inf_opt.get_stats()
        assert stats["predictions"] == 5
        assert stats["total_time"] > 0
        assert stats["avg_prediction_time"] > 0
        assert "device" in stats

    def test_inference_optimizer_without_pytorch_raises(self):
        """Test that InferenceOptimizer raises RuntimeError without PyTorch."""
        with patch("python_optimizer.ml.pytorch_optimizer.PYTORCH_AVAILABLE", False):
            from python_optimizer.ml.pytorch_optimizer import InferenceOptimizer

            with pytest.raises(RuntimeError, match="PyTorch is not installed"):
                InferenceOptimizer(Mock())


class TestHighLevelAPI:
    """Tests for high-level API functions."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for API testing."""
        import torch.nn as nn

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        return SimpleModel()

    def test_optimize_model_function(self, simple_model):
        """Test optimize_model convenience function."""
        from python_optimizer.ml import optimize_model

        optimized = optimize_model(simple_model, device="cpu", compile=False)

        assert optimized is not None
        from python_optimizer.ml import PyTorchModelOptimizer

        assert isinstance(optimized, PyTorchModelOptimizer)

    def test_optimize_training_decorator(self):
        """Test optimize_training decorator."""
        import torch
        import torch.nn as nn

        from python_optimizer.ml import optimize_training

        @optimize_training(mixed_precision=False, gradient_accumulation_steps=1)
        def train_step(model, inputs, targets, criterion, optimizer):
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            return loss.item()

        # Create simple training setup
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()
        inputs = torch.randn(4, 10)
        targets = torch.randn(4, 1)

        # Run training step
        loss = train_step(model, inputs, targets, criterion, optimizer)
        assert isinstance(loss, float)
        assert loss >= 0

    def test_optimize_inference_function(self, simple_model):
        """Test optimize_inference convenience function."""
        from python_optimizer.ml import optimize_inference

        inf_opt = optimize_inference(simple_model, device="cpu", compile=False)

        assert inf_opt is not None
        from python_optimizer.ml import InferenceOptimizer

        assert isinstance(inf_opt, InferenceOptimizer)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_model_with_no_parameters(self):
        """Test model with no trainable parameters."""
        import torch.nn as nn

        from python_optimizer.ml import PyTorchModelOptimizer

        class EmptyModel(nn.Module):
            def forward(self, x):
                return x

        model = EmptyModel()
        optimizer = PyTorchModelOptimizer(model, device="cpu", compile=False)

        import torch

        x = torch.randn(5, 10)
        output = optimizer.forward(x)
        assert output.shape == x.shape

    def test_model_with_multiple_outputs(self):
        """Test model that returns multiple outputs."""
        import torch
        import torch.nn as nn

        from python_optimizer.ml import PyTorchModelOptimizer

        class MultiOutputModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = nn.Linear(10, 5)
                self.linear2 = nn.Linear(10, 3)

            def forward(self, x):
                return self.linear1(x), self.linear2(x)

        model = MultiOutputModel()
        optimizer = PyTorchModelOptimizer(model, device="cpu", compile=False)

        x = torch.randn(4, 10)
        out1, out2 = optimizer.forward(x)
        assert out1.shape == (4, 5)
        assert out2.shape == (4, 3)

    def test_training_with_zero_grad_norm(self):
        """Test training with gradient clipping disabled."""
        import torch
        import torch.nn as nn
        import torch.optim as optim

        from python_optimizer.ml import TrainingOptimizer

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        training_opt = TrainingOptimizer(
            model, optimizer, device="cpu", mixed_precision=False, max_grad_norm=None
        )

        inputs = torch.randn(8, 10)
        targets = torch.randn(8, 1)

        result = training_opt.training_step(inputs, targets, criterion, step=0)
        assert "loss" in result

    def test_inference_with_empty_batch(self):
        """Test inference with empty batch list."""
        import torch.nn as nn

        from python_optimizer.ml import InferenceOptimizer

        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        inf_opt = InferenceOptimizer(model, device="cpu", compile=False)

        outputs = inf_opt.batch_predict([])
        assert outputs == []


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_training_workflow(self):
        """Test complete training workflow with optimizer."""
        import torch
        import torch.nn as nn
        import torch.optim as optim

        from python_optimizer.ml import PyTorchModelOptimizer, TrainingOptimizer

        # Create model
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()

        # Optimize model
        model_opt = PyTorchModelOptimizer(
            model, device="cpu", compile=False, mixed_precision=False
        )

        # Create training optimizer
        optimizer = optim.Adam(model_opt.model.parameters(), lr=0.001)
        training_opt = TrainingOptimizer(
            model_opt.model, optimizer, device="cpu", mixed_precision=False
        )

        # Generate data
        inputs = torch.randn(16, 10)
        targets = torch.randn(16, 1)
        criterion = nn.MSELoss()

        # Train for a few steps
        initial_loss = None
        for step in range(10):
            result = training_opt.training_step(inputs, targets, criterion, step)
            if initial_loss is None:
                initial_loss = result["loss"]

        # Check that training happened
        stats = training_opt.get_stats()
        assert stats["steps"] == 10
        assert stats["total_time"] > 0

    def test_full_inference_workflow(self):
        """Test complete inference workflow with optimizer."""
        import torch
        import torch.nn as nn

        from python_optimizer.ml import optimize_inference, optimize_model

        # Create and train a simple model
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)

            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()

        # Optimize for training
        model_opt = optimize_model(model, device="cpu", compile=False)

        # Switch to inference mode
        model_opt.model.eval()
        inf_opt = optimize_inference(model_opt.model, device="cpu", compile=False)

        # Run inference
        test_inputs = [torch.randn(1, 10) for _ in range(20)]
        outputs = inf_opt.batch_predict(test_inputs)

        assert len(outputs) == 20
        assert all(o.shape == (1, 1) for o in outputs)

        stats = inf_opt.get_stats()
        assert stats["predictions"] == 20


class TestPerformance:
    """Performance and benchmark tests."""

    @pytest.mark.benchmark
    def test_optimization_overhead(self):
        """Test that optimization overhead is minimal."""
        import time

        import torch
        import torch.nn as nn

        from python_optimizer.ml import PyTorchModelOptimizer

        class BenchmarkModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = nn.Linear(100, 50)
                self.relu = nn.ReLU()
                self.linear2 = nn.Linear(50, 10)

            def forward(self, x):
                x = self.linear1(x)
                x = self.relu(x)
                x = self.linear2(x)
                return x

        model = BenchmarkModel()
        optimizer = PyTorchModelOptimizer(model, device="cpu", compile=False)

        # Warm up
        x = torch.randn(32, 100)
        for _ in range(10):
            optimizer.forward(x)

        # Benchmark
        num_iterations = 100
        start = time.perf_counter()
        for _ in range(num_iterations):
            optimizer.forward(x)
        elapsed = time.perf_counter() - start

        avg_time = elapsed / num_iterations
        # Overhead should be minimal (< 1ms per forward pass on CPU)
        assert avg_time < 0.001

    @pytest.mark.benchmark
    def test_batch_inference_efficiency(self):
        """Test batch inference is more efficient than individual predictions."""
        import time

        import torch
        import torch.nn as nn

        from python_optimizer.ml import InferenceOptimizer

        class BenchmarkModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(50, 10)

            def forward(self, x):
                return self.linear(x)

        model = BenchmarkModel()
        inf_opt = InferenceOptimizer(model, device="cpu", compile=False, batch_size=8)

        # Create test inputs
        inputs = [torch.randn(1, 50) for _ in range(32)]

        # Batch prediction
        start = time.perf_counter()
        batch_outputs = inf_opt.batch_predict(inputs)
        batch_time = time.perf_counter() - start

        # Individual predictions
        start = time.perf_counter()
        individual_outputs = [inf_opt.predict(x) for x in inputs]
        individual_time = time.perf_counter() - start

        # Batch should be faster or comparable
        assert len(batch_outputs) == len(individual_outputs)
        # Allow some tolerance for small batch sizes
        assert batch_time <= individual_time * 1.5
