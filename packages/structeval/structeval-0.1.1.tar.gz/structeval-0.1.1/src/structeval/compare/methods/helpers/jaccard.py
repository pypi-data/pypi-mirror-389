from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from typing import Any

import numpy as np


def jaccard_similarity_sets(sets0: Sequence[AbstractSet[Any]], sets1: Sequence[AbstractSet[Any]]) -> np.ndarray:
    n0, n1 = len(sets0), len(sets1)
    out = np.zeros((n0, n1), dtype=float)
    for i, s0 in enumerate(sets0):
        for j, s1 in enumerate(sets1):
            if not s0 and not s1:
                out[i, j] = 1.0
            else:
                inter = len(s0 & s1)
                union = len(s0 | s1)
                out[i, j] = inter / union if union else 0.0
    return out
