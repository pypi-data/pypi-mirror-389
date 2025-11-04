def is_subset(subset: set, superset: set) -> bool:
    """Checks if 'subset' is a subset of 'superset'."""
    return all(elem in superset for elem in subset)


if __name__ == "__main__":
    # Example usage
    set_a = {1, 2}
    set_b = {1, 2, 3, 4}

    if is_subset(set_a, set_b):
        print(f"{set_a} is a subset of {set_b}")
    else:
        print(f"{set_a} is not a subset of {set_b}")
