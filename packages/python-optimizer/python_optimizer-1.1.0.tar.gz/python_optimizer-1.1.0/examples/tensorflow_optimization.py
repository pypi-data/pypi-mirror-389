"""TensorFlow/Keras Model Optimization Examples

Demonstrates comprehensive optimization for TensorFlow models including:
- Model optimization with XLA
- Training loop acceleration with mixed precision
- Inference optimization with dynamic batching
- Performance benchmarking
"""

import time

import numpy as np
import tensorflow as tf

from python_optimizer.ml import (
    TFInferenceOptimizer,
    TFModelOptimizer,
    TFTrainingOptimizer,
    optimize_tf_inference,
    optimize_tf_model,
    optimize_tf_training,
)

print("=" * 80)
print("TensorFlow/Keras Model Optimization Examples")
print("=" * 80)

# ============================================================================
# Example 1: Basic Model Optimization
# ============================================================================

print("\n" + "=" * 80)
print("Example 1: Basic Model Optimization with XLA")
print("=" * 80)

# Create a simple sequential model
model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(128, activation="relu", input_shape=(784,)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)

# Optimize model with XLA
print("\nOptimizing model with XLA...")
optimized_model = optimize_tf_model(model, device="CPU:0", use_xla=True)

# Create sample data
x_sample = tf.random.normal((32, 784))

# Run inference with optimized model
print("\nRunning optimized inference...")
output = optimized_model(x_sample)
print(f"Output shape: {output.shape}")

# Get statistics
stats = optimized_model.get_stats()
print(f"\nOptimization Statistics:")
print(f"  Forward passes: {stats['forward_passes']}")
print(f"  Avg forward time: {stats['avg_forward_time']:.6f}s")
print(f"  Device: {stats['device']}")
print(f"  XLA enabled: {stats['use_xla']}")

# ============================================================================
# Example 2: Training Loop Optimization
# ============================================================================

print("\n" + "=" * 80)
print("Example 2: Training Loop Optimization with Mixed Precision")
print("=" * 80)

# Create a simple CNN for image classification
model = tf.keras.Sequential(
    [
        tf.keras.layers.Conv2D(32, 3, activation="relu", input_shape=(28, 28, 1)),
        tf.keras.layers.MaxPooling2D(2),
        tf.keras.layers.Conv2D(64, 3, activation="relu"),
        tf.keras.layers.MaxPooling2D(2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)

# Setup training
optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()

# Create training optimizer with mixed precision
print("\nCreating training optimizer with mixed precision...")
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    device="CPU:0",
    mixed_precision=False,  # Set to True if GPU available
    gradient_accumulation_steps=2,
    use_xla=False,  # Set to True for additional speedup
)

# Generate synthetic training data
print("\nGenerating synthetic training data...")
x_train = tf.random.normal((128, 28, 28, 1))
y_train = tf.random.uniform((128,), minval=0, maxval=10, dtype=tf.int32)

# Training loop
print("\nTraining for 10 steps...")
num_steps = 10
for step in range(num_steps):
    # Get batch
    batch_x = x_train[step * 8 : (step + 1) * 8]
    batch_y = y_train[step * 8 : (step + 1) * 8]

    # Training step
    result = training_opt.training_step(batch_x, batch_y, loss_fn, step)

    if step % 5 == 0:
        print(
            f"  Step {step}: Loss={result['loss']:.4f}, "
            f"Time={result['step_time']:.4f}s"
        )

# Get training statistics
stats = training_opt.get_stats()
print(f"\nTraining Statistics:")
print(f"  Total steps: {stats['steps']}")
print(f"  Total time: {stats['total_time']:.2f}s")
print(f"  Avg step time: {stats['avg_step_time']:.4f}s")
print(f"  Mixed precision: {stats['mixed_precision']}")
print(f"  Gradient accumulation: {stats['gradient_accumulation_steps']}")

# ============================================================================
# Example 3: Inference Optimization with Dynamic Batching
# ============================================================================

print("\n" + "=" * 80)
print("Example 3: Inference Optimization with Dynamic Batching")
print("=" * 80)

# Create inference model
model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(64, activation="relu", input_shape=(100,)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)

# Optimize for inference with dynamic batching
print("\nOptimizing model for inference...")
inf_opt = optimize_tf_inference(model, device="CPU:0", use_xla=True, batch_size=16)

# Generate test data (list of individual inputs)
print("\nGenerating test data...")
test_inputs = [tf.random.normal((1, 100)) for _ in range(50)]

# Batch prediction
print(f"\nRunning batch inference on {len(test_inputs)} inputs...")
outputs = inf_opt.batch_predict(test_inputs)
print(f"Processed {len(outputs)} predictions")

# Get inference statistics
stats = inf_opt.get_stats()
print(f"\nInference Statistics:")
print(f"  Total predictions: {stats['predictions']}")
print(f"  Total time: {stats['total_time']:.4f}s")
print(f"  Avg prediction time: {stats['avg_prediction_time']:.6f}s")
print(f"  Throughput: {len(test_inputs)/stats['total_time']:.1f} pred/s")
print(f"  Batch size: {stats['batch_size']}")

# ============================================================================
# Example 4: Performance Comparison
# ============================================================================

print("\n" + "=" * 80)
print("Example 4: Performance Comparison (Optimized vs Baseline)")
print("=" * 80)

# Create model for comparison
model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(256, activation="relu", input_shape=(784,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)

# Test data
x_test = tf.random.normal((100, 784))

# Baseline performance
print("\nMeasuring baseline performance...")
baseline_times = []
for _ in range(10):  # Warm up
    model(x_test, training=False)

for _ in range(100):
    start = time.perf_counter()
    model(x_test, training=False)
    baseline_times.append(time.perf_counter() - start)

baseline_avg = np.mean(baseline_times)
print(f"Baseline avg time: {baseline_avg:.6f}s")

# Optimized performance
print("\nOptimizing model with XLA and tf.function...")
optimized_model = TFModelOptimizer(
    model, device="CPU:0", use_xla=True, jit_compile=True
)

# Warm up optimized model
for _ in range(10):
    optimized_model(x_test)

optimized_times = []
for _ in range(100):
    start = time.perf_counter()
    optimized_model(x_test)
    optimized_times.append(time.perf_counter() - start)

optimized_avg = np.mean(optimized_times)
print(f"Optimized avg time: {optimized_avg:.6f}s")

# Calculate speedup
speedup = baseline_avg / optimized_avg
print(f"\nSpeedup: {speedup:.2f}x")
print(f"Time reduction: {(1 - optimized_avg/baseline_avg) * 100:.1f}%")

# ============================================================================
# Example 5: Custom Training Loop with Decorator
# ============================================================================

print("\n" + "=" * 80)
print("Example 5: Custom Training Loop with Decorator")
print("=" * 80)


@optimize_tf_training(mixed_precision=False, use_xla=False)
def custom_train_step(model, inputs, targets, loss_fn, optimizer):
    """Custom training step with decorator."""
    with tf.GradientTape() as tape:
        predictions = model(inputs, training=True)
        loss = loss_fn(targets, predictions)

    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))

    return float(loss.numpy())


