from __future__ import annotations

import pytest

from structeval.exceptions import ValidationError
from structeval.models.json_schema import CustomJsonSchema


def test_filter_object_ok() -> None:
    schema = CustomJsonSchema.model_validate(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "additionalProperties": False,
        }
    )
    data = {"name": "John", "age": 30}
    out = schema.filter_to_json_schema(data)
    assert out == data


def test_filter_object_additional_properties_false_raises() -> None:
    schema = CustomJsonSchema.model_validate(
        {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
    )
    with pytest.raises(ValidationError):
        schema.filter_to_json_schema({"name": "Jane", "extra": 1})


def test_filter_object_additional_properties_true_drops_unknown() -> None:
    schema = CustomJsonSchema.model_validate(
        {
            "type": "object",
            "properties": {"flag": {"type": "boolean"}},
            "additionalProperties": True,
        }
    )
    data = {"flag": True, "unknown": "keep?"}
    out = schema.filter_to_json_schema(data)
    # Unknown property should be ignored in the filtered output
    assert out == {"flag": True}


def test_filter_array_of_objects() -> None:
    schema = CustomJsonSchema.model_validate(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "additionalProperties": False,
            },
        }
    )
    data = [{"x": 1}, {"x": 2}]
    out = schema.filter_to_json_schema(data)
    assert out == data


def test_number_accepts_int_and_float() -> None:
    num_schema = CustomJsonSchema.model_validate({"type": "number"})
    assert num_schema.filter_to_json_schema(3.14) == 3.14
    assert num_schema.filter_to_json_schema(7) == 7
