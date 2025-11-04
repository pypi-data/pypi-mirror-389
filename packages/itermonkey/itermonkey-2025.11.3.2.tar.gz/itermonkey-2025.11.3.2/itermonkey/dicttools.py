"""Submodule for dictionary manipulation utilities."""

def dict_invert(d: dict) -> dict:
    """Inverts a dictionary, swapping keys and values.
    If multiple keys have the same value, the inverted dictionary will map that value to a list of keys."""
    inverted = {}
    for key, value in d.items():
        if value in inverted:
            if isinstance(inverted[value], list):
                inverted[value].append(key)
            else:
                inverted[value] = [inverted[value], key]
        else:
            inverted[value] = key
    return inverted

def flatten_dict(d: dict[tuple, any]) -> dict:
    """Flattens a dictionary with tuple keys into a single-level dictionary."""
    return {k: v for keys, v in d.items() for k in keys}

def dict_intersection(dict1: dict, dict2: dict) -> dict:
    """Returns a dictionary containing only the key-value pairs that are present in both input dictionaries."""
    return {k: dict1[k] for k in dict1 if k in dict2 and dict1[k] == dict2[k]}


if __name__ == "__main__":
    sample_dict = {'a': 1, 'b': 2, 'c': 1}
    print("Original dictionary:", sample_dict)
    print("Inverted dictionary:", dict_invert(sample_dict))

    tuple_key_dict = {('x', 'y'): 10, ('z',): 20}
    print("Flattened dictionary:", flatten_dict(tuple_key_dict))

    dict_a = {'a': 1, 'b': 2, 'c': 3}
    dict_b = {'b': 2, 'c': 4, 'd': 5}
    print("Dictionary intersection:", dict_intersection(dict_a, dict_b))