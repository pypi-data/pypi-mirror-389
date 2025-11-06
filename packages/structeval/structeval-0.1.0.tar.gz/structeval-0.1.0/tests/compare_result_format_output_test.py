from __future__ import annotations

from structeval.compare.types import JsonPathWildCard
from structeval.models.compare_result import ComparedArray, ComparedArrayElement, ComparedElement, ComparedObject, CompareResult, MissingArrayElement, RunMetadata
from structeval.models.value_node import ArrayValueNode, ValueNode


def test_json_comparison_output_structure_single_assert() -> None:
    test_json = {"a": 1, "b": {"c": True}, "arr": [{"x": "foo"}]}
    gt_json = {"a": 1, "b": {"c": True}, "arr": [{"x": "foo"}, {"x": "bar"}]}

    nodes = [
        ValueNode(path=("a",), method="Binary", value0=1, value1=1, score=1.0),
        ValueNode(path=("b", "c"), method="Binary", value0=True, value1=True, score=1.0),
        ArrayValueNode(
            index_0=0,
            index_1=0,
            path=("arr",),
            values=[ValueNode(path=("arr", JsonPathWildCard(), "x"), method="Binary", value0="foo", value1="foo", score=1.0)],
        ),
        ArrayValueNode(
            index_0=None,
            index_1=1,
            path=("arr",),
            values=[ValueNode(path=("arr", JsonPathWildCard(), "x"), method="Binary", value0="bar", value1="bar", score=1.0)],
        ),
    ]
    compare_result = CompareResult(results=nodes, ground_truth_value=gt_json, test_value=test_json, run_metadata=RunMetadata(array_matching_threshold=0.3))

    expected = ComparedObject(
        properties={
            "a": ComparedElement(test_value=1, ground_truth_value=1, score=1.0, method="Binary", target_index=None),
            "b": ComparedObject(properties={"c": ComparedElement(test_value=True, ground_truth_value=True, score=1.0, method="Binary", target_index=None)}),
            "arr": ComparedArray(
                present_items=[
                    ComparedArrayElement(
                        current_index=0,
                        target_index=0,
                        values=ComparedObject(properties={"x": ComparedElement(test_value="foo", ground_truth_value="foo", score=1.0, method="Binary", target_index=0)}),
                    )
                ],
                missing_items=[MissingArrayElement(target_index=1, value={"x": "bar"})],
            ),
        }
    )
    assert compare_result.output == expected
