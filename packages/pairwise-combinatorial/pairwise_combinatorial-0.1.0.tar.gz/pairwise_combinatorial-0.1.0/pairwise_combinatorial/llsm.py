import numpy as np
from numpy.linalg import lstsq

def llsm_incomplete(A: np.ndarray):
    n = A.shape[0]
    eqs = []
    vals = []

    # Беремо лише відомі елементи (не nan)
    for i in range(n):
        for j in range(n):
            if i != j and not np.isnan(A[i, j]):
                row = np.zeros(n)
                row[i] = 1
                row[j] = -1
                eqs.append(row)
                vals.append(np.log(A[i, j]))

    eqs = np.array(eqs)
    vals = np.array(vals)

    # язання методом найменших квадратів
    x, _, _, _ = np.linalg.lstsq(eqs, vals, rcond=None)

    # Обчислюємо ваги
    w = np.exp(x)
    w /= w.sum()  # нормалізація

    # Відновлюємо повну матрицю
    A_filled = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            A_filled[i, j] = w[i] / w[j]

    return w, A_filled
