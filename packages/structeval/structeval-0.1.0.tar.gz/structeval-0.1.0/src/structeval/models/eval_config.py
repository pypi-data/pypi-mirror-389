from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class EvaluationType(Enum):
    JACCARD = "jaccard"
    COSINE = "cosine"
    BINARY = "binary"
    THRESHOLD = "threshold"


class EvaluationDefinition(BaseModel):
    evaluation_type: EvaluationType
    evaluation_params: Optional[dict[str, Any]] = None


class EvalConfig(BaseModel):
    string_evaluation_type: Optional[EvaluationDefinition] = None
    boolean_evaluation_type: Optional[EvaluationDefinition] = None
    number_evaluation_type: Optional[EvaluationDefinition] = None
    array_matching_threshold: Optional[float] = None

    # TODO: Implement validation
    def model_post_init(self, __context: Any) -> None:
        pass

    @staticmethod
    def from_file(file_path: str) -> "EvalConfig":
        with open(file_path) as f:
            return EvalConfig.model_validate_json(f.read())
