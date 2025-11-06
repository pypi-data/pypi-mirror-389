from typing import TYPE_CHECKING

from structeval.compare.methods.vector import ComposedTypedEvaluator
from structeval.compare.types import JsonScalar

from .typed_evaluator import TypedEvaluator

if TYPE_CHECKING:
    from structeval.compare.methods.vector import TypedEvaluator as VectorTypedEvaluator


class ThresholdTypedEvaluator(TypedEvaluator):
    def __init__(self, threshold: float, difference_penalty_weighting: float = 1):
        """
        Evaluator for threshold-based evaluation.
        Args:
            threshold: The threshold value to use for evaluation.
            difference_penalty_weighting: The weighting to apply as a penalty when approaching the threshold (exponential --
             0 is no penalty, 1 is linear, 2 is quadratic, etc.)
        """
        assert threshold > 0, "Threshold must be greater than 0"
        assert difference_penalty_weighting >= 0, "Difference penalty weight must be greater than 0"
        self.threshold = threshold
        self.penalty_weighting = difference_penalty_weighting

    def name(self) -> str:
        return f"Threshold_{self.threshold:.2f}_{self.penalty_weighting:.2f}"

    def __call__(self, value0: JsonScalar, value1: JsonScalar) -> float:
        delta = abs(float(value0) - float(value1))
        if delta > self.threshold:
            return 0
        elif self.penalty_weighting == 0:
            return 1.0
        else:
            percentage_to_threshold = delta / self.threshold
            return 1.0 - percentage_to_threshold ** (1 / self.penalty_weighting)

    def as_vector_evaluator(self) -> "VectorTypedEvaluator":
        return ComposedTypedEvaluator(scalar_evaluator=self)
