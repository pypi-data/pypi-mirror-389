"""
Pairwise Combinatorial - Combinatorial method for pairwise comparison aggregation.

This library implements the combinatorial method using Prüfer sequence enumeration
for perfect parallelization, achieving near-linear speedup with multiple workers.
"""

from .combinatorial import (
    combinatorial_method,
    weighted_geometric_mean,
    simple_geometric_mean,
    weighted_arithmetic_mean,
    simple_arithmetic_mean,
    smart_worker_count,
    auto_detect_workers,
)
from .llsm import llsm_incomplete
from .helpers import (
    is_full,
    is_connected,
    calculate_consistency_ratio,
)
from .gen import (
    generate_comparison_matrix,
    saaty_generator,
)

__version__ = "0.1.0"

__all__ = [
    # Main method
    "combinatorial_method",
    # Aggregation functions - Geometric
    "weighted_geometric_mean",
    "simple_geometric_mean",
    # Aggregation functions - Arithmetic
    "weighted_arithmetic_mean",
    "simple_arithmetic_mean",
    # Worker selection
    "smart_worker_count",
    "auto_detect_workers",
    # LLSM
    "llsm_incomplete",
    # Helper functions
    "is_full",
    "is_connected",
    "calculate_consistency_ratio",
    # Matrix generation
    "generate_comparison_matrix",
    "saaty_generator",
]
