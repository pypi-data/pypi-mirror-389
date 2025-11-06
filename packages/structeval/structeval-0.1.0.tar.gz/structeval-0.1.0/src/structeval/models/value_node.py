from pydantic import BaseModel, Field

from structeval.compare.types import JsonPath, JsonScalar


class ArrayValueNode(BaseModel):
    """
    An ArrayValueNode represents a single array value in the comparison.

    This could be a product type (json object, arbitrarily nested).
    Note that nested arrays are not supported.
    """

    parent_indexes_0: list[int] = []
    parent_indexes_1: list[int] = []
    index_0: int | None
    index_1: int | None
    path: JsonPath = Field(description="The path to this array value in the comparison.")
    values: list["ValueNode"] = Field(
        default_factory=list,
        description="The scalar values for each scalar element in this position (can be arbitrarily nested objects)",
    )


class ValueNode(BaseModel):
    """
    A ValueNode represents a single scalar value in the comparison.
    """

    path: JsonPath
    method: str
    value0: JsonScalar
    value1: JsonScalar
    score: float
