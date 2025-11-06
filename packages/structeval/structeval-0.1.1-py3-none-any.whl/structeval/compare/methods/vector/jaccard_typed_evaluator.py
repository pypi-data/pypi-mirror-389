from __future__ import annotations

from collections.abc import Iterable
from typing import Callable

import numpy as np

from structeval.compare.methods.helpers.jaccard import jaccard_similarity_sets
from structeval.compare.methods.vector.typed_evaluator import TypedEvaluator


def _default_tokenizer(text: str) -> frozenset[str]:
    return frozenset(t for t in text.lower().split() if t)


class JaccardTypedEvaluator(TypedEvaluator):
    def __init__(self, tokenizer: Callable[[str], Iterable[str]] | None = None):
        self._tokenize = tokenizer if tokenizer is not None else _default_tokenizer

    def __call__(self, values0: list, values1: list) -> np.ndarray:
        sets0 = [frozenset(self._tokenize(s)) for s in values0]
        sets1 = [frozenset(self._tokenize(s)) for s in values1]
        return jaccard_similarity_sets(sets0, sets1)

    def name(self) -> str:
        return "Jaccard"
