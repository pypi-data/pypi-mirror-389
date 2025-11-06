from dataclasses import dataclass
from enum import Enum

import numpy as np
from pydantic import BaseModel

from structeval.array_helpers import find_optimal_pairing, get_flattened_json_path_dict
from structeval.compare.methods.scalar import TypedEvaluator
from structeval.compare.methods.vector import JaccardTypedEvaluator
from structeval.compare.types import Json, JsonPath
from structeval.models.compare_result import CompareResult, RunMetadata
from structeval.models.eval_config import EvalConfig
from structeval.models.evaluators import Evaluators
from structeval.models.json_schema import CustomJsonSchema
from structeval.models.value_node import ArrayValueNode, ValueNode


class NonScalarEvaluable(Enum):
    Object = "object"
    Array = "array"
    BothEmpty = "both_empty"
    OneEmpty = "one_empty"
    TypeMismatch = "type_mismatch"


EvalStep = NonScalarEvaluable | TypedEvaluator


def _get_eval_step_name(eval_step: EvalStep) -> str:
    return eval_step.name() if isinstance(eval_step, TypedEvaluator) else eval_step.value


@dataclass
class VectorResult:
    method_name: str
    weight_matrix: np.ndarray


@dataclass
class VectorResults:
    evaluated: dict[JsonPath, VectorResult]
    nested_list_keys: set[str]


