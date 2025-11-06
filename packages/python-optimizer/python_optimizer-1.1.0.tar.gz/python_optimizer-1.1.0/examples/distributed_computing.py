#!/usr/bin/env python3
"""
Distributed Computing Optimization Example

Demonstrates JIT optimization for distributed computing scenarios including:
- Message passing and serialization
- Parallel algorithm coordination
- Load balancing calculations
- Network communication patterns
- Distributed consensus algorithms
"""

import hashlib
import pickle
import queue
import random
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from python_optimizer import optimize

# =============================================================================
# Distributed System Data Structures
# =============================================================================


@dataclass
class Message:
    """Distributed system message."""

    sender_id: int
    receiver_id: int
    message_type: str
    payload: bytes
    timestamp: float
    sequence_number: int


@dataclass
class Node:
    """Distributed computing node."""

    node_id: int
    address: str
    port: int
    status: str
    load: float
    capacity: float


@dataclass
class Task:
    """Distributed task representation."""

    task_id: int
    priority: int
    estimated_duration: float
    memory_requirement: int
    cpu_requirement: float
    dependencies: List[int]


# =============================================================================
# Message Serialization & Communication (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_message_checksum(data, data_length):
    """JIT-optimized message checksum calculation."""
    checksum = 0
    for i in range(data_length):
        checksum = (checksum + int(data[i])) % 65536
        checksum = (checksum << 1) % 65536
    return checksum


@optimize(jit=True, fastmath=True, nogil=True)
def compress_message_data(input_data, output_data, input_length):
    """JIT-optimized simple message compression (RLE-like)."""
    if input_length == 0:
        return 0

    output_pos = 0
    current_byte = input_data[0]
    count = 1

    for i in range(1, input_length):
        if input_data[i] == current_byte and count < 255:
            count += 1
        else:
            # Write current run
            if output_pos + 1 < len(output_data):
                output_data[output_pos] = count
                output_data[output_pos + 1] = current_byte
                output_pos += 2

            current_byte = input_data[i]
            count = 1

    # Write final run
    if output_pos + 1 < len(output_data):
        output_data[output_pos] = count
        output_data[output_pos + 1] = current_byte
        output_pos += 2

    return output_pos


@optimize(jit=True, fastmath=True, nogil=True)
def decompress_message_data(compressed_data, output_data, compressed_length):
    """JIT-optimized message decompression."""
    output_pos = 0

    for i in range(0, compressed_length, 2):
        if i + 1 >= compressed_length:
            break

        count = compressed_data[i]
        byte_value = compressed_data[i + 1]

        for j in range(count):
            if output_pos < len(output_data):
                output_data[output_pos] = byte_value
                output_pos += 1

    return output_pos


# =============================================================================
# Load Balancing & Task Distribution (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def calculate_node_scores(
    node_loads, node_capacities, task_requirements, n_nodes, n_tasks
):
    """JIT-optimized node scoring for load balancing."""
    scores = np.zeros((n_nodes, n_tasks))

    for node_idx in range(n_nodes):
        current_load = node_loads[node_idx]
        capacity = node_capacities[node_idx]

        if capacity <= 0:
            continue

        utilization = current_load / capacity

        for task_idx in range(n_tasks):
            task_req = task_requirements[task_idx]

            # Check if node can handle the task
            if current_load + task_req > capacity:
                scores[node_idx, task_idx] = -1.0  # Cannot handle
            else:
                # Calculate score based on utilization after assignment
                new_utilization = (current_load + task_req) / capacity

                # Prefer balanced load distribution
                balance_score = 1.0 - abs(new_utilization - 0.5) * 2.0

                # Prefer nodes with more remaining capacity
                capacity_score = (capacity - current_load - task_req) / capacity

                # Combined score
                scores[node_idx, task_idx] = balance_score * 0.6 + capacity_score * 0.4

    return scores


