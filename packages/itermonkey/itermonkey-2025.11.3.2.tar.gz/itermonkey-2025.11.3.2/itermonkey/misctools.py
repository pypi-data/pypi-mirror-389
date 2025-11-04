from typing import Iterable
import json

def fancy_print(data: dict | list | set, indent: int = 4, color: str = "\033[97m") -> None:
    """Prints data structures in a formatted and colored way. A color name or ANSI code can be provided."""
    COLOR = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "black": "\033[90m",
        "\033[91m": "\033[91m",
        "\033[92m": "\033[92m",
        "\033[93m": "\033[93m",
        "\033[94m": "\033[94m",
        "\033[95m": "\033[95m",
        "\033[96m": "\033[96m",
        "\033[97m": "\033[97m",
        "\033[90m": "\033[90m",
    }.get(color.lower(), "\033[97m")

    formatted_data = json.dumps(data, indent=indent)
    print(f"{COLOR}{formatted_data}\033[0m")

def is_monotypic(iter: Iterable):
    """Checks if all elements in an iterable are of the same type."""
    return True if len(iter) == 0 else (True if all([type(iter[0]) == type(i) for i in iter]) else False)

def keys_exist(data: dict | list, keys: list):
    """Returns true if every key in a nested dictionary/list exists, returns false if not."""
    for key in keys:
        try:
            data = data[key]
        except:
            return False
    return True

def tree_sum(data):
    """Recursively computes the sum of all numerical values in a nested list or dictionary."""
    if isinstance(data, (int, float)):
        return data
    elif isinstance(data, list):
        return sum(tree_sum(item) for item in data)
    elif isinstance(data, dict):
        return sum(tree_sum(value) for value in data.values())
    else:
        return 0

if __name__ == "__main__":
    # Example usage
    sample_dict = {"name": "Alice", "age": 30, "city": "New York"}
    fancy_print(sample_dict, color="cyan")

    sample_list = [1, 1, 1, 1]
    print("Is monotypic:", is_monotypic(sample_list))

    nested_dict = {"a": {"b": {"c": 42}}}
    print("Keys exist:", keys_exist(nested_dict, ["a", "b", "c"]))