class StructEvaluator:
    DEFAULT_ARRAY_MATCHING_THRESHOLD: float = 0.3

    # When we have untyped json in arrays, we still attempt evaluate it by coercing to strings and using this evaluator
    FALLBACK_VECTOR_EVALUATOR = JaccardTypedEvaluator()

    def __init__(self, evaluators: Evaluators, array_matching_threshold: float):
        self.evaluators = evaluators
        self.array_matching_threshold = array_matching_threshold

    def _find_next_eval_step_by_type(self, type_: type) -> EvalStep:
        if type_ is type(None):
            return NonScalarEvaluable.OneEmpty
        elif type_ is dict:
            return NonScalarEvaluable.Object
        elif type_ is list:
            return NonScalarEvaluable.Array
        elif type_ is bool:
            return self.evaluators.boolean_compare
        elif type_ in (int, float):
            return self.evaluators.number_compare
        elif type_ is str:
            return self.evaluators.string_compare
        else:
            raise ValueError(f"Unsupported type: {type_}")

    def _find_next_eval_step(self, type0: type, type1: type, path: JsonPath) -> EvalStep:
        field_override = next((override for override in self.evaluators.field_evaluator_overrides if override.path == path), None)
        if type0 is type(None) and type1 is type(None):
            return NonScalarEvaluable.BothEmpty
        elif field_override is not None:
            return field_override.evaluator
        else:
            eval_step_0 = self._find_next_eval_step_by_type(type0)
            eval_step_1 = self._find_next_eval_step_by_type(type1)
            if _get_eval_step_name(eval_step_0) != _get_eval_step_name(eval_step_1):
                return NonScalarEvaluable.TypeMismatch
            else:
                return eval_step_0

    def _find_next_eval_step_from_type_set(self, type_set_0: set[type], type_set_1: set[type], path: JsonPath) -> EvalStep:
        """Find a valid eval step from the set of types. If no valid eval step is found, return None."""
        if len(type_set_0) == 0 and len(type_set_1) == 0:
            return NonScalarEvaluable.BothEmpty
        elif len(type_set_0) == 0 or len(type_set_1) == 0:
            return NonScalarEvaluable.OneEmpty

        eval_step = None
        for type0 in type_set_0:
            for type1 in type_set_1:
                new_eval_step = self._find_next_eval_step(type0, type1, path)
                if eval_step is not None and _get_eval_step_name(new_eval_step) != _get_eval_step_name(eval_step):
                    return NonScalarEvaluable.TypeMismatch
                eval_step = new_eval_step
        return eval_step

    def _evaluate_within_array_get_vector_results(self, key_dict0: dict, key_dict1: dict, start_path: str) -> VectorResults:
        vector_results: dict[str, VectorResult] = {}
        nested_list_keys = set()
        for key in set(key_dict0.keys()) | set(key_dict1.keys()):
            value0 = key_dict0.get(key, [])
            value1 = key_dict1.get(key, [])
            eval_step = self._find_next_eval_step_from_type_set({type(v) for v in value0}, {type(v) for v in value1}, (*start_path, key))
            if eval_step == NonScalarEvaluable.TypeMismatch:
                # This is a fallback for doing some kind of evaluation when we have some polymorphic lists
                key_dict0[key] = [str(v) for v in value0]
                key_dict1[key] = [str(v) for v in value1]
                vector_results[key] = VectorResult(
                    method_name=f"Fallback_{self.FALLBACK_VECTOR_EVALUATOR.name()}",
                    weight_matrix=self.FALLBACK_VECTOR_EVALUATOR([str(v) for v in value0], [str(v) for v in value1]),
                )
            elif isinstance(eval_step, TypedEvaluator):
                vector_evaluator = eval_step.as_vector_evaluator()
                vector_results[key] = VectorResult(method_name=eval_step.name(), weight_matrix=vector_evaluator(value0, value1))
            elif eval_step == NonScalarEvaluable.Array:
                nested_list_keys |= {key}
            elif eval_step == NonScalarEvaluable.BothEmpty:
                key_dict0[key] = [str(v) for v in value0]
                key_dict1[key] = [str(v) for v in value1]
                vector_results[key] = VectorResult(method_name="BothEmpty", weight_matrix=np.full((len(value0), len(value1)), 1.0, dtype=float))
            elif eval_step == NonScalarEvaluable.OneEmpty:
                key_dict0[key] = [str(v) for v in value0]
                key_dict1[key] = [str(v) for v in value1]
                vector_results[key] = VectorResult(method_name="OneEmpty", weight_matrix=np.full((len(value0), len(value1)), 0.0, dtype=float))
            else:
                raise AssertionError(f"Impossible eval step -- objects, type mismatches should be removed/flattened out by now: {eval_step}")

        return VectorResults(evaluated=vector_results, nested_list_keys=nested_list_keys)

    def _evaluate_within_array(
        self, array0: list[Json], array1: list[Json], start_path: JsonPath, parent_indexes_0: list[int], parent_indexes_1: list[int]
    ) -> list[ArrayValueNode]:
        # Flatten the arrays into a dictionary of paths and values
        key_dict0 = get_flattened_json_path_dict(array0)
        key_dict1 = get_flattened_json_path_dict(array1)

        # Evaluate the results for everything except for array-nested elements
        vector_results = self._evaluate_within_array_get_vector_results(key_dict0, key_dict1, start_path)

        # Find the optimal pairing of elements across the arrays
        optimal_pairing = find_optimal_pairing(
            weight_matrices=[vector_result.weight_matrix for vector_result in vector_results.evaluated.values()],
            threshold=self.array_matching_threshold,
        )

        # Consturct the array nodes from the optimal pairing
        array_nodes = []
        for r, c in zip(optimal_pairing.row_idx, optimal_pairing.col_idx):
            value_nodes = []
            for key, vector_result in vector_results.evaluated.items():
                values0 = key_dict0.get(key) or []
                values1 = key_dict1.get(key) or []
                value0 = values0[r] if len(values0) > r else None
                value1 = values1[c] if len(values1) > c else None
                score = vector_result.weight_matrix[r, c] if vector_result.weight_matrix.shape[0] > r and vector_result.weight_matrix.shape[1] > c else 0.0
                value_nodes.append(ValueNode(path=start_path + key, method=vector_result.method_name, value0=value0, value1=value1, score=score))
            array_nodes.append(ArrayValueNode(index_0=r, index_1=c, path=start_path, values=value_nodes, parent_indexes_0=parent_indexes_0, parent_indexes_1=parent_indexes_1))
            for key in vector_results.nested_list_keys:
                values0 = key_dict0.get(key) or []
                values1 = key_dict1.get(key) or []
                value0 = values0[r] if len(values0) > r else None
                value1 = values1[c] if len(values1) > c else None
                nested_array_nodes = self._evaluate_within_array(
                    array0=value0, array1=value1, start_path=start_path + key, parent_indexes_0=[*parent_indexes_0, r], parent_indexes_1=[*parent_indexes_1, c]
                )
                array_nodes.extend(nested_array_nodes)

        # Construct the array nodes for the elements that were not paired
        for r in range(optimal_pairing.accumulated_cost_matrix.shape[0]):
            if r not in optimal_pairing.row_idx:
                value_nodes = [
                    ValueNode(
                        path=start_path + key,
                        method=vector_result.method_name,
                        value0=key_dict0[key][r] if len(key_dict0[key]) > r else None,
                        value1=None,
                        score=0,
                    )
                    for key, vector_result in vector_results.evaluated.items()
                    if key in key_dict0
                ]
                array_nodes.append(
                    ArrayValueNode(
                        index_0=r,
                        index_1=None,
                        path=start_path,
                        values=value_nodes,
                        parent_indexes_0=parent_indexes_0,
                        parent_indexes_1=parent_indexes_1,
                    )
                )
        # Construct the array nodes for the elements that were not paired
        for c in range(optimal_pairing.accumulated_cost_matrix.shape[1]):
            if c not in optimal_pairing.col_idx:
                value_nodes = [
                    ValueNode(
                        path=start_path + key,
                        method=vector_result.method_name,
                        value1=key_dict1[key][c] if len(key_dict1[key]) > c else None,
                        score=0,
                        value0=None,
                    )
                    for key, vector_result in vector_results.evaluated.items()
                    if key in key_dict1
                ]
                array_nodes.append(
                    ArrayValueNode(
                        index_1=c,
                        index_0=None,
                        path=start_path,
                        values=value_nodes,
                        parent_indexes_0=parent_indexes_0,
                        parent_indexes_1=parent_indexes_1,
                    )
                )

        return array_nodes

    def _evaluate(self, test_value: Json, ground_truth_value: Json, path: JsonPath) -> list[ValueNode | ArrayValueNode]:
        result = self._find_next_eval_step(type(test_value), type(ground_truth_value), path)
        if result == NonScalarEvaluable.Object:
            assert isinstance(test_value, dict) and isinstance(ground_truth_value, dict), "Internal data integrity error"
            all_keys = set(test_value.keys()) | set(ground_truth_value.keys())
            value_nodes = []
            for key in all_keys:
                value_nodes.extend(self._evaluate(test_value.get(key), ground_truth_value.get(key), (*path, key)))
            return value_nodes
        elif result == NonScalarEvaluable.Array:
            return self._evaluate_within_array(array0=test_value, array1=ground_truth_value, start_path=path, parent_indexes_0=[], parent_indexes_1=[])
        elif result == NonScalarEvaluable.BothEmpty:
            return [ValueNode(path=path, value0=None, value1=None, method="BothEmpty", score=1.0)]
        elif result == NonScalarEvaluable.OneEmpty:
            return [ValueNode(path=path, value0=None, value1=None, method="OneEmpty", score=0.0)]
        elif result == NonScalarEvaluable.TypeMismatch:
            return [ValueNode(path=path, value0=str(test_value), value1=str(ground_truth_value), method="TypeMismatch", score=0.0)]
        elif isinstance(result, TypedEvaluator):
            return [ValueNode(path=path, value0=test_value, value1=ground_truth_value, method=result.name(), score=result(test_value, ground_truth_value))]
        else:
            raise ValueError(f"Unsupported result type: {type(result)}")

    def __call__(self, test_value: Json, ground_truth_value: Json) -> CompareResult:
        value_nodes = self._evaluate(test_value, ground_truth_value, ())
        return CompareResult(
            results=value_nodes, ground_truth_value=ground_truth_value, test_value=test_value, run_metadata=RunMetadata(array_matching_threshold=self.array_matching_threshold)
        )

    @staticmethod
    def run(
        test_value: Json,
        ground_truth_value: Json,
        evaluators: Evaluators | None = None,
        json_schema: Json | None = None,
        configuration: EvalConfig | str | None = None,
    ) -> CompareResult:
        """
        Run the evaluator on the test and ground truth values.
        Args:
            test_value: The test value to compare. Must be a JsonScalar, list, or dict.
            ground_truth_value: The ground truth value to compare. Must be a JsonScalar, list, or dict.
            evaluators: Evaluators that defines how to parse and evaluate the values, which will default.
            json_schema: The json schema that can be used to improve the evaluation by looking up field types, which are
             not discernible via reflection on the object (e.g. enums), and applying any custom overrides specified in
             "x-override-evaluator".
            configuration: The configuration to use that can override the default evaluators.

        Order of precedence for determining which evaluation rules to apply is:
        1. per-field overrides specified in "x-override-evaluator" in the json_schema
        2. per-field overrides specified in the evaluators
        3. type-specific rules applied by deafault in the json schema (e.g.. enums are binary classification by default)
        4. configuration-specified evaluation rules by type
        5. evaluators-specified evaluation rules by type

        Raises:
            ValidationError: If the test or ground truth value is not valid according to the json schema.
        """
        if evaluators is None:
            evaluators = Evaluators.default()
        if configuration is not None:
            if isinstance(configuration, str):
                configuration = EvalConfig.from_file(configuration)
            evaluators = evaluators.with_config_evaluators(configuration)
        if json_schema is not None:
            json_schema_model = CustomJsonSchema.model_validate(json_schema)
            evaluators = evaluators.with_field_overrides_from_json_schema(json_schema_model)
            test_value = json_schema_model.filter_to_json_schema(test_value)
            ground_truth_value = json_schema_model.filter_to_json_schema(ground_truth_value)
        array_matching_threshold = configuration.array_matching_threshold if configuration is not None else StructEvaluator.DEFAULT_ARRAY_MATCHING_THRESHOLD
        evaluator = StructEvaluator(evaluators, array_matching_threshold=array_matching_threshold)
        return evaluator(test_value, ground_truth_value)

    @staticmethod
    def run_typed(
        test_value: BaseModel,
        ground_truth_value: BaseModel,
        evaluators: Evaluators | None = None,
        configuration: EvalConfig | str | None = None,
    ) -> CompareResult:
        return StructEvaluator.run(
            test_value=test_value.model_dump(),
            ground_truth_value=ground_truth_value.model_dump(),
            json_schema=test_value.model_json_schema(),
            evaluators=evaluators,
            configuration=configuration,
        )
