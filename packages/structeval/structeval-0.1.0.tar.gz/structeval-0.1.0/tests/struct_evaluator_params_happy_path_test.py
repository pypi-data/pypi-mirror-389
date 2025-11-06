from __future__ import annotations

import os

import pytest

from structeval.compare.methods.scalar import BinaryTypedEvaluator
from structeval.models.eval_config import EvalConfig, EvaluationDefinition, EvaluationType
from structeval.models.evaluators import Evaluators
from structeval.models.field_overrides import FieldOverride
from structeval.struct_evaluator import StructEvaluator

LEFT = {"name": "John", "age": 25, "is_student": True}
RIGHT = {"name": "Jane", "age": 26, "is_student": True}


def test_run_with_custom_evaluators() -> None:
    evaluators = Evaluators.default()
    evaluators.string_compare = BinaryTypedEvaluator()

    result = StructEvaluator.run(LEFT, RIGHT, evaluators=evaluators)

    assert 0.0 <= result.sum_metrics.precision <= 1.0
    # Name differs; with binary string compare it should be 0
    name_nodes = [n for n in result.results if n.path == ("name",)]
    assert name_nodes and name_nodes[0].score == 0.0


def test_run_with_custom_overrides() -> None:
    evaluators = Evaluators.default()
    evaluators = evaluators.with_field_overrides([FieldOverride(path=("name",), evaluator=EvaluationDefinition(evaluation_type=EvaluationType.BINARY))])

    result = StructEvaluator.run(LEFT, RIGHT, evaluators=evaluators)

    assert 0.0 <= result.sum_metrics.precision <= 1.0
    # Name differs; with binary string compare it should be 0
    name_nodes = {n.method for n in result.results if n.path == ("name",)}
    assert name_nodes == {"Binary"}


def test_run_with_configuration() -> None:
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.BINARY), array_matching_threshold=0)
    result = StructEvaluator.run(LEFT, RIGHT, configuration=cfg)
    assert 0.0 <= result.sum_metrics.precision <= 1.0
    name_nodes = [n for n in result.results if n.path == ("name",)]
    assert name_nodes and name_nodes[0].score == 0.0


def test_run_with_json_schema() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "enum": ["John", "Jane"]}, "age": {"type": "integer"}, "is_student": {"type": "boolean"}},
    }
    result = StructEvaluator.run(LEFT, RIGHT, json_schema=schema)
    # Even if overrides do not change behavior, call should succeed
    assert 0.0 <= result.sum_metrics.precision <= 1.0


def test_run_with_json_schema_enum() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "enum": ["John", "Jane"]}, "age": {"type": "integer"}, "is_student": {"type": "boolean"}},
    }
    result = StructEvaluator.run(LEFT, RIGHT, json_schema=schema)
    # Even if overrides do not change behavior, call should succeed

    assert 0.0 <= result.sum_metrics.precision <= 1.0


def test_run_with_all_parameters() -> None:
    evaluators = Evaluators.default()
    evaluators.string_compare = BinaryTypedEvaluator()
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.BINARY), array_matching_threshold=0)
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "enum": ["John", "Jane"]}, "age": {"type": "integer"}, "is_student": {"type": "boolean"}},
    }
    result = StructEvaluator.run(
        LEFT,
        RIGHT,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=schema,
    )
    assert 0.0 <= result.sum_metrics.precision <= 1.0


@pytest.mark.skipif(not os.path.exists("RUN_EMBEDDING_TESTS"), reason="Embedding tests are disabled")
def test_run_with_all_parameters_embedding_model() -> None:
    evaluators = Evaluators.default()
    evaluators.string_compare = BinaryTypedEvaluator()
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.COSINE, evaluation_params={"embedding_model": "all-MiniLM-L6-v2"}))
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "enum": ["John", "Jane"]}, "age": {"type": "integer"}, "is_student": {"type": "boolean"}},
    }
    result = StructEvaluator.run(
        LEFT,
        RIGHT,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=schema,
    )
    assert 0.0 <= result.sum_metrics.precision <= 1.0


def test_run_with_parameters_array_matching_threshold() -> None:
    left = {"name": "John", "age": 25, "is_student": True, "arr": [{"x": "foo", "y": "baz"}, {"x": "bar", "y": "qux"}]}
    right = {"name": "Jane", "age": 26, "is_student": True, "arr": [{"x": "foo", "y": "bar"}, {"x": "bar", "y": "qux"}]}
    evaluators = Evaluators.default()
    evaluators.string_compare = BinaryTypedEvaluator()
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.BINARY), array_matching_threshold=0.5)
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["John", "Jane"]},
            "age": {"type": "integer"},
            "is_student": {"type": "boolean"},
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"x": {"type": "string"}, "y": {"type": "string"}},
                },
            },
        },
    }
    result = StructEvaluator.run(
        left,
        right,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=schema,
    )
    output_arr = result.output.properties["arr"]
    assert len(output_arr.present_items) == 2
    assert len(output_arr.missing_items) == 1


def test_run_with_parameters_array_no_matching_threshold() -> None:
    left = {"name": "John", "age": 25, "is_student": True, "arr": [{"x": "foo", "y": "baz"}, {"x": "bar", "y": "qux"}]}
    right = {"name": "Jane", "age": 26, "is_student": True, "arr": [{"x": "foo", "y": "bar"}, {"x": "bar", "y": "qux"}]}
    evaluators = Evaluators.default()
    evaluators.string_compare = BinaryTypedEvaluator()
    cfg = EvalConfig(string_evaluation_type=EvaluationDefinition(evaluation_type=EvaluationType.BINARY), array_matching_threshold=0)
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["John", "Jane"]},
            "age": {"type": "integer"},
            "is_student": {"type": "boolean"},
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"x": {"type": "string"}, "y": {"type": "string"}},
                },
            },
        },
    }
    result = StructEvaluator.run(
        left,
        right,
        evaluators=evaluators,
        configuration=cfg,
        json_schema=schema,
    )
    output_arr = result.output.properties["arr"]
    assert len(output_arr.present_items) == 2
    assert len(output_arr.missing_items) == 0