# Create model and setup
model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(32, activation="relu", input_shape=(10,)),
        tf.keras.layers.Dense(1),
    ]
)
optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)
loss_fn = tf.keras.losses.MeanSquaredError()

# Generate data
x_train = tf.random.normal((50, 10))
y_train = tf.random.normal((50, 1))

# Train with decorator
print("\nTraining with decorated function...")
for step in range(10):
    batch_x = x_train[step * 5 : (step + 1) * 5]
    batch_y = y_train[step * 5 : (step + 1) * 5]

    loss = custom_train_step(model, batch_x, batch_y, loss_fn, optimizer)

    if step % 5 == 0:
        print(f"  Step {step}: Loss={loss:.4f}")

print("\nTraining complete!")

# ============================================================================
# Example 6: Multi-Output Model Optimization
# ============================================================================

print("\n" + "=" * 80)
print("Example 6: Multi-Output Model Optimization")
print("=" * 80)

# Create multi-output model
input_layer = tf.keras.Input(shape=(100,))
hidden = tf.keras.layers.Dense(64, activation="relu")(input_layer)
output1 = tf.keras.layers.Dense(10, activation="softmax", name="output1")(hidden)
output2 = tf.keras.layers.Dense(5, activation="softmax", name="output2")(hidden)

model = tf.keras.Model(inputs=input_layer, outputs=[output1, output2])

# Optimize model
print("\nOptimizing multi-output model...")
optimized_model = TFModelOptimizer(model, device="CPU:0", use_xla=True)

# Test inference
x_test = tf.random.normal((32, 100))
out1, out2 = optimized_model(x_test)

print(f"\nMulti-output inference:")
print(f"  Output 1 shape: {out1.shape}")
print(f"  Output 2 shape: {out2.shape}")

# Get statistics
stats = optimized_model.get_stats()
print(f"\nOptimization Statistics:")
print(f"  Forward passes: {stats['forward_passes']}")
print(f"  Avg time: {stats['avg_forward_time']:.6f}s")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("Examples Complete!")
print("=" * 80)
print("\nKey Takeaways:")
print("  1. XLA compilation provides 1.2-2.5x speedup for most models")
print("  2. Mixed precision training accelerates GPU training by 1.5-3x")
print("  3. Dynamic batching improves inference throughput by 2-10x")
print("  4. tf.function optimization reduces overhead significantly")
print("  5. Gradient accumulation enables larger effective batch sizes")
print("\nFor more information, see docs/tensorflow_optimization.md")
