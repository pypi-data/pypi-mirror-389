"""ML Model Optimization Module

Provides optimization capabilities for machine learning models with focus on PyTorch.

Features:
- Automatic model compilation and optimization
- Training loop acceleration with mixed precision
- Inference optimization with dynamic batching
- GPU acceleration integration
- Memory optimization

Supported Frameworks:
- PyTorch (primary support)
- TensorFlow (planned)

Usage:
    from python_optimizer.ml import optimize_model, optimize_training

    # Optimize PyTorch model
    optimized_model = optimize_model(model, device='cuda')

    # Optimize training loop
    @optimize_training(mixed_precision=True, gpu=True)
    def train_step(model, data, target):
        # Training code
        pass
"""

# Try to import PyTorch
try:
    import torch

    PYTORCH_AVAILABLE = True
    PYTORCH_VERSION = torch.__version__
except ImportError:
    PYTORCH_AVAILABLE = False
    PYTORCH_VERSION = None
    torch = None

# Try to import TensorFlow
try:
    import tensorflow as tf

    TENSORFLOW_AVAILABLE = True
    TENSORFLOW_VERSION = tf.__version__
except ImportError:
    TENSORFLOW_AVAILABLE = False
    TENSORFLOW_VERSION = None
    tf = None

# Core ML optimization functions - PyTorch
from python_optimizer.ml.pytorch_optimizer import (
    InferenceOptimizer,
    PyTorchModelOptimizer,
    TrainingOptimizer,
    optimize_inference,
    optimize_model,
    optimize_training,
)

# Core ML optimization functions - TensorFlow
from python_optimizer.ml.tensorflow_optimizer import (
    TFInferenceOptimizer,
    TFModelOptimizer,
    TFTrainingOptimizer,
    optimize_tf_inference,
    optimize_tf_model,
    optimize_tf_training,
)

__all__ = [
    # PyTorch optimization
    "optimize_model",
    "optimize_training",
    "optimize_inference",
    "PyTorchModelOptimizer",
    "TrainingOptimizer",
    "InferenceOptimizer",
    # TensorFlow optimization
    "optimize_tf_model",
    "optimize_tf_training",
    "optimize_tf_inference",
    "TFModelOptimizer",
    "TFTrainingOptimizer",
    "TFInferenceOptimizer",
    # Framework availability
    "PYTORCH_AVAILABLE",
    "PYTORCH_VERSION",
    "TENSORFLOW_AVAILABLE",
    "TENSORFLOW_VERSION",
]


def check_framework_availability():
    """Check which ML frameworks are available.

    Returns:
        dict: Framework availability status
    """
    return {
        "pytorch": {
            "available": PYTORCH_AVAILABLE,
            "version": PYTORCH_VERSION,
        },
        "tensorflow": {
            "available": TENSORFLOW_AVAILABLE,
            "version": TENSORFLOW_VERSION,
        },
    }
