from structeval.compare.methods.vector import CosineTypedEvaluator, JaccardTypedEvaluator
from structeval.models.eval_config import EvaluationDefinition, EvaluationType

from .binary_typed_evalutor import BinaryTypedEvaluator
from .composed_type_evaluator import ComposedTypedEvaluator
from .threshold_type_evaluator import ThresholdTypedEvaluator
from .typed_evaluator import TypedEvaluator


def from_eval_definition(definition: EvaluationDefinition) -> TypedEvaluator:
    if definition.evaluation_type == EvaluationType.JACCARD:
        return ComposedTypedEvaluator(vector_evaluator=JaccardTypedEvaluator())
    elif definition.evaluation_type == EvaluationType.COSINE:
        embedding_model = definition.evaluation_params.get("embedding_model")
        if embedding_model is None:
            raise ValueError("Cosine evaluation type requires evaluation parameters: {embedding_model: str}")
        return ComposedTypedEvaluator(vector_evaluator=CosineTypedEvaluator.from_model_name(embedding_model))
    elif definition.evaluation_type == EvaluationType.BINARY:
        return BinaryTypedEvaluator()
    elif definition.evaluation_type == EvaluationType.THRESHOLD:
        if definition.evaluation_params is None:
            raise ValueError("Threshold evaluation type requires evaluation parameters: {threshold: float, difference_penalty_weighting: float}")
        return ThresholdTypedEvaluator(**definition.evaluation_params)


__all__ = [
    "BinaryTypedEvaluator",
    "ComposedTypedEvaluator",
    "ThresholdTypedEvaluator",
    "TypedEvaluator",
    "from_eval_definition",
]
