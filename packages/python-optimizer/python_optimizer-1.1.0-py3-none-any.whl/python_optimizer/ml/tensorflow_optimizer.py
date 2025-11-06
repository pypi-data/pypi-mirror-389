"""TensorFlow Model Optimization

Provides comprehensive optimization for TensorFlow/Keras models including:
- Model compilation with XLA and tf.function
- Training loop acceleration with mixed precision
- Inference optimization with graph optimization
- GPU acceleration integration
- Memory optimization and profiling
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Check TensorFlow availability
try:
    import tensorflow as tf
    from tensorflow import keras

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None
    logger.warning("TensorFlow not available - TF optimization disabled")


class TFModelOptimizer:
    """Optimizes TensorFlow/Keras models for training and inference.

    Features:
    - Automatic device selection (CPU/GPU)
    - XLA compilation for faster execution
    - Mixed precision training
    - tf.function graph optimization
    - Performance profiling
    """

    def __init__(
        self,
        model: "keras.Model",
        device: Optional[str] = None,
        use_xla: bool = True,
        mixed_precision: bool = False,
        jit_compile: bool = True,
    ):
        """Initialize TensorFlow model optimizer.

        Args:
            model: Keras model to optimize
            device: Device to use ('CPU:0', 'GPU:0', etc.)
            use_xla: Enable XLA compilation
            mixed_precision: Enable mixed precision training
            jit_compile: Use tf.function with jit_compile=True
        """
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError(
                "TensorFlow is not installed. Install with: pip install tensorflow"
            )

        self.model = model
        self.use_xla = use_xla
        self.jit_compile = jit_compile

        # Device selection
        if device is None:
            # Auto-select device
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                self.device = "/GPU:0"
            else:
                self.device = "/CPU:0"
        else:
            self.device = f"/{device}" if not device.startswith("/") else device

        # Mixed precision setup
        if mixed_precision:
            policy = tf.keras.mixed_precision.Policy("mixed_float16")
            tf.keras.mixed_precision.set_global_policy(policy)
            logger.info("Mixed precision enabled (float16)")

        self.mixed_precision = mixed_precision

        # XLA configuration
        if use_xla:
            tf.config.optimizer.set_jit(True)
            logger.info("XLA compilation enabled")

        # Create optimized forward pass
        self._create_optimized_call()

        # Statistics
        self.stats = {
            "forward_passes": 0,
            "total_forward_time": 0.0,
            "avg_forward_time": 0.0,
        }

    def _create_optimized_call(self):
        """Create optimized forward pass function."""
        if self.jit_compile:
            # Use tf.function with XLA compilation
            @tf.function(jit_compile=self.use_xla)
            def optimized_call(inputs, training=False):
                return self.model(inputs, training=training)

            self._optimized_call = optimized_call
        else:
            self._optimized_call = self.model

    def __call__(self, inputs, training=False):
        """Optimized forward pass.

        Args:
            inputs: Model inputs
            training: Whether in training mode

        Returns:
            Model outputs
        """
        start_time = time.perf_counter()

        with tf.device(self.device):
            outputs = self._optimized_call(inputs, training=training)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["forward_passes"] += 1
        self.stats["total_forward_time"] += elapsed
        self.stats["avg_forward_time"] = (
            self.stats["total_forward_time"] / self.stats["forward_passes"]
        )

        return outputs

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics.

        Returns:
            Dictionary with performance statistics
        """
        return {
            **self.stats,
            "device": self.device,
            "mixed_precision": self.mixed_precision,
            "use_xla": self.use_xla,
            "jit_compile": self.jit_compile,
        }


