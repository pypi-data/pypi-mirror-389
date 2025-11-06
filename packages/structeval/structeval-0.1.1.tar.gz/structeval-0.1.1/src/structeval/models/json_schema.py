from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from structeval.compare.types import Json, JsonPath, JsonPathWildCard
from structeval.exceptions import ValidationError
from structeval.models.eval_config import EvaluationDefinition, EvaluationType
from structeval.models.field_overrides import FieldOverride


class CustomJsonSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["string", "number", "integer", "boolean", "array", "object"]
    enum: Optional[list[str]] = None
    properties: Optional[dict[str, "CustomJsonSchema"]] = None
    items: Optional["CustomJsonSchema"] = None
    x_override_evaluator: Optional[EvaluationDefinition] = Field(default=None, alias="x-override-evaluator")
    additional_properties: Optional[bool] = Field(default=False, alias="additionalProperties")

    def to_field_overrides(self) -> list[FieldOverride]:
        field_overrides: list[FieldOverride] = []

        def _traverse(path: JsonPath, schema: "CustomJsonSchema") -> None:
            if schema.x_override_evaluator is not None:
                field_overrides.append(FieldOverride(path=path, evaluator=schema.x_override_evaluator))
            elif schema.enum is not None:
                field_overrides.append(FieldOverride(path=path, evaluator=EvaluationDefinition(evaluation_type=EvaluationType.BINARY)))

            if schema.properties is not None:
                for key, value in schema.properties.items():
                    _traverse((*path, key) if path else (key,), value)
            if schema.items is not None:
                _traverse((*path, JsonPathWildCard()) if path else (JsonPathWildCard(),), schema.items)

        _traverse((), self)
        return field_overrides

    def filter_to_json_schema(self, instance: Json) -> Json:
        def _traverse(schema: "CustomJsonSchema", el: Json, path: JsonPath) -> Json:
            if isinstance(el, dict) and schema.type == "object" and schema.properties is not None:
                result = {}
                for key, value in el.items():
                    if key in schema.properties:
                        result[key] = _traverse(schema.properties.get(key), value, (*path, key))
                    elif schema.additional_properties in (None, False):
                        raise ValidationError(f"Invalid path {path}.{key}: additional properties are not allowed here")
                return result
            elif isinstance(el, list) and schema.type == "array" and schema.items is not None:
                return [_traverse(schema.items, item, (*path, i)) for i, item in enumerate(el)]
            elif (
                (isinstance(el, str) and schema.type == "string")
                or (isinstance(el, int) and schema.type == "integer")
                or ((isinstance(el, (float, int))) and schema.type == "number")
                or (isinstance(el, bool) and schema.type == "boolean")
            ):
                return el
            else:
                raise ValidationError(f"invalid type for schema: {type(el)}: {el} at path {path}")

        return _traverse(self, instance, ())
