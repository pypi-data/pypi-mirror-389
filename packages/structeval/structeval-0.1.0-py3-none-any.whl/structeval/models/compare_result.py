from collections import defaultdict
from typing import Any, TypeAliasType

from pydantic import BaseModel, Field, computed_field

from structeval.compare.types import Json, JsonPath, JsonPathWildCard, JsonScalar, keys_in_json
from structeval.models.sum_metrics import SumMetrics
from structeval.models.value_node import ArrayValueNode, ValueNode


class ComparedElement(BaseModel):
    test_value: JsonScalar
    ground_truth_value: JsonScalar
    score: float
    method: str
    target_index: int | None = Field(exclude=True, default=None)


class ComparedObject(BaseModel):
    properties: dict[str, "Output"]

    def find_target_index(self) -> int | None:
        for property in self.properties.values():
            if isinstance(property, ComparedElement):
                return property.target_index
            elif isinstance(property, ComparedObject):
                target_index = property.find_target_index()
                if target_index is not None:
                    return target_index
        return None

    @computed_field(return_type=SumMetrics)  # type: ignore[prop-decorator]
    def sum_metrics(self) -> SumMetrics:
        return _sum_metrics_from_output(self)


class ComparedArrayElement(BaseModel):
    current_index: int
    target_index: int | None
    values: "Output"


class MissingArrayElement(BaseModel):
    target_index: int
    value: Json


class ComparedArray(BaseModel):
    present_items: list[ComparedArrayElement]
    missing_items: list[MissingArrayElement]

    @computed_field(return_type=SumMetrics)  # type: ignore[prop-decorator]
    def sum_metrics(self) -> SumMetrics:
        return _sum_metrics_from_output(self)


class RunMetadata(BaseModel):
    array_matching_threshold: float
    error_message: str | None = None


def _lookup_via_json_path(value: Json, path: JsonPath) -> Json:
    for part in path:
        if isinstance(part, (int, str)):
            value = value[part]  # type: ignore[index]
        else:
            raise ValueError(f"Unsupported path element type: {type(part)}")
    return value


def _replace_indices(path: JsonPath, indexes: list[int]) -> JsonPath:
    """Replace all the * characters in the path with the corresponding index.
    They are * to allow for comparison with other indices, but we want the full path to the element.
    """
    out_: list[str | int | JsonPathWildCard] = []
    all_indexes = iter(indexes)
    for char_ in path:
        if char_ == JsonPathWildCard():
            out_.append(next(all_indexes))
        else:
            out_.append(char_)

    return tuple(out_)


# Named recursive type alias so Pydantic can resolve recursion
Output = TypeAliasType("Output", ComparedElement | ComparedArray | ComparedObject)


def _sum_metrics_from_output(output: Output) -> SumMetrics:
    if isinstance(output, ComparedElement):
        return SumMetrics(
            true_positives=output.score,
            positive_predictions=1 if output.test_value is not None or output.score != 0 else 0,
            ground_truth_predictions=1 if output.ground_truth_value is not None or output.score != 0 else 0,
        )
    elif isinstance(output, ComparedArray):
        present_item_metrics = [_sum_metrics_from_output(present_item.values) for present_item in output.present_items]
        empty_item_metrics = [
            SumMetrics(true_positives=0, ground_truth_predictions=keys_in_json(missing_item.value), positive_predictions=0) for missing_item in output.missing_items
        ]  # TODO; Fix
        return SumMetrics.merge(present_item_metrics + empty_item_metrics)
    elif isinstance(output, ComparedObject):
        return SumMetrics.merge([_sum_metrics_from_output(property) for property in output.properties.values()])
    else:
        raise ValueError(f"Unsupported output type: {type(output)}")


