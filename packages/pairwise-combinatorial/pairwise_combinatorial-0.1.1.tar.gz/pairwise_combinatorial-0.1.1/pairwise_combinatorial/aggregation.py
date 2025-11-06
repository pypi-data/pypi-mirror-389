from typing import List, Tuple

import numpy as np


def simple_geometric_mean(results: List[Tuple[np.ndarray, float]]) -> np.ndarray:
    """Simple geometric mean aggregation (equal weight for all trees)."""
    vectors = np.array([v for v, q in results])
    log_vectors = np.log(vectors + 1e-10)
    log_mean = np.mean(log_vectors, axis=0)
    w_agg = np.exp(log_mean)
    return w_agg / w_agg.sum()


def weighted_geometric_mean(results: List[Tuple[np.ndarray, float]]) -> np.ndarray:
    """Weighted geometric mean aggregation using quality ratings."""
    vectors = np.array([v for v, q in results])
    qualities = np.array([q for v, q in results])
    qualities = qualities / qualities.sum()

    log_vectors = np.log(vectors + 1e-10)
    log_weighted_mean = np.sum(log_vectors * qualities[:, np.newaxis], axis=0)
    w_agg = np.exp(log_weighted_mean)
    return w_agg / w_agg.sum()


def simple_arithmetic_mean(results: List[Tuple[np.ndarray, float]]) -> np.ndarray:
    """Simple arithmetic mean aggregation (equal weight for all trees)."""
    vectors = np.array([v for v, q in results])
    w_agg = np.mean(vectors, axis=0)
    return w_agg / w_agg.sum()


def weighted_arithmetic_mean(results: List[Tuple[np.ndarray, float]]) -> np.ndarray:
    """Weighted arithmetic mean aggregation using quality ratings."""
    vectors = np.array([v for v, q in results])
    qualities = np.array([q for v, q in results])
    qualities = qualities / qualities.sum()

    w_agg = np.sum(vectors * qualities[:, np.newaxis], axis=0)
    return w_agg / w_agg.sum()
