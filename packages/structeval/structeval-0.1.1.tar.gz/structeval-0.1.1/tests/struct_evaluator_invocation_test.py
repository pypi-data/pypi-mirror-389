from __future__ import annotations

import numpy as np

from structeval.compare.methods.scalar import (
    TypedEvaluator as ScalarTypedEvaluator,
)
from structeval.compare.methods.vector import (
    TypedEvaluator as VectorTypedEvaluator,
)
from structeval.models.eval_config import EvalConfig, EvaluationDefinition, EvaluationType
from structeval.models.evaluators import Evaluators
from structeval.struct_evaluator import StructEvaluator


class _RecordingScalar(ScalarTypedEvaluator):
    def __init__(self, vector_evaluator: VectorTypedEvaluator, score: float = 0.42):
        self.called: bool = False
        self.calls: list[tuple[object, object]] = []
        self.score = score
        self.vector_evaluator = vector_evaluator

    def __call__(self, value0, value1) -> float:  # type: ignore[override]
        self.called = True
        self.calls.append((value0, value1))
        return self.score

    def name(self) -> str:
        return "RecordingScalar"

    def as_vector_evaluator(self) -> VectorTypedEvaluator:
        return self.vector_evaluator


class _RecordingVector(VectorTypedEvaluator):
    def __init__(self, score: float = 0.7):
        self.called: bool = False
        self.calls: list[tuple[list[object], list[object]]] = []
        self.score = score

    def __call__(self, values0: list, values1: list) -> np.ndarray:  # type: ignore[override]
        self.called = True
        self.calls.append((values0, values1))
        return np.full((len(values0), len(values1)), self.score, dtype=float)

    def name(self) -> str:
        return "RecordingVector"


LEFT = {
    "name": "John",
    "age": 25,
    "is_student": True,
    "hobbies": [
        {"name": "reading", "is_physical": False},
        {"name": "swimming", "is_physical": True},
    ],
}

RIGHT = {
    "name": "Jane",
    "age": 26,
    "is_student": True,
    "hobbies": [
        {"name": "hiking", "is_physical": True},
        {"name": "running", "is_physical": True},
        {"name": "buildings", "is_physical": False},
    ],
}

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "enum": ["John", "Jane"]},
        "age": {"type": "integer"},
        "is_student": {"type": "boolean"},
        "hobbies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "is_physical": {"type": "boolean"}},
            },
        },
    },
}


def test_injected_evaluators_are_used() -> None:
    rec_vector = _RecordingVector(score=0.8)
    rec_scalar = _RecordingScalar(vector_evaluator=rec_vector, score=0.33)
    evaluators = Evaluators.default()
    evaluators.string_compare = rec_scalar
    evaluators.string_vector_evaluator = rec_vector

    _ = StructEvaluator.run(LEFT, RIGHT, evaluators=evaluators)

    assert rec_scalar.called, "Expected injected scalar string evaluator to be called"
    assert rec_vector.called, "Expected injected vector string evaluator to be called"


def test_configuration_invokes_binary_for_string() -> None:
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.BINARY), array_matching_threshold=0)
    result = StructEvaluator.run(LEFT, RIGHT, configuration=cfg)
    # Different names should be a binary mismatch
    name_nodes = [n for n in result.results if n.path == ("name",)]
    assert name_nodes and name_nodes[0].score == 0.0


def test_json_schema_enum_triggers_binary_override_path() -> None:
    # Note: with_field_overrides_from_json_schema is exercised inside run; this asserts no error and plausible output
    result = StructEvaluator.run(LEFT, RIGHT, json_schema=SCHEMA)
    assert 0.0 <= result.sum_metrics.precision <= 1.0


def test_all_parameters_invoke_expected_paths() -> None:
    rec_vector = _RecordingVector(score=0.75)
    rec_scalar = _RecordingScalar(vector_evaluator=rec_vector, score=0.25)
    evaluators = Evaluators.default()
    evaluators.string_compare = rec_scalar
    evaluators.string_vector_evaluator = rec_vector

    cfg = EvalConfig(
        integer_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.THRESHOLD, evaluation_params={"threshold": 10.0, "difference_penalty_weighting": 0.1}),
        array_matching_threshold=0,
    )

    _ = StructEvaluator.run(
        LEFT,
        RIGHT,
        evaluators=evaluators,
        configuration=cfg,
    )

    assert rec_scalar.called and rec_vector.called


def test_all_parameters_not_invoke_expected_paths_with_enum() -> None:
    rec_vector = _RecordingVector(score=0.75)
    rec_scalar = _RecordingScalar(vector_evaluator=rec_vector, score=0.25)
    evaluators = Evaluators.default()
    evaluators.string_compare = rec_scalar
    evaluators.string_vector_evaluator = rec_vector

    cfg = EvalConfig(
        integer_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.THRESHOLD, evaluation_params={"threshold": 10.0, "difference_penalty_weighting": 0.1}),
        array_matching_threshold=0,
    )

    _ = StructEvaluator.run(
        LEFT,
        RIGHT,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=SCHEMA,
    )

    assert not rec_scalar.called


def test_all_parameters_not_invoke_expected_paths_with_override() -> None:
    rec_vector = _RecordingVector(score=0.75)
    rec_scalar = _RecordingScalar(vector_evaluator=rec_vector, score=0.25)
    evaluators = Evaluators.default()
    evaluators.string_compare = rec_scalar

    cfg = EvalConfig(
        integer_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.THRESHOLD, evaluation_params={"threshold": 10.0, "difference_penalty_weighting": 0.1}),
        array_matching_threshold=0,
    )

    _ = StructEvaluator.run(
        LEFT,
        RIGHT,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=SCHEMA,
    )

    assert not rec_scalar.called
