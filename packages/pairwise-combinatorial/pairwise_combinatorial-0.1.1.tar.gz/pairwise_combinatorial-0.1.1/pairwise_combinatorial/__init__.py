"""
Pairwise Combinatorial - Combinatorial method for pairwise comparison aggregation.

This library implements the combinatorial method using Prüfer sequence enumeration
for perfect parallelization, achieving near-linear speedup with multiple workers.
"""

from .aggregation import (
    simple_arithmetic_mean,
    simple_geometric_mean,
    weighted_arithmetic_mean,
    weighted_geometric_mean,
)
from .combinatorial import (
    auto_detect_workers,
    combinatorial_method,
    smart_worker_count,
)
from .gen import (
    generate_comparison_matrix,
    saaty_generator,
)
from .helpers import (
    calculate_consistency_ratio,
    is_connected,
    is_full,
)
from .llsm import llsm_incomplete

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