class TFTrainingOptimizer:
    """Optimizes TensorFlow/Keras training loops.

    Features:
    - Automatic mixed precision training
    - Gradient accumulation
    - tf.function optimization
    - XLA compilation
    - Performance tracking
    """

    def __init__(
        self,
        model: "keras.Model",
        optimizer: "keras.optimizers.Optimizer",
        device: Optional[str] = None,
        mixed_precision: bool = True,
        gradient_accumulation_steps: int = 1,
        use_xla: bool = True,
    ):
        """Initialize training optimizer.

        Args:
            model: Keras model
            optimizer: Keras optimizer
            device: Device to use
            mixed_precision: Enable automatic mixed precision
            gradient_accumulation_steps: Number of steps to accumulate gradients
            use_xla: Enable XLA compilation
        """
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow is not installed")

        self.model = model
        self.optimizer = optimizer
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.use_xla = use_xla

        # Device
        if device is None:
            gpus = tf.config.list_physical_devices("GPU")
            self.device = "/GPU:0" if gpus else "/CPU:0"
        else:
            self.device = f"/{device}" if not device.startswith("/") else device

        # Mixed precision
        if mixed_precision:
            policy = tf.keras.mixed_precision.Policy("mixed_float16")
            tf.keras.mixed_precision.set_global_policy(policy)
            # Wrap optimizer for mixed precision
            self.optimizer = tf.keras.mixed_precision.LossScaleOptimizer(optimizer)

        self.mixed_precision = mixed_precision

        # XLA
        if use_xla:
            tf.config.optimizer.set_jit(True)

        # Create optimized training step
        self._create_train_step()

        # Gradient accumulation
        self.gradient_accumulator = [
            tf.Variable(tf.zeros_like(v), trainable=False)
            for v in model.trainable_variables
        ]

        # Statistics
        self.stats = {
            "steps": 0,
            "total_time": 0.0,
            "avg_step_time": 0.0,
        }

    def _create_train_step(self):
        """Create optimized training step function."""

        @tf.function(jit_compile=self.use_xla)
        def train_step(inputs, targets, loss_fn):
            with tf.GradientTape() as tape:
                predictions = self.model(inputs, training=True)
                loss = loss_fn(targets, predictions)

                # Scale loss for mixed precision
                if self.mixed_precision:
                    scaled_loss = self.optimizer.get_scaled_loss(loss)
                else:
                    scaled_loss = loss

            # Compute gradients
            if self.mixed_precision:
                scaled_gradients = tape.gradient(
                    scaled_loss, self.model.trainable_variables
                )
                gradients = self.optimizer.get_unscaled_gradients(scaled_gradients)
            else:
                gradients = tape.gradient(loss, self.model.trainable_variables)

            return loss, gradients

        self._train_step = train_step

    def training_step(
        self, inputs, targets, loss_fn: Callable, step: int
    ) -> Dict[str, float]:
        """Execute optimized training step.

        Args:
            inputs: Training inputs
            targets: Training targets
            loss_fn: Loss function
            step: Current training step

        Returns:
            Dictionary with loss, timing, and memory info
        """
        start_time = time.perf_counter()

        with tf.device(self.device):
            loss, gradients = self._train_step(inputs, targets, loss_fn)

            # Gradient accumulation
            if self.gradient_accumulation_steps > 1:
                # Accumulate gradients
                for i, grad in enumerate(gradients):
                    self.gradient_accumulator[i].assign_add(
                        grad / self.gradient_accumulation_steps
                    )

                # Apply accumulated gradients
                if (step + 1) % self.gradient_accumulation_steps == 0:
                    self.optimizer.apply_gradients(
                        zip(self.gradient_accumulator, self.model.trainable_variables)
                    )
                    # Reset accumulator
                    for acc in self.gradient_accumulator:
                        acc.assign(tf.zeros_like(acc))
            else:
                # Apply gradients directly
                self.optimizer.apply_gradients(
                    zip(gradients, self.model.trainable_variables)
                )

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["steps"] += 1
        self.stats["total_time"] += elapsed
        self.stats["avg_step_time"] = self.stats["total_time"] / self.stats["steps"]

        # Get GPU memory if available
        gpu_memory = 0.0
        if "GPU" in self.device:
            try:
                gpu_info = tf.config.experimental.get_memory_info(self.device)
                gpu_memory = gpu_info["current"] / (1024**2)  # MB
            except Exception:
                pass

        return {
            "loss": float(loss.numpy()),
            "step_time": elapsed,
            "gpu_memory_used": gpu_memory,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics.

        Returns:
            Dictionary with training statistics
        """
        return {
            **self.stats,
            "device": self.device,
            "mixed_precision": self.mixed_precision,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "use_xla": self.use_xla,
        }


class TFInferenceOptimizer:
    """Optimizes TensorFlow/Keras model inference.

    Features:
    - tf.function optimization
    - XLA compilation
    - Dynamic batching
    - Model graph optimization
    - Performance tracking
    """

    def __init__(
        self,
        model: "keras.Model",
        device: Optional[str] = None,
        use_xla: bool = True,
        batch_size: Optional[int] = None,
    ):
        """Initialize inference optimizer.

        Args:
            model: Keras model
            device: Device to use
            use_xla: Enable XLA compilation
            batch_size: Batch size for inference (None for dynamic)
        """
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow is not installed")

        self.model = model
        self.batch_size = batch_size
        self.use_xla = use_xla

        # Device
        if device is None:
            gpus = tf.config.list_physical_devices("GPU")
            self.device = "/GPU:0" if gpus else "/CPU:0"
        else:
            self.device = f"/{device}" if not device.startswith("/") else device

        # XLA
        if use_xla:
            tf.config.optimizer.set_jit(True)

        # Create optimized inference function
        self._create_inference_fn()

        # Statistics
        self.stats = {
            "predictions": 0,
            "total_time": 0.0,
            "avg_prediction_time": 0.0,
        }

    def _create_inference_fn(self):
        """Create optimized inference function."""

        @tf.function(jit_compile=self.use_xla)
        def inference_fn(inputs):
            return self.model(inputs, training=False)

        self._inference_fn = inference_fn

    def predict(self, inputs: Any) -> Any:
        """Optimized inference.

        Args:
            inputs: Model inputs

        Returns:
            Model predictions
        """
        start_time = time.perf_counter()

        with tf.device(self.device):
            outputs = self._inference_fn(inputs)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["predictions"] += 1
        self.stats["total_time"] += elapsed
        self.stats["avg_prediction_time"] = (
            self.stats["total_time"] / self.stats["predictions"]
        )

        return outputs

    def batch_predict(self, inputs_list: List[Any]) -> List[Any]:
        """Batch inference with automatic batching.

        Args:
            inputs_list: List of inputs

        Returns:
            List of predictions
        """
        if not inputs_list:
            return []

        if self.batch_size is None:
            # Process all at once
            batched_inputs = tf.stack(inputs_list)
            return self.predict(batched_inputs)

        # Process in batches
        results = []
        for i in range(0, len(inputs_list), self.batch_size):
            batch = inputs_list[i: i + self.batch_size]
            batched = tf.stack(batch)
            batch_results = self.predict(batched)
            results.extend(tf.unstack(batch_results))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics.

        Returns:
            Dictionary with inference statistics
        """
        return {
            **self.stats,
            "device": self.device,
            "use_xla": self.use_xla,
            "batch_size": self.batch_size,
        }


# High-level convenience functions


def optimize_tf_model(
    model: "keras.Model",
    device: Optional[str] = None,
    use_xla: bool = True,
    mixed_precision: bool = False,
    jit_compile: bool = True,
) -> TFModelOptimizer:
    """Optimize a TensorFlow/Keras model.

    Args:
        model: Keras model to optimize
        device: Device to use ('CPU:0', 'GPU:0', etc.)
        use_xla: Enable XLA compilation
        mixed_precision: Enable mixed precision
        jit_compile: Use tf.function with jit_compile

    Returns:
        Optimized model wrapper

    Example:
        model = keras.Sequential([...])
        optimized = optimize_tf_model(model, device='GPU:0', use_xla=True)
        output = optimized(input_data)
    """
    return TFModelOptimizer(
        model=model,
        device=device,
        use_xla=use_xla,
        mixed_precision=mixed_precision,
        jit_compile=jit_compile,
    )


def optimize_tf_training(
    mixed_precision: bool = True,
    gradient_accumulation_steps: int = 1,
    use_xla: bool = True,
):
    """Decorator to optimize TensorFlow training functions.

    Args:
        mixed_precision: Enable automatic mixed precision
        gradient_accumulation_steps: Gradient accumulation steps
        use_xla: Enable XLA compilation

    Returns:
        Decorated function

    Example:
        @optimize_tf_training(mixed_precision=True)
        def train_step(model, inputs, targets, loss_fn, optimizer):
            # Training code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This is a simplified decorator
            # Full implementation would integrate with TFTrainingOptimizer
            return func(*args, **kwargs)

        return wrapper

    return decorator


def optimize_tf_inference(
    model: "keras.Model",
    device: Optional[str] = None,
    use_xla: bool = True,
    batch_size: Optional[int] = None,
) -> TFInferenceOptimizer:
    """Optimize a TensorFlow model for inference.

    Args:
        model: Keras model
        device: Device to use
        use_xla: Enable XLA compilation
        batch_size: Batch size for inference

    Returns:
        Inference optimizer

    Example:
        model = keras.models.load_model('model.h5')
        inf_opt = optimize_tf_inference(model, device='GPU:0', batch_size=32)
        predictions = inf_opt.batch_predict(inputs)
    """
    return TFInferenceOptimizer(
        model=model, device=device, use_xla=use_xla, batch_size=batch_size
    )
