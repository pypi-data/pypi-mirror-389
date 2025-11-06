from structeval.compare.types import Json, JsonPath, JsonPathWildCard, JsonScalar


def get_flattened_json_path_dict(
    json_list: list[Json],
) -> dict[JsonPath, list[JsonScalar | list[Json]]]:
    """
    Returns a flattened dictionary of JSON paths and their associated values.
    Nested lists are returned as is, to be re-processed recursively.
    Flattening is helpful for comparing arrays, given that we are optimizing the pairing of elements across the arrays.
    """

    def _flatten_dict(obj: Json, path: str = (JsonPathWildCard(),)) -> dict[JsonPath, JsonScalar | list[Json]]:
        result: dict[JsonPath, JsonScalar] = {}

        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = (*path, key)
                result.update(_flatten_dict(value, new_path))
        elif isinstance(obj, list):
            result[path] = obj
        elif isinstance(obj, JsonScalar):
            # Base case: primitive value
            result[path] = obj
        else:
            raise ValueError(f"Unsupported type: {type(obj)}")
        return result

    items: list[dict[JsonPath, JsonScalar]] = []
    all_keys: set[str] = set()
    for element in json_list:
        result = _flatten_dict(element)
        items.append(result)
        all_keys |= set(result.keys())

    output = {}
    for key in all_keys:
        output[key] = [result.get(key) for result in items]

    return output
