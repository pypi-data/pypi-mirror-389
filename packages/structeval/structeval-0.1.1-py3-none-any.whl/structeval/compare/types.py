from typing import TypeAliasType

from pydantic import BaseModel

JsonScalar = bool | int | str | float | None


class JsonPathWildCard(BaseModel):
    class Config:
        frozen = True


# Named recursive type alias to avoid implicit recursion issues with Pydantic
Json = TypeAliasType("Json", JsonScalar | list["Json"] | dict[str, "Json"])

JsonPath = tuple[str | int | JsonPathWildCard, ...]


def keys_in_json(json: Json) -> int:
    if isinstance(json, dict):
        return sum(keys_in_json(v) for v in json.values())
    elif isinstance(json, list):
        return sum(keys_in_json(v) for v in json)
    else:
        return 1
