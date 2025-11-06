import numpy as np
from typing import Callable

_rng = np.random.default_rng()

def saaty_generator(i: int, j: int) -> float:
    """
    Generates random values from Saaty scale (1, 2, 3, 4, 5, 6, 7, 8, 9).

    Args:
        i: row index
        j: column index

    Returns:
        Random value from Saaty scale
    """
    saaty_scale = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=float)
    return _rng.choice(saaty_scale)

def generate_comparison_matrix(
    n: int,
    missing_ratio: float = 0.0,
    generator: Callable[[int, int], float] = saaty_generator
) -> np.ndarray:
    """
    Generates a pairwise comparison matrix.

    Args:
        n: matrix dimension (number of criteria)
        missing_ratio: ratio of missing comparisons (0.0 to 1.0)
        generator: lambda function that accepts (i, j) and returns comparison value
                   If None, uses saaty_generator by default

    Returns:
        np.ndarray of shape (n, n) with:
        - Diagonal filled with 1.0
        - Upper triangle filled by generator when not missing
        - Lower triangle filled with reciprocal values (1/value)
        - Missing values as np.nan
    """
    matrix = np.ones((n, n), dtype=float)

    for i in range(n):
        for j in range(i + 1, n):
            if _rng.random() < missing_ratio:
                matrix[i, j] = np.nan
                matrix[j, i] = np.nan
            else:
                value = generator(i, j)
                matrix[i, j] = value
                matrix[j, i] = 1.0 / value if value != 0 else np.nan

    np.fill_diagonal(matrix, 1.0)

    return matrix