@optimize(jit=True, fastmath=True, nogil=True)
def assign_tasks_greedy(node_scores, task_priorities, n_nodes, n_tasks):
    """JIT-optimized greedy task assignment algorithm."""
    assignments = np.full(n_tasks, -1, dtype=np.int32)
    assigned_count = 0

    # Create priority-sorted task indices
    task_indices = np.arange(n_tasks)

    # Simple bubble sort by priority (JIT-friendly)
    for i in range(n_tasks):
        for j in range(n_tasks - 1 - i):
            if task_priorities[task_indices[j]] < task_priorities[task_indices[j + 1]]:
                # Swap
                temp = task_indices[j]
                task_indices[j] = task_indices[j + 1]
                task_indices[j + 1] = temp

    # Assign tasks in priority order
    for i in range(n_tasks):
        task_idx = task_indices[i]

        best_node = -1
        best_score = -2.0

        for node_idx in range(n_nodes):
            score = node_scores[node_idx, task_idx]
            if score > best_score:
                best_score = score
                best_node = node_idx

        if best_node >= 0:
            assignments[task_idx] = best_node
            assigned_count += 1

    return assignments, assigned_count


# =============================================================================
# Distributed Consensus Algorithms (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def raft_leader_election(node_votes, node_terms, current_term, n_nodes):
    """JIT-optimized Raft consensus leader election."""
    vote_counts = np.zeros(n_nodes, dtype=np.int32)

    # Count votes for current term
    for i in range(n_nodes):
        if node_terms[i] == current_term and 0 <= node_votes[i] < n_nodes:
            vote_counts[node_votes[i]] += 1

    # Find leader (majority required)
    majority = (n_nodes // 2) + 1
    leader_id = -1

    for i in range(n_nodes):
        if vote_counts[i] >= majority:
            leader_id = i
            break

    return leader_id, vote_counts


@optimize(jit=True, fastmath=True, nogil=True)
def byzantine_fault_tolerance(
    node_values, node_signatures, byzantine_threshold, n_nodes
):
    """JIT-optimized Byzantine fault tolerance consensus."""
    # Simplified BFT - count identical values
    value_counts = {}
    trusted_count = 0

    # In a real implementation, signatures would be verified
    # Here we simulate by checking signature values
    for i in range(n_nodes):
        value = node_values[i]
        signature = node_signatures[i]

        # Simple signature validation (in real implementation, use cryptography)
        expected_signature = int(value * 12345 + 67890) % 100000

        if signature == expected_signature:
            trusted_count += 1

            # Count this value
            found = False
            for j in range(i):  # Check if we've seen this value
                if abs(node_values[j] - value) < 1e-9:
                    found = True
                    break

            if not found:
                # New unique value, count occurrences
                count = 1
                for j in range(i + 1, n_nodes):
                    if abs(node_values[j] - value) < 1e-9:
                        count += 1

                if count > byzantine_threshold:
                    return value, count

    return 0.0, 0  # No consensus


# =============================================================================
# Parallel Algorithm Coordination (JIT Optimized)
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def mapreduce_mapper(input_data, output_keys, output_values, input_size, hash_buckets):
    """JIT-optimized MapReduce mapper function."""
    output_count = 0

    for i in range(input_size):
        data_item = input_data[i]

        # Simple word count example - count occurrences of each value
        key = int(data_item) % hash_buckets
        value = 1.0

        if output_count < len(output_keys):
            output_keys[output_count] = key
            output_values[output_count] = value
            output_count += 1

    return output_count


@optimize(jit=True, fastmath=True, nogil=True)
def mapreduce_reducer(input_keys, input_values, output_keys, output_values, input_size):
    """JIT-optimized MapReduce reducer function."""
    # Group by key and sum values
    key_sums = {}
    output_count = 0

    # Simple reduction - sum values for each key
    for i in range(input_size):
        key = input_keys[i]
        value = input_values[i]

        # Find existing key or create new entry
        found = False
        for j in range(output_count):
            if output_keys[j] == key:
                output_values[j] += value
                found = True
                break

        if not found and output_count < len(output_keys):
            output_keys[output_count] = key
            output_values[output_count] = value
            output_count += 1

    return output_count


@optimize(jit=True, fastmath=True, nogil=True)
def barrier_synchronization(
    node_states, node_timestamps, barrier_id, timeout_seconds, n_nodes
):
    """JIT-optimized barrier synchronization for distributed algorithms."""
    current_time = time.time()
    ready_count = 0
    timeout_count = 0

    for i in range(n_nodes):
        node_time = node_timestamps[i]
        state = node_states[i]

        if state == barrier_id:  # Node is at this barrier
            if current_time - node_time <= timeout_seconds:
                ready_count += 1
            else:
                timeout_count += 1

    # All nodes ready
    if ready_count == n_nodes:
        return 1, ready_count  # Success

    # Some nodes timed out
    if timeout_count > 0:
        return -1, timeout_count  # Timeout

    # Still waiting
    return 0, ready_count  # Waiting


# =============================================================================
# Distributed Computing Simulation
# =============================================================================


class DistributedSystem:
    """Distributed computing system simulation."""

    def __init__(self, n_nodes: int = 10):
        self.n_nodes = n_nodes
        self.nodes = []
        self.message_queue = queue.Queue()
        self.task_queue = []
        self.performance_stats = {
            "messages_processed": 0,
            "tasks_completed": 0,
            "consensus_rounds": 0,
            "total_latency": 0.0,
        }

        # Initialize nodes
        for i in range(n_nodes):
            node = Node(
                node_id=i,
                address=f"192.168.1.{i+10}",
                port=8000 + i,
                status="active",
                load=random.uniform(0.1, 0.5),
                capacity=random.uniform(0.8, 1.0),
            )
            self.nodes.append(node)

    def simulate_message_passing(self, n_messages: int = 1000):
        """Simulate distributed message passing."""
        message_sizes = []
        compression_ratios = []

        for i in range(n_messages):
            # Generate random message data
            data_size = random.randint(100, 1000)
            message_data = np.random.randint(0, 256, size=data_size, dtype=np.uint8)

            # Compress message
            compressed_data = np.zeros(data_size * 2, dtype=np.uint8)  # Worst case
            compressed_size = compress_message_data(
                message_data, compressed_data, data_size
            )

            # Calculate checksum
            checksum = calculate_message_checksum(compressed_data, compressed_size)

            # Track statistics
            message_sizes.append(data_size)
            if data_size > 0:
                compression_ratios.append(compressed_size / data_size)

            self.performance_stats["messages_processed"] += 1

        return {
            "avg_message_size": np.mean(message_sizes),
            "avg_compression_ratio": np.mean(compression_ratios),
            "total_messages": n_messages,
        }

    def simulate_load_balancing(self, n_tasks: int = 100):
        """Simulate distributed task load balancing."""
        # Generate random tasks
        task_requirements = np.random.uniform(0.1, 0.4, n_tasks)
        task_priorities = np.random.randint(1, 10, n_tasks)

        # Extract node information
        node_loads = np.array([node.load for node in self.nodes])
        node_capacities = np.array([node.capacity for node in self.nodes])

        # Calculate assignment scores
        start_time = time.perf_counter()
        scores = calculate_node_scores(
            node_loads, node_capacities, task_requirements, self.n_nodes, n_tasks
        )

        # Assign tasks
        assignments, assigned_count = assign_tasks_greedy(
            scores, task_priorities, self.n_nodes, n_tasks
        )
        end_time = time.perf_counter()

        self.performance_stats["tasks_completed"] += assigned_count
        assignment_time = end_time - start_time

        return {
            "assigned_tasks": assigned_count,
            "total_tasks": n_tasks,
            "assignment_efficiency": assigned_count / n_tasks,
            "assignment_time": assignment_time,
        }

    def simulate_consensus(self, n_rounds: int = 50):
        """Simulate distributed consensus algorithms."""
        consensus_results = []

        for round_num in range(n_rounds):
            # Raft leader election
            node_votes = np.random.randint(0, self.n_nodes, self.n_nodes)
            node_terms = np.full(self.n_nodes, round_num, dtype=np.int32)

            leader_id, vote_counts = raft_leader_election(
                node_votes, node_terms, round_num, self.n_nodes
            )

            # Byzantine fault tolerance
            node_values = np.random.uniform(0, 100, self.n_nodes)
            node_signatures = np.array(
                [int(val * 12345 + 67890) % 100000 for val in node_values]
            )

            # Add some Byzantine faults (incorrect signatures)
            n_faults = random.randint(0, self.n_nodes // 3)
            fault_indices = random.sample(range(self.n_nodes), n_faults)
            for idx in fault_indices:
                node_signatures[idx] = random.randint(0, 99999)

            consensus_value, consensus_count = byzantine_fault_tolerance(
                node_values, node_signatures, self.n_nodes // 2, self.n_nodes
            )

            consensus_results.append(
                {
                    "leader_elected": leader_id >= 0,
                    "byzantine_consensus": consensus_count > 0,
                    "leader_id": leader_id,
                    "consensus_value": consensus_value,
                }
            )

            self.performance_stats["consensus_rounds"] += 1

        return {
            "total_rounds": n_rounds,
            "successful_elections": sum(
                1 for r in consensus_results if r["leader_elected"]
            ),
            "successful_consensus": sum(
                1 for r in consensus_results if r["byzantine_consensus"]
            ),
            "election_rate": sum(1 for r in consensus_results if r["leader_elected"])
            / n_rounds,
            "consensus_rate": sum(
                1 for r in consensus_results if r["byzantine_consensus"]
            )
            / n_rounds,
        }


def benchmark_distributed_system():
    """Comprehensive distributed computing benchmark."""
    print("🌐 Distributed Computing System Benchmark")
    print("=" * 60)

    # Initialize distributed system
    system = DistributedSystem(n_nodes=20)

    # 1. Message Passing Benchmark
    print("\n📨 Message Passing & Serialization")
    print("-" * 40)

    start_time = time.perf_counter()
    message_stats = system.simulate_message_passing(5000)
    message_time = time.perf_counter() - start_time

    print(f"Messages processed:    {message_stats['total_messages']}")
    print(f"Average message size:  {message_stats['avg_message_size']:.1f} bytes")
    print(f"Compression ratio:     {message_stats['avg_compression_ratio']:.3f}")
    print(f"Processing time:       {message_time:.4f}s")
    print(
        f"Throughput:           {message_stats['total_messages']/message_time:.0f} msg/sec"
    )

    # 2. Load Balancing Benchmark
    print("\n⚖️ Load Balancing & Task Distribution")
    print("-" * 40)

    start_time = time.perf_counter()
    load_balance_stats = system.simulate_load_balancing(500)
    load_balance_time = time.perf_counter() - start_time

    print(
        f"Tasks assigned:        {load_balance_stats['assigned_tasks']}/{load_balance_stats['total_tasks']}"
    )
    print(f"Assignment efficiency: {load_balance_stats['assignment_efficiency']:.2%}")
    print(f"Assignment time:       {load_balance_stats['assignment_time']:.6f}s")
    print(
        f"Tasks per second:      {load_balance_stats['assigned_tasks']/load_balance_time:.0f}"
    )

    # 3. Consensus Algorithm Benchmark
    print("\n🤝 Distributed Consensus")
    print("-" * 40)

    start_time = time.perf_counter()
    consensus_stats = system.simulate_consensus(100)
    consensus_time = time.perf_counter() - start_time

    print(f"Consensus rounds:      {consensus_stats['total_rounds']}")
    print(f"Leader election rate:  {consensus_stats['election_rate']:.2%}")
    print(f"Byzantine consensus:   {consensus_stats['consensus_rate']:.2%}")
    print(f"Total consensus time:  {consensus_time:.4f}s")
    print(
        f"Rounds per second:     {consensus_stats['total_rounds']/consensus_time:.0f}"
    )

    # 4. MapReduce Simulation
    print("\n🗺️ MapReduce Processing")
    print("-" * 40)

    # Simulate MapReduce workload
    input_data = np.random.randint(0, 1000, 10000)
    map_keys = np.zeros(10000, dtype=np.int32)
    map_values = np.zeros(10000)

    start_time = time.perf_counter()
    map_count = mapreduce_mapper(input_data, map_keys, map_values, len(input_data), 100)

    reduce_keys = np.zeros(1000, dtype=np.int32)
    reduce_values = np.zeros(1000)
    reduce_count = mapreduce_reducer(
        map_keys[:map_count],
        map_values[:map_count],
        reduce_keys,
        reduce_values,
        map_count,
    )
    mapreduce_time = time.perf_counter() - start_time

    print(f"Input records:         {len(input_data):,}")
    print(f"Map output pairs:      {map_count:,}")
    print(f"Reduce output pairs:   {reduce_count}")
    print(f"MapReduce time:        {mapreduce_time:.4f}s")
    print(f"Records per second:    {len(input_data)/mapreduce_time:.0f}")

    # 5. Barrier Synchronization
    print("\n🚧 Barrier Synchronization")
    print("-" * 40)

    node_states = np.full(system.n_nodes, 1, dtype=np.int32)  # All at barrier 1
    node_timestamps = np.full(system.n_nodes, time.time())

    start_time = time.perf_counter()
    for _ in range(1000):  # Test synchronization overhead
        result, count = barrier_synchronization(
            node_states, node_timestamps, 1, 10.0, system.n_nodes
        )
    barrier_time = time.perf_counter() - start_time

    print(f"Barrier checks:        1,000")
    print(f"Synchronization time:  {barrier_time:.4f}s")
    print(f"Checks per second:     {1000/barrier_time:.0f}")
    print(f"Nodes synchronized:    {count}/{system.n_nodes}")

    # Summary
    print("\n🏆 Distributed System Performance Summary")
    print("=" * 60)
    total_ops = (
        message_stats["total_messages"]
        + load_balance_stats["assigned_tasks"]
        + consensus_stats["total_rounds"]
        + len(input_data)
    )
    total_time = message_time + load_balance_time + consensus_time + mapreduce_time

    print(f"Total Operations:          {total_ops:,}")
    print(f"Total Processing Time:     {total_time:.4f}s")
    print(f"Overall Throughput:        {total_ops/total_time:.0f} ops/sec")
    print(
        f"Message Processing Rate:   {message_stats['total_messages']/message_time:.0f} msg/sec"
    )
    print(
        f"Task Assignment Rate:      {load_balance_stats['assigned_tasks']/load_balance_time:.0f} tasks/sec"
    )
    print(
        f"Consensus Rate:           {consensus_stats['total_rounds']/consensus_time:.0f} rounds/sec"
    )
    print(f"MapReduce Rate:           {len(input_data)/mapreduce_time:.0f} records/sec")

    return {
        "message_throughput": message_stats["total_messages"] / message_time,
        "task_assignment_rate": load_balance_stats["assigned_tasks"]
        / load_balance_time,
        "consensus_rate": consensus_stats["total_rounds"] / consensus_time,
        "mapreduce_rate": len(input_data) / mapreduce_time,
        "overall_throughput": total_ops / total_time,
    }


if __name__ == "__main__":
    results = benchmark_distributed_system()
    print("\n✨ Distributed computing optimization complete!")
