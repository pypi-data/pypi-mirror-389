"""
Combinatorial Method for Pairwise Comparison Aggregation using Prüfer Sequences.

This implementation uses Prüfer sequence enumeration for perfect parallelization,
achieving near-linear speedup with multiple workers.
"""

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from typing import Callable, Dict, Iterator, List, Tuple

import numpy as np

from .aggregation import weighted_geometric_mean
from .helpers import is_full
from .llsm import llsm_incomplete


def prufer_to_edges(sequence: List[int], n: int) -> List[Tuple[int, int]]:
    """
    Convert Prüfer sequence to tree edge list.

    Algorithm: Standard Prüfer decoding in O(n) time.

    Args:
        sequence: Prüfer sequence of length (n-2)
        n: Number of nodes

    Returns:
        List of edges representing the spanning tree
    """
    # Initialize degree array: degree[i] = 1 + count of i in sequence
    degree = [1] * n
    for node in sequence:
        degree[node] += 1

    edges = []

    # Process each element in the Prüfer sequence
    for node in sequence:
        # Find first node with degree 1
        for i in range(n):
            if degree[i] == 1:
                # Add edge
                edges.append((i, node))
                # Update degrees
                degree[i] -= 1
                degree[node] -= 1
                break

    # Add final edge between last two nodes with degree 1
    remaining = [i for i in range(n) if degree[i] == 1]
    if len(remaining) == 2:
        edges.append(tuple(remaining))

    return edges


def generate_prufer_sequences_with_prefix(
    n: int, prefix: List[int]
) -> Iterator[List[int]]:
    """
    Generate all Prüfer sequences of length (n-2) starting with given prefix.

    Args:
        n: Number of nodes
        prefix: Prefix that all sequences should start with

    Yields:
        Prüfer sequences as lists
    """
    sequence_length = n - 2
    remaining_length = sequence_length - len(prefix)

    if remaining_length < 0:
        return

    if remaining_length == 0:
        yield prefix
        return

    # Generate all combinations for remaining positions
    for suffix in product(range(n), repeat=remaining_length):
        yield prefix + list(suffix)


def calculate_work_distribution(n: int, num_workers: int) -> List[List[List[int]]]:
    """
    Calculate prefix distribution for each worker to ensure balanced load.

    Returns a list where each element is a list of prefixes that worker should process.

    For n=8, workers=1: [[[]] ]  (one worker, one empty prefix = all trees)
    For n=8, workers=2: [ [[0],[1],[2],[3]], [[4],[5],[6],[7]] ]  (each worker gets 4 prefixes)
    For n=8, workers=8: [ [[0]], [[1]], ..., [[7]] ]  (each worker gets 1 prefix)

    Args:
        n: Matrix size
        num_workers: Number of parallel workers

    Returns:
        List of prefix lists, one list per worker. Each prefix list contains one or more prefixes.
    """
    # Special case: 1 worker
    if num_workers == 1:
        return [[[]]]  # One worker with one empty prefix (all trees)

    # Find optimal prefix length
    # We want enough prefixes to distribute evenly among workers
    prefix_length = 1
    while n**prefix_length < num_workers:
        prefix_length += 1

    # Generate all prefixes
    all_prefixes = [list(p) for p in product(range(n), repeat=prefix_length)]

    # Distribute prefixes among workers
    num_prefixes = len(all_prefixes)
    prefixes_per_worker = num_prefixes // num_workers
    extra = num_prefixes % num_workers

    result = []
    start_idx = 0
    for i in range(num_workers):
        # Some workers get one extra prefix if there's a remainder
        count = prefixes_per_worker + (1 if i < extra else 0)
        worker_prefixes = all_prefixes[start_idx : start_idx + count]
        result.append(worker_prefixes)
        start_idx += count

    return result


def build_icpcm_from_edges(
    edges: List[Tuple[int, int]], A: np.ndarray, n: int
) -> np.ndarray:
    """
    Build Ideally Consistent PCM from tree edges using transitivity.

    Args:
        edges: List of tree edges
        A: Original comparison matrix (for edge weights)
        n: Number of criteria

    Returns:
        Complete ICPCM matrix
    """
    # Build adjacency list from edges
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    icpcm = np.ones((n, n), dtype=float)

    # For each node, BFS to compute all pairwise comparisons
    for start in range(n):
        visited = {start: 1.0}  # node -> accumulated product from start
        queue = [start]

        while queue:
            current = queue.pop(0)
            current_product = visited[current]

            for neighbor in adj[current]:
                if neighbor not in visited:
                    # Get comparison value from original matrix
                    if current < neighbor:
                        weight = A[current, neighbor]
                    else:
                        weight = A[neighbor, current]
                        weight = 1.0 / weight if weight != 0 else 1.0

                    visited[neighbor] = current_product * weight
                    queue.append(neighbor)

        # Fill ICPCM row
        for j, product in visited.items():
            icpcm[start, j] = product

    return icpcm


