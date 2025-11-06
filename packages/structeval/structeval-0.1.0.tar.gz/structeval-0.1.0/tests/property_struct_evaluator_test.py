from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from structeval.struct_evaluator import StructEvaluator

# Shape algebra: 'null'|'bool'|'int'|'float'|'str'|{'object': {k: shape}}|{'array': shape}
scalar_shapes = st.sampled_from(["null", "bool", "int", "float", "str"])


@st.composite
def shape_strategy(draw, max_depth: int = 3, possible_types: tuple[str, ...] = ("scalar", "object")):
    """We generate a json shape, but one that avoids naked arrays.
    Particularly when these are nested, they are tricky to evaluate for invariants like precision and recall swapping.
    """
    if max_depth <= 0:
        return draw(scalar_shapes)
    kind = draw(st.sampled_from(possible_types))
    if kind == "scalar":
        return draw(scalar_shapes)
    if kind == "object":
        keys = draw(st.lists(st.text(min_size=1, max_size=8), min_size=0, max_size=3, unique=True))
        props = {}
        for k in keys:
            props[k] = draw(shape_strategy(max_depth=max_depth - 1, possible_types=("scalar", "object", "array")))
        return {"object": props}
    # array
    return {"array": draw(shape_strategy(max_depth=max_depth - 1, possible_types=("scalar", "object")))}


def value_strategy_from_shape(shape):
    response = st.none()
    if shape == "null":
        response = st.none()
    if shape == "bool":
        response = st.booleans()
    if shape == "int":
        response = st.integers(min_value=-1_000, max_value=1_000)
    if shape == "float":
        response = st.floats(allow_nan=False, allow_infinity=False, width=32)
    if shape == "str":
        response = st.text(max_size=20)
    if isinstance(shape, dict) and "object" in shape:
        props = shape["object"]
        response = st.fixed_dictionaries({k: value_strategy_from_shape(v) for k, v in props.items()})
    if isinstance(shape, dict) and "array" in shape:
        inner = value_strategy_from_shape(shape["array"])
        response = st.lists(inner, max_size=4)
    # fallback shouldn't happen
    return response


@st.composite
def same_shape_json_pair(draw):
    shp = draw(shape_strategy())
    strat = value_strategy_from_shape(shp)
    a = draw(strat)
    b = draw(strat)
    return a, b


# Build a bounded JSON strategy (Json = scalar | list[Json] | dict[str, Json])
json_scalar = st.one_of(
    st.booleans(),
    st.integers(min_value=-1_000, max_value=1_000),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=20),
    st.none(),
)

json_strategy = st.recursive(
    base=json_scalar,
    extend=lambda inner: st.one_of(
        st.lists(inner, max_size=4),
        st.dictionaries(st.text(max_size=10), inner, max_size=4),
    ),
    max_leaves=30,
)


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(a=json_strategy, b=json_strategy)
def test_run_invariants(a, b) -> None:
    # Should not crash for any Json inputs
    res = StructEvaluator.run(a, b)

    # Metrics should always be in [0, 1]
    assert 0.0 <= res.sum_metrics.precision <= 1.0
    assert 0.0 <= res.sum_metrics.recall <= 1.0
    assert 0.0 <= res.sum_metrics.f_score() <= 1.0


@settings(deadline=None)
@given(x=json_strategy)
def test_identical_inputs_are_perfect(x) -> None:
    res = StructEvaluator.run(x, x)
    assert res.sum_metrics.precision == pytest.approx(1.0)
    assert res.sum_metrics.recall == pytest.approx(1.0)
    assert res.sum_metrics.f_score() == pytest.approx(1.0)


@settings(deadline=None)
@given(same_shape_json_pair())
def test_swap_inputs_swaps_precision_and_recall_with_same_structure(pair) -> None:
    a, b = pair
    res_ab = StructEvaluator.run(a, b)
    res_ba = StructEvaluator.run(b, a)

    # Swapping inputs should swap precision and recall; warn if discrepancies
    assert res_ab.sum_metrics.precision == pytest.approx(res_ba.sum_metrics.recall)
    assert res_ab.sum_metrics.recall == pytest.approx(res_ba.sum_metrics.precision)


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(same_shape_json_pair())
def test_run_invariants_same_shape(pair) -> None:
    a, b = pair
    res = StructEvaluator.run(a, b)
    assert 0.0 <= res.sum_metrics.precision <= 1.0
    assert 0.0 <= res.sum_metrics.recall <= 1.0
    assert 0.0 <= res.sum_metrics.f_score() <= 1.0
