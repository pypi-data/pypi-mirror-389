from typing import TYPE_CHECKING

import numpy as np

from .typed_evaluator import TypedEvaluator

if TYPE_CHECKING:
    from structeval.compare.methods.scalar import TypedEvaluator as ScalarTypedEvaluator


class ComposedTypedEvaluator(TypedEvaluator):
    def __init__(self, scalar_evaluator: "ScalarTypedEvaluator"):
        self.scalar_evaluator = scalar_evaluator

    def __call__(self, values0: list, values1: list) -> np.ndarray:
        output_matrix = np.zeros((len(values0), len(values1)))
        for index_0, value0 in enumerate(values0):
            for index_1, value1 in enumerate(values1):
                output_matrix[index_0, index_1] = self.scalar_evaluator(value0, value1)
        return output_matrix

    def name(self) -> str:
        return f"{self.scalar_evaluator.name()}_v"
