from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass
class OptimalPairing:
    accumulated_cost_matrix: np.ndarray
    row_idx: list[int]
    col_idx: list[int]


def _safely_stack_2d_arrays(matrices: list[np.ndarray]) -> np.ndarray:
    """
    Safely stacks 2D arrays of different shapes into a single 3D array.
    """
    padded_matrices = []
    max_X, max_Y = max(matrix.shape[0] for matrix in matrices), max(matrix.shape[1] for matrix in matrices)
    for matrix in matrices:
        X, Y = matrix.shape
        if matrix.shape[0] == max_X and matrix.shape[1] == max_Y:
            padded_matrices.append(matrix)
        else:
            # This condition is needed for untyped json in arrays, which results in matrics with different shapes
            # Json paths are discrepant across the two inputs.
            # Padding with zeroes allows us to treat these missing paths as misses
            if matrix.shape[0] < max_X:
                out_matrix = np.concatenate([matrix, np.full((max_X - X, Y), 0.0)], axis=0)
            if matrix.shape[1] < max_Y:
                out_matrix = np.concatenate([matrix, np.full((X, max_Y - Y), 0.0)], axis=1)
            padded_matrices.append(out_matrix)
    return np.stack(padded_matrices, axis=0)


def find_optimal_pairing(weight_matrices: list[np.ndarray], threshold: float) -> OptimalPairing:
    if len(weight_matrices) == 0:
        return OptimalPairing(accumulated_cost_matrix=np.array([[]]), row_idx=[], col_idx=[])

    stacked_weight_matrices = _safely_stack_2d_arrays(weight_matrices)

    accumulated_matrix = np.mean(stacked_weight_matrices, axis=0)
    accumulated_cost_matrix = 1 - accumulated_matrix

    row_idx, col_idx = linear_sum_assignment(accumulated_cost_matrix)

    filtered_row_idx = []
    filtered_col_idx = []
    for r, c in zip(row_idx, col_idx):
        if accumulated_matrix[r, c] > threshold:
            filtered_row_idx.append(r)
            filtered_col_idx.append(c)

    return OptimalPairing(accumulated_cost_matrix=accumulated_cost_matrix, row_idx=filtered_row_idx, col_idx=filtered_col_idx)