class CompareResult(BaseModel):
    results: list[ValueNode | ArrayValueNode] = Field(exclude=True)
    ground_truth_value: Json = Field(exclude=True)
    test_value: Json = Field(exclude=True)
    run_metadata: RunMetadata

    def model_post_init(self, __context: Any) -> None:
        self._scalar_results = [r for r in self.results if isinstance(r, ValueNode)]
        self._array_results = [r for r in self.results if isinstance(r, ArrayValueNode)]

    @computed_field(return_type=SumMetrics)  # type: ignore[prop-decorator]
    def sum_metrics(self) -> SumMetrics:
        return _sum_metrics_from_output(self.output)

    def _get_missing_array_elements(self) -> dict[JsonPath, list[MissingArrayElement]]:
        missing_elements = defaultdict[JsonPath, list[MissingArrayElement]](list)
        for a in self._array_results:
            if a.index_0 is None:
                assert a.index_1 is not None, "Internal data integrity error"
                fq_path = _replace_indices(a.path, a.parent_indexes_1)
                value = _lookup_via_json_path(self.ground_truth_value, (*fq_path, a.index_1))
                missing_elements[fq_path].append(MissingArrayElement(target_index=a.index_1, value=value))
        return missing_elements

    def _missing_scalar_elements(self) -> dict[JsonPath, ComparedElement]:
        missing_elements = dict[JsonPath, ComparedElement]()
        for v in self._scalar_results:
            if v.value0 is None and v.value1 is not None:
                missing_elements[v.path] = ComparedElement(test_value=v.value0, ground_truth_value=v.value1, score=0, method=v.method)
        return missing_elements

    @computed_field(return_type=Output)  # type: ignore[prop-decorator]
    def output(self) -> ComparedObject:
        value_nodes_dict = {v.path: v for v in self._scalar_results}

        array_value_nodes_dict = {_replace_indices(v.path, [*a.parent_indexes_0, a.index_0]): (v, a.index_1) for a in self._array_results for v in a.values}
        missing_elements_dict = self._get_missing_array_elements()

        def traverse_value_with_path(value: Json, path: JsonPath) -> Output | None:
            if isinstance(value, dict):
                _properties = {k: traverse_value_with_path(v, (*path, k)) for k, v in value.items()}
                return ComparedObject(properties={k: v for k, v in _properties.items() if v is not None})
            elif isinstance(value, list):
                array_result = [traverse_value_with_path(v, (*path, i)) for i, v in enumerate(value)]
                array_result = [v for v in array_result if v is not None]
                array_elements = []
                # Here we collect indexes for all end node scalar types, and raise them to the level of the array element itself
                # Nested naked arrays will not work. They are tricky with the current implementation, we don't know which index corresponds to which array
                for i, element in enumerate(array_result):
                    target_index_found = None
                    if isinstance(element, ComparedElement):
                        target_index_found = element.target_index
                    elif isinstance(element, ComparedObject):
                        target_index_found = element.find_target_index()
                    array_elements.append(ComparedArrayElement(current_index=i, target_index=target_index_found, values=element))

                return ComparedArray(present_items=array_elements, missing_items=missing_elements_dict.get(path, []))
            else:
                value_node = value_nodes_dict.get(path)
                array_node_and_target_index = array_value_nodes_dict.get(path)
                if value_node is not None:
                    return ComparedElement(
                        test_value=value_node.value0,
                        ground_truth_value=value_node.value1,
                        score=value_node.score,
                        method=value_node.method,
                        target_index=None,
                    )
                elif array_node_and_target_index is not None:
                    array_node, target_index = array_node_and_target_index
                    return ComparedElement(
                        test_value=array_node.value0,
                        ground_truth_value=array_node.value1,
                        score=array_node.score,
                        method=array_node.method,
                        target_index=target_index,
                    )
                else:
                    # This is a fallback that should only be encountered when value is a particular unstructured json
                    # It probably has to be adversarially structured to trigger this fallback
                    return None

        matched_result = traverse_value_with_path(value=self.test_value, path=())
        if not isinstance(matched_result, ComparedObject):
            matched_result = ComparedObject(properties={"$": matched_result})

        missing_scalar_elements = self._missing_scalar_elements()
        for path, element in missing_scalar_elements.items():
            matched_result.properties[".".join(["$", *list(path)])] = element

        return matched_result
