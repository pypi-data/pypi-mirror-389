from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from structeval.compare.types import JsonScalar

if TYPE_CHECKING:
    from structeval.compare.methods.vector import TypedEvaluator as VectorTypedEvaluator


class TypedEvaluator(ABC):
    @abstractmethod
    def __call__(self, value0: JsonScalar, value1: JsonScalar) -> float:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def as_vector_evaluator(self) -> "VectorTypedEvaluator":
        pass
