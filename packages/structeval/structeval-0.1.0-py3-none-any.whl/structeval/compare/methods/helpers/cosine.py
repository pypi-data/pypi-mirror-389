import numpy as np


def cosine_similarity(matrix0: np.ndarray, matrix1: np.ndarray) -> np.ndarray:
    a = np.asarray(matrix0, dtype=float)
    b = np.asarray(matrix1, dtype=float)
    if a.ndim != 2 or b.ndim != 2:
        raise ValueError("cosine_similarity expects 2D arrays")
    if a.shape[1] != b.shape[1]:
        raise ValueError("Input arrays must have the same number of features (columns)")
    eps = 1e-12
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + eps)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + eps)
    return a_norm @ b_norm.T