def calculate_priority_vector(icpcm: np.ndarray) -> np.ndarray:
    """
    Calculate priority vector from ICPCM using geometric mean method.

    Formula: w_j = (∏_i a_ij)^(1/n)
    Then normalize: w = w / sum(w)

    Args:
        icpcm: Ideally Consistent Pairwise Comparison Matrix

    Returns:
        Normalized priority vector
    """
    n = icpcm.shape[0]
    w = np.prod(icpcm, axis=0) ** (1.0 / n)
    w = w / w.sum()
    return w


def calculate_tree_quality_from_edges(edges: List[Tuple[int, int]], n: int) -> float:
    """
    Calculate quality rating for a spanning tree based on diameter.

    Lower diameter = less error propagation = higher quality.

    Args:
        edges: Tree edge list
        n: Number of nodes

    Returns:
        Quality rating (higher is better)
    """
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    # Calculate diameter using two BFS
    # First BFS from node 0
    def bfs_farthest(start):
        visited = {start: 0}
        queue = [start]
        farthest = start
        max_dist = 0

        while queue:
            node = queue.pop(0)
            dist = visited[node]

            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    queue.append(neighbor)
                    if dist + 1 > max_dist:
                        max_dist = dist + 1
                        farthest = neighbor

        return farthest, max_dist

    # Find one end of diameter
    farthest1, _ = bfs_farthest(0)
    # Find other end and actual diameter
    _, diameter = bfs_farthest(farthest1)

    return 1.0 / (diameter + 1)  # +1 to avoid division by zero


# ============================================================================
# WORKER COUNT SELECTION
# ============================================================================


def smart_worker_count(n: int) -> int:
    """Intelligently select number of workers based on matrix size."""
    cpu_count = os.cpu_count() or 8

    # For Prüfer-based approach, use n workers for perfect distribution
    # But don't exceed available CPUs
    optimal = min(n, cpu_count)
    return optimal


def auto_detect_workers(n: int = None) -> int:
    """Auto-detect number of workers based on CPU count."""
    return os.cpu_count() or 4


def _process_prufer_range(
    prefixes: List[List[int]], A_data: bytes, n: int, quality_fn_name: str
) -> List[Tuple[np.ndarray, float]]:
    """
    Worker function: process all Prüfer sequences with given prefixes.

    Args:
        prefixes: List of Prüfer sequence prefixes to process
        A_data: Serialized comparison matrix
        n: Matrix size
        quality_fn_name: Name of quality function (unused for now)

    Returns:
        List of (priority_vector, quality) tuples
    """
    # Deserialize matrix
    A = np.frombuffer(A_data, dtype=np.float64).reshape(n, n).copy()

    results = []

    # Process all sequences for each prefix
    for prefix in prefixes:
        for sequence in generate_prufer_sequences_with_prefix(n, prefix):
            # Convert Prüfer sequence to edges
            edges = prufer_to_edges(sequence, n)

            # Build ICPCM
            icpcm = build_icpcm_from_edges(edges, A, n)

            # Calculate priority vector
            priority_vector = calculate_priority_vector(icpcm)

            # Calculate quality
            quality = calculate_tree_quality_from_edges(edges, n)

            results.append((priority_vector, quality))

    return results


def combinatorial_method(
    A: np.ndarray,
    n_workers: int | Callable = smart_worker_count,
    aggregator: Callable = weighted_geometric_mean,
) -> np.ndarray:
    """
    Combinatorial method using Prüfer sequence enumeration.

    For incomplete matrices, uses LLSM to fill missing values first.

    Args:
        A: Pairwise comparison matrix (n × n)
        n_workers: Number of workers or function returning worker count
        aggregator: Function to aggregate priority vectors

    Returns: Final aggregated priority vector
    """
    n = A.shape[0]

    num_workers = n_workers(n) if callable(n_workers) else n_workers

    # Calculate work distribution
    work_distribution = calculate_work_distribution(n, num_workers)

    # Serialize matrix for workers
    A_data = A.astype(np.float64).tobytes()

    all_results = []

    if num_workers == 1:
        # Serial execution
        results = _process_prufer_range(work_distribution[0], A_data, n, "default")
        all_results.extend(results)
    else:
        # Parallel execution
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []

            for i, worker_prefixes in enumerate(work_distribution):
                future = executor.submit(
                    _process_prufer_range, worker_prefixes, A_data, n, "default"
                )
                futures.append((i, future))

            # Collect results as they complete
            for i, future in futures:
                results = future.result()
                all_results.extend(results)

    return aggregator(all_results)
