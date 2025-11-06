from typing import TYPE_CHECKING

from structeval.compare.types import JsonScalar

from .typed_evaluator import TypedEvaluator

if TYPE_CHECKING:
    from structeval.compare.methods.vector import TypedEvaluator as VectorTypedEvaluator


class ComposedTypedEvaluator(TypedEvaluator):
    def __init__(self, vector_evaluator: "VectorTypedEvaluator"):
        self._vector_evaluator = vector_evaluator
        self.is_from_vector = True

    def __call__(self, values0: JsonScalar, values1: JsonScalar) -> float:
        return float(self._vector_evaluator(values0=[values0], values1=[values1])[0][0])

    def name(self) -> str:
        return f"{self._vector_evaluator.name()}_s"

    def as_vector_evaluator(self) -> "VectorTypedEvaluator":
        return self._vector_evaluator
