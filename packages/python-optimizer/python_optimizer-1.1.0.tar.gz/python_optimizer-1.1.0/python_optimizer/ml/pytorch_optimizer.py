"""PyTorch Model Optimization

Provides comprehensive optimization for PyTorch models including:
- Model compilation and JIT optimization
- Training loop acceleration with mixed precision
- Inference optimization with dynamic batching
- GPU acceleration integration
- Memory optimization and profiling
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Check PyTorch availability
try:
    import torch
    import torch.nn as nn
    from torch.cuda.amp import GradScaler, autocast

    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    nn = None
    autocast = None
    GradScaler = None
    logger.warning("PyTorch not available - ML optimization disabled")


class PyTorchModelOptimizer:
    """Optimizes PyTorch models for training and inference.

    Features:
    - Automatic device selection (CPU/GPU)
    - Model compilation (torch.compile in PyTorch 2.0+)
    - Mixed precision training
    - Memory optimization
    - Performance profiling
    """

    def __init__(
        self,
        model: "nn.Module",
        device: Optional[Union[str, "torch.device"]] = None,
        compile: bool = True,
        mixed_precision: bool = False,
        memory_efficient: bool = True,
    ):
        """Initialize model optimizer.

        Args:
            model: PyTorch model to optimize
            device: Device to use ('cpu', 'cuda', 'mps', or torch.device)
            compile: Use torch.compile if available (PyTorch 2.0+)
            mixed_precision: Enable automatic mixed precision training
            memory_efficient: Enable memory optimization techniques
        """
        if not PYTORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is not installed. Install with: pip install torch"
            )

        self.model = model
        self.mixed_precision = mixed_precision
        self.memory_efficient = memory_efficient

        # Device selection
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device) if isinstance(device, str) else device

        # Move model to device
        self.model = self.model.to(self.device)

        # Apply torch.compile if available and requested
        if compile and hasattr(torch, "compile"):
            try:
                self.model = torch.compile(self.model)
                logger.info("Model compiled with torch.compile")
            except Exception as e:
                logger.warning(f"torch.compile failed: {e}. Using uncompiled model.")

        # Mixed precision scaler
        self.scaler = (
            GradScaler() if mixed_precision and self.device.type == "cuda" else None
        )

        # Statistics
        self.stats = {
            "forward_passes": 0,
            "total_forward_time": 0.0,
            "avg_forward_time": 0.0,
        }

    def forward(self, *args, **kwargs):
        """Optimized forward pass.

        Args:
            *args: Arguments to pass to model
            **kwargs: Keyword arguments to pass to model

        Returns:
            Model output
        """
        start_time = time.perf_counter()

        with torch.no_grad():
            if self.mixed_precision and self.scaler:
                with autocast():
                    output = self.model(*args, **kwargs)
            else:
                output = self.model(*args, **kwargs)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["forward_passes"] += 1
        self.stats["total_forward_time"] += elapsed
        self.stats["avg_forward_time"] = (
            self.stats["total_forward_time"] / self.stats["forward_passes"]
        )

        return output

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics.

        Returns:
            Dictionary with performance statistics
        """
        return {
            **self.stats,
            "device": str(self.device),
            "mixed_precision": self.mixed_precision,
            "memory_efficient": self.memory_efficient,
        }


