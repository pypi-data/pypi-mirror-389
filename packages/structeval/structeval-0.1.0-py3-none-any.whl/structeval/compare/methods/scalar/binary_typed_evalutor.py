from typing import TYPE_CHECKING

from structeval.compare.methods.vector import ComposedTypedEvaluator

from .typed_evaluator import TypedEvaluator

if TYPE_CHECKING:
    from structeval.compare.methods.vector import TypedEvaluator as VectorTypedEvaluator


class BinaryTypedEvaluator(TypedEvaluator):
    def __call__(self, value0: bool | int | float | str, value1: bool | int | float | str) -> float:
        return 1.0 if value0 == value1 else 0.0

    def name(self) -> str:
        return "Binary"

    def as_vector_evaluator(self) -> "VectorTypedEvaluator":
        return ComposedTypedEvaluator(scalar_evaluator=self)
