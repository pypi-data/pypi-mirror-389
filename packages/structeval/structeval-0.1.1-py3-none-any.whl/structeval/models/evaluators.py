from dataclasses import dataclass, field

from structeval.compare.methods.scalar import (
    BinaryTypedEvaluator,
    ComposedTypedEvaluator,
    JaccardTypedEvaluator,
    ThresholdTypedEvaluator,
    TypedEvaluator,
    from_eval_definition,
)
from structeval.compare.types import JsonPath, JsonPathWildCard
from structeval.models.eval_config import EvalConfig
from structeval.models.field_overrides import FieldOverride
from structeval.models.json_schema import CustomJsonSchema


@dataclass
class FieldEvaluatorOverride:
    path: JsonPath
    evaluator: TypedEvaluator


@dataclass
class Evaluators:
    boolean_compare: TypedEvaluator
    number_compare: TypedEvaluator
    string_compare: TypedEvaluator
    field_evaluator_overrides: list[FieldEvaluatorOverride] = field(default_factory=list)

    def with_config_evaluators(self, config: EvalConfig) -> "Evaluators":
        if config.string_evaluation_type is not None:
            self.string_compare = from_eval_definition(config.string_evaluation_type)
        if config.boolean_evaluation_type is not None:
            self.boolean_compare = from_eval_definition(config.boolean_evaluation_type)
        if config.number_evaluation_type is not None:
            self.number_compare = from_eval_definition(config.number_evaluation_type)
        return self

    def with_field_overrides(self, field_overrides: list[FieldOverride]) -> "Evaluators":
        for field_override in field_overrides:
            if JsonPathWildCard() in field_override.path:
                self.field_evaluator_overrides.append(
                    FieldEvaluatorOverride(
                        path=field_override.path,
                        evaluator=from_eval_definition(field_override.evaluator),
                    )
                )
            else:
                self.field_evaluator_overrides.append(
                    FieldEvaluatorOverride(
                        path=field_override.path,
                        evaluator=from_eval_definition(field_override.evaluator),
                    )
                )
        return self

    def with_field_overrides_from_json_schema(self, schema: CustomJsonSchema) -> "Evaluators":
        return self.with_field_overrides(schema.to_field_overrides())

    @staticmethod
    def default() -> "Evaluators":
        return Evaluators(
            boolean_compare=BinaryTypedEvaluator(),
            number_compare=ThresholdTypedEvaluator(threshold=0.001, difference_penalty_weighting=0.1),
            string_compare=ComposedTypedEvaluator(vector_evaluator=JaccardTypedEvaluator()),
            field_evaluator_overrides=[],
        )