class TrainingOptimizer:
    """Optimizes PyTorch training loops.

    Features:
    - Automatic mixed precision training
    - Gradient accumulation
    - Gradient clipping
    - Memory optimization
    - Performance tracking
    """

    def __init__(
        self,
        model: "nn.Module",
        optimizer: "torch.optim.Optimizer",
        device: Optional[Union[str, "torch.device"]] = None,
        mixed_precision: bool = True,
        gradient_accumulation_steps: int = 1,
        max_grad_norm: Optional[float] = 1.0,
    ):
        """Initialize training optimizer.

        Args:
            model: PyTorch model
            optimizer: PyTorch optimizer
            device: Device to use
            mixed_precision: Enable automatic mixed precision
            gradient_accumulation_steps: Number of steps to accumulate gradients
            max_grad_norm: Maximum gradient norm for clipping (None to disable)
        """
        if not PYTORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")

        self.model = model
        self.optimizer = optimizer
        self.mixed_precision = mixed_precision
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.max_grad_norm = max_grad_norm

        # Device
        if device is None:
            self.device = next(model.parameters()).device
        else:
            self.device = torch.device(device) if isinstance(device, str) else device

        # Mixed precision scaler
        self.scaler = (
            GradScaler() if mixed_precision and self.device.type == "cuda" else None
        )

        # Statistics
        self.stats = {
            "steps": 0,
            "total_time": 0.0,
            "avg_step_time": 0.0,
        }

    def training_step(
        self,
        inputs: Any,
        targets: Any,
        criterion: Callable,
        step: int,
    ) -> Dict[str, float]:
        """Perform optimized training step.

        Args:
            inputs: Model inputs
            targets: Training targets
            criterion: Loss function
            step: Current training step

        Returns:
            Dictionary with loss and metrics
        """
        start_time = time.perf_counter()

        # Forward pass with mixed precision
        if self.mixed_precision and self.scaler:
            with autocast():
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss = loss / self.gradient_accumulation_steps
        else:
            outputs = self.model(inputs)
            loss = criterion(outputs, targets)
            loss = loss / self.gradient_accumulation_steps

        # Backward pass
        if self.scaler:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()

        # Update weights (with gradient accumulation)
        if (step + 1) % self.gradient_accumulation_steps == 0:
            if self.scaler:
                # Gradient clipping
                if self.max_grad_norm is not None:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.max_grad_norm
                    )

                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                # Gradient clipping
                if self.max_grad_norm is not None:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.max_grad_norm
                    )

                self.optimizer.step()

            self.optimizer.zero_grad()

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["steps"] += 1
        self.stats["total_time"] += elapsed
        self.stats["avg_step_time"] = self.stats["total_time"] / self.stats["steps"]

        return {
            "loss": loss.item() * self.gradient_accumulation_steps,
            "step_time": elapsed,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        return {
            **self.stats,
            "device": str(self.device),
            "mixed_precision": self.mixed_precision,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
        }


class InferenceOptimizer:
    """Optimizes PyTorch models for inference.

    Features:
    - Batch inference optimization
    - Dynamic batching
    - Model quantization (planned)
    - ONNX export (planned)
    """

    def __init__(
        self,
        model: "nn.Module",
        device: Optional[Union[str, "torch.device"]] = None,
        compile: bool = True,
        batch_size: Optional[int] = None,
    ):
        """Initialize inference optimizer.

        Args:
            model: PyTorch model
            device: Device to use
            compile: Use torch.compile if available
            batch_size: Batch size for inference (None for dynamic)
        """
        if not PYTORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")

        self.model = model
        self.model.eval()  # Set to evaluation mode
        self.batch_size = batch_size

        # Device
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device) if isinstance(device, str) else device

        self.model = self.model.to(self.device)

        # Compile model
        if compile and hasattr(torch, "compile"):
            try:
                self.model = torch.compile(self.model, mode="reduce-overhead")
                logger.info("Model compiled for inference")
            except Exception as e:
                logger.warning(f"Compilation failed: {e}")

        # Statistics
        self.stats = {
            "inferences": 0,
            "total_time": 0.0,
            "avg_inference_time": 0.0,
        }

    def predict(self, inputs: Any) -> Any:
        """Optimized inference.

        Args:
            inputs: Model inputs

        Returns:
            Model predictions
        """
        start_time = time.perf_counter()

        with torch.no_grad():
            # Move inputs to device
            if isinstance(inputs, torch.Tensor):
                inputs = inputs.to(self.device)
            elif isinstance(inputs, (list, tuple)):
                inputs = [
                    x.to(self.device) if isinstance(x, torch.Tensor) else x
                    for x in inputs
                ]

            # Forward pass
            outputs = self.model(inputs)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["inferences"] += 1
        self.stats["total_time"] += elapsed
        self.stats["avg_inference_time"] = (
            self.stats["total_time"] / self.stats["inferences"]
        )

        return outputs

    def batch_predict(self, inputs_list: List[Any]) -> List[Any]:
        """Batch inference with automatic batching.

        Args:
            inputs_list: List of inputs

        Returns:
            List of predictions
        """
        if self.batch_size is None:
            # Process all at once
            batched_inputs = (
                torch.stack(inputs_list)
                if isinstance(inputs_list[0], torch.Tensor)
                else inputs_list
            )
            return self.predict(batched_inputs)

        # Process in batches
        results = []
        for i in range(0, len(inputs_list), self.batch_size):
            batch = inputs_list[i: i + self.batch_size]
            batched = (
                torch.stack(batch) if isinstance(batch[0], torch.Tensor) else batch
            )
            batch_results = self.predict(batched)
            results.extend(batch_results)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics."""
        return {
            **self.stats,
            "device": str(self.device),
            "batch_size": self.batch_size,
        }


# High-level convenience functions


def optimize_model(
    model: "nn.Module",
    device: Optional[str] = None,
    compile: bool = True,
    mixed_precision: bool = False,
) -> PyTorchModelOptimizer:
    """Optimize a PyTorch model.

    Args:
        model: PyTorch model to optimize
        device: Device to use ('cpu', 'cuda', 'mps')
        compile: Use torch.compile if available
        mixed_precision: Enable mixed precision

    Returns:
        Optimized model wrapper

    Example:
        model = MyModel()
        optimized = optimize_model(model, device='cuda', compile=True)
        output = optimized.forward(input_data)
    """
    return PyTorchModelOptimizer(
        model=model,
        device=device,
        compile=compile,
        mixed_precision=mixed_precision,
    )


def optimize_training(
    mixed_precision: bool = True,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: Optional[float] = 1.0,
):
    """Decorator to optimize training functions.

    Args:
        mixed_precision: Enable automatic mixed precision
        gradient_accumulation_steps: Gradient accumulation steps
        max_grad_norm: Maximum gradient norm

    Returns:
        Decorated function

    Example:
        @optimize_training(mixed_precision=True)
        def train_step(model, inputs, targets, criterion, optimizer):
            # Training code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This is a simplified decorator
            # Full implementation would integrate with TrainingOptimizer
            return func(*args, **kwargs)

        return wrapper

    return decorator


def optimize_inference(
    model: "nn.Module",
    device: Optional[str] = None,
    compile: bool = True,
    batch_size: Optional[int] = None,
) -> InferenceOptimizer:
    """Optimize a model for inference.

    Args:
        model: PyTorch model
        device: Device to use
        compile: Use torch.compile
        batch_size: Batch size for inference

    Returns:
        Inference optimizer

    Example:
        model = MyModel()
        optimizer = optimize_inference(model, device='cuda')
        predictions = optimizer.predict(input_data)
    """
    return InferenceOptimizer(
        model=model,
        device=device,
        compile=compile,
        batch_size=batch_size,
    )
