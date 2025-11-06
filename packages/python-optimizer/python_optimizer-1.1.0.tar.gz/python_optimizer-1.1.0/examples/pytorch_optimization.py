"""PyTorch Model Optimization Example

Demonstrates how to optimize PyTorch models for training and inference
using python-optimizer's ML module.

Requirements:
    pip install torch torchvision
"""

import torch
import torch.nn as nn
import torch.optim as optim
import time
import numpy as np

# Check if python_optimizer ML module is available
try:
    from python_optimizer.ml import (
        optimize_model,
        optimize_inference,
        TrainingOptimizer,
        PYTORCH_AVAILABLE,
    )

    if not PYTORCH_AVAILABLE:
        print("PyTorch not installed. Install with: pip install torch")
        exit(1)
except ImportError:
    print("python_optimizer ML module not available")
    exit(1)


# Define a simple neural network
class SimpleNN(nn.Module):
    """Simple neural network for demonstration."""

    def __init__(self, input_size=784, hidden_size=128, num_classes=10):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


def example_1_model_optimization():
    """Example 1: Basic model optimization."""
    print("=" * 70)
    print("Example 1: Basic Model Optimization")
    print("=" * 70)

    # Create model
    model = SimpleNN()
    print(f"Created model: {model.__class__.__name__}")

    # Optimize model
    optimized = optimize_model(model, device='cpu', compile=False)
    print(f"Model optimized - Device: {optimized.device}")

    # Test inference
    dummy_input = torch.randn(32, 784)
    output = optimized.forward(dummy_input)
    print(f"Output shape: {output.shape}")

    # Get statistics
    stats = optimized.get_stats()
    print(f"Forward passes: {stats['forward_passes']}")
    print()


def example_2_training_optimization():
    """Example 2: Training loop optimization."""
    print("=" * 70)
    print("Example 2: Training Loop Optimization")
    print("=" * 70)

    # Create model and optimizer
    model = SimpleNN().to('cpu')
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    # Create training optimizer
    training_opt = TrainingOptimizer(
        model=model,
        optimizer=optimizer,
        mixed_precision=False,  # Disable for CPU
        gradient_accumulation_steps=2,
    )

    print(f"Training optimizer created")
    print(f"Device: {training_opt.device}")
    print(f"Mixed precision: {training_opt.mixed_precision}")

    # Simulate training steps
    print("\nSimulating training steps...")
    for step in range(10):
        inputs = torch.randn(32, 784)
        targets = torch.randint(0, 10, (32,))

        metrics = training_opt.training_step(inputs, targets, criterion, step)
        if step % 5 == 0:
            print(f"Step {step}: Loss = {metrics['loss']:.4f}, "
                  f"Time = {metrics['step_time']*1000:.2f}ms")

    # Get training statistics
    stats = training_opt.get_stats()
    print(f"\nTotal steps: {stats['steps']}")
    print(f"Avg step time: {stats['avg_step_time']*1000:.2f}ms")
    print()


def example_3_inference_optimization():
    """Example 3: Inference optimization."""
    print("=" * 70)
    print("Example 3: Inference Optimization")
    print("=" * 70)

    # Create and optimize model for inference
    model = SimpleNN()
    inference_opt = optimize_inference(model, device='cpu', compile=False)

    print(f"Inference optimizer created")
    print(f"Device: {inference_opt.device}")

    # Single prediction
    single_input = torch.randn(1, 784)
    prediction = inference_opt.predict(single_input)
    print(f"Single prediction shape: {prediction.shape}")

    # Batch prediction
    batch_inputs = [torch.randn(1, 784) for _ in range(100)]
    start = time.perf_counter()
    predictions = inference_opt.batch_predict(batch_inputs)
    elapsed = time.perf_counter() - start

    print(f"Batch predictions: {len(predictions)} in {elapsed*1000:.2f}ms")

    # Get inference statistics
    stats = inference_opt.get_stats()
    print(f"Total inferences: {stats['inferences']}")
    print(f"Avg inference time: {stats['avg_inference_time']*1000:.2f}ms")
    print()


def example_4_performance_comparison():
    """Example 4: Performance comparison."""
    print("=" * 70)
    print("Example 4: Performance Comparison (Optimized vs Unoptimized)")
    print("=" * 70)

    # Unoptimized model
    model_base = SimpleNN().eval()
    
    # Optimized model
    model_opt = SimpleNN()
    optimizer = optimize_inference(model_opt, device='cpu', compile=False)

    # Test data
    test_data = torch.randn(100, 784)
    
    # Benchmark unoptimized
    start = time.perf_counter()
    with torch.no_grad():
        for i in range(100):
            _ = model_base(test_data[i:i+1])
    unopt_time = time.perf_counter() - start

    # Benchmark optimized
    start = time.perf_counter()
    for i in range(100):
        _ = optimizer.predict(test_data[i:i+1])
    opt_time = time.perf_counter() - start

    print(f"Unoptimized: {unopt_time*1000:.2f}ms for 100 inferences")
    print(f"Optimized:   {opt_time*1000:.2f}ms for 100 inferences")
    print(f"Speedup:     {unopt_time/opt_time:.2f}x")
    print()


def main():
    """Run all PyTorch optimization examples."""
    print("\n" + "=" * 70)
    print("Python Optimizer - PyTorch Integration Examples")
    print("=" * 70)
    print()

    examples = [
        example_1_model_optimization,
        example_2_training_optimization,
        example_3_inference_optimization,
        example_4_performance_comparison,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
