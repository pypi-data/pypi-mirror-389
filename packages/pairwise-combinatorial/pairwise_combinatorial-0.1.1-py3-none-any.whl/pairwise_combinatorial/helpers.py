import numpy as np

def is_connected(A: np.ndarray) -> bool:
    n = A.shape[0]
    visited = set()

    def dfs(i):
        for j in range(n):
            if i != j and not np.isnan(A[i, j]):  # є ребро i→j
                if j not in visited:
                    visited.add(j)
                    dfs(j)
            if i != j and not np.isnan(A[j, i]):  # або j→i (ігноруємо напрям)
                if j not in visited:
                    visited.add(j)
                    dfs(j)

    visited.add(0)
    dfs(0)

    return len(visited) == n

def is_full(A: np.ndarray) -> bool:
    """
    Check if the comparison matrix is full (no missing values)
    """
    return not np.isnan(A).any()


def calculate_consistency_ratio(A: np.ndarray, w: np.ndarray) -> float:
    """
    Calculate the Consistency Ratio (CR) for a pairwise comparison matrix.

    The CR measures how consistent the pairwise comparisons are with the
    derived weight vector. Lower CR values indicate better consistency.

    Saaty's guideline: CR < 0.10 is acceptable

    Formula:
    1. Compute λ_max (maximum eigenvalue)
    2. CI = (λ_max - n) / (n - 1)  (Consistency Index)
    3. CR = CI / RI  (Consistency Ratio)

    where RI is the Random Index (depends on n)

    Args:
        A: Pairwise comparison matrix (n x n), may contain NaN
        w: Priority weight vector (n,)

    Returns:
        Consistency Ratio (CR)
    """
    n = A.shape[0]

    if n < 2:
        return 0.0

    # Random Index values (Saaty, 1980)
    # RI[n] is the average CI of randomly generated matrices of size n
    RI = {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
        11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
    }

    if n not in RI:
        # For larger matrices, use approximation
        RI[n] = 1.98 * (n - 2) / n

    # Compute λ_max using only available (non-NaN) comparisons
    # Method: λ_max ≈ average of (Aw)_i / w_i for all i

    lambda_max_estimates = []

    for i in range(n):
        # Compute (Aw)_i using only non-NaN values
        weighted_sum = 0.0
        count = 0

        for j in range(n):
            if not np.isnan(A[i, j]):
                weighted_sum += A[i, j] * w[j]
                count += 1

        if count > 0 and w[i] > 0:
            lambda_max_estimates.append(weighted_sum / w[i])

    if not lambda_max_estimates:
        return 0.0

    lambda_max = np.mean(lambda_max_estimates)

    # Calculate Consistency Index
    CI = (lambda_max - n) / (n - 1)

    # Calculate Consistency Ratio
    if RI[n] == 0:
        return 0.0

    CR = CI / RI[n]

    return CR
