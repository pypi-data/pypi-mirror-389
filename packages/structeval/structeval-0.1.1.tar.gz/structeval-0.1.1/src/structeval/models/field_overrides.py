from pydantic import BaseModel

from structeval.compare.types import JsonPath
from structeval.models.eval_config import EvaluationDefinition


class FieldOverride(BaseModel):
    path: JsonPath
    evaluator: EvaluationDefinition
