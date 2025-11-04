"""Submodule of itermonkey providing utilities pertaining to lists."""
from __future__ import annotations
from typing import Any
import datetime
import random

class SortedList:
    """A list that maintains its sorted order upon insertion of new elements. Key can be customized."""
    def __init__(self, listt: list=[], key=None):
        self._list = sorted(listt, key=key)
        self._key = key if key is not None else lambda x: x

    def insert(self, item: Any) -> None:
        """Insert an item into the sorted list, maintaining order."""
        key_item = self._key(item)
        low, high = 0, len(self._list)
        while low < high:
            mid = (low + high) // 2
            if self._key(self._list[mid]) < key_item:
                low = mid + 1
            else:
                high = mid
        self._list.insert(low, item)

    def sort(self) -> None:
        """Sort the list in place."""
        return "The list is already sorted, silly!"

    def __getitem__(self, index: int) -> Any:
        return self._list[index]
    
    def __len__(self) -> int:
        return len(self._list)
    
    def __iter__(self) -> iter:
        return iter(self._list)
    
    def __repr__(self) -> str:
        return f"SortedList({self._list})"
    
    def __add__(self, other: list | SortedList) -> SortedList:
        """Merge two sorted lists into a new SortedList."""
        if isinstance(other, list):
            other.sort(key=self._key)
            merged_list = merge(self._list, other, key=self._key)
            return SortedList(merged_list, key=self._key)
        elif isinstance(other, SortedList):
            merged_list = merge(self._list, other._list, key=self._key)
            return SortedList(merged_list, key=self._key)
        else:
            raise TypeError("Can only merge with list or SortedList")
        
    def __eq__(self, value) -> bool:
        if isinstance(value, SortedList):
            return self._list == value._list
        elif isinstance(value, list):
            return self._list == value
        else:
            return False
        
def _counting_sort_for_radix(lst: list, exp: int) -> list:
    """A helper function for radix sort that performs counting sort based on the digit represented by exp."""
    n = len(lst)
    output = [0] * n
    count = [0] * 10

    for i in range(n):
        index = (lst[i] // exp) % 10
        count[index] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    for i in range(n - 1, -1, -1):
        index = (lst[i] // exp) % 10
        output[count[index] - 1] = lst[i]
        count[index] -= 1

    return output
        
def bogo_sort(lst: list, key=lambda x: x) -> list: # O((n+1)!)
    """Sorts a list using the highly inefficient bogo sort algorithm."""

    while not is_sorted(lst, key):
        random.shuffle(lst)
    return lst

    here_is_some_unreachable_code_the_developer_thought_would_be_fun_for_any_curious_module_readers = "Eat your vegetables!"

def bubble_sort(lst: list, key=lambda x: x) -> list: # O(n^2)
    """Sorts a list using the bubble sort algorithm."""
    n = len(lst)
    for i in range(n):
        for j in range(0, n - i - 1):
            if key(lst[j]) > key(lst[j + 1]):
                lst[j], lst[j + 1] = lst[j + 1], lst[j]
    return lst

def cocktail_sort(lst: list, key=lambda x: x) -> list: # O(n^2)
    """Sorts a list using the cocktail sort algorithm."""
    n = len(lst)
    swapped = True
    start = 0
    end = n - 1

    while swapped:
        swapped = False

        for i in range(start, end):
            if key(lst[i]) > key(lst[i + 1]):
                lst[i], lst[i + 1] = lst[i + 1], lst[i]
                swapped = True

        if not swapped:
            break

        swapped = False
        end -= 1

        for i in range(end - 1, start - 1, -1):
            if key(lst[i]) > key(lst[i + 1]):
                lst[i], lst[i + 1] = lst[i + 1], lst[i]
                swapped = True

        start += 1

    return lst

def denest_list(iter: list[list]) -> list:
    """Flattens a nested list into a single list."""
    value = []
    for i in iter:
        if isinstance(i, list):
            value += denest_list(i)
        else:
            value += [i]

    return value

def find_index(lst: list, condition: function) -> int: # O(f(n))
    """Finds the index of the first element in a list that satisfies a given condition."""
    return next((i for i, x in enumerate(lst) if condition(x)), -1)

def gnome_sort(lst: list, key=lambda x: x) -> list: # O(n^2)
    """Sorts a list using the gnome sort algorithm."""
    index = 0
    n = len(lst)

    while index < n:
        if index == 0 or key(lst[index]) >= key(lst[index - 1]):
            index += 1
        else:
            lst[index], lst[index - 1] = lst[index - 1], lst[index]
            index -= 1

    return lst

def insertion_sort(lst: list, key=lambda x: x) -> list: # O(n^2)
    """Sorts a list using the insertion sort algorithm."""
    for i in range(1, len(lst)):
        key_item = lst[i]
        j = i - 1
        while j >= 0 and key(lst[j]) > key(key_item):
            lst[j + 1] = lst[j]
            j -= 1
        lst[j + 1] = key_item
    return lst

def is_sorted(lst: list, key=lambda x: x) -> bool:
    """Checks if a list is sorted according to the given key."""
    return all(key(lst[i]) <= key(lst[i + 1]) for i in range(len(lst) - 1))

def merge(left: list, right: list, key=lambda x: x) -> list: # O(n)
    """Merges two sorted lists into a single sorted list."""
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

def merge_sort(lst: list, key=lambda x: x) -> list: # O(n log n)
    """Sorts a list using the merge sort algorithm."""
    if len(lst) <= 1:
        return lst
    mid = len(lst) // 2
    left = merge_sort(lst[:mid], key)
    right = merge_sort(lst[mid:], key)
    return merge(left, right, key)

def pearson(f: list[int | float], g: list[int | float]) -> float:
    """Calculates the Pearson correlation coefficient between two lists of numbers."""
    assert (n := len(f)) == len(g)

    f_u = sum(f) / n
    g_u = sum(g) / n

    return sum([(f[k] - f_u)*(g[k] - g_u) for k in range(n)]) / (sum([(f[k] - f_u) ** 2 for k in range(n)]) ** 0.5 * sum([(g[k] - g_u) ** 2 for k in range(n)]) ** 0.5)


def pigeonhole_sort(lst: list) -> list: # O(n + k)
    """Sorts a list of integers using the pigeonhole sort algorithm."""
    if len(lst) == 0:
        return lst

    min_value = min(lst)
    max_value = max(lst)
    size = max_value - min_value + 1
    holes = [[] for _ in range(size)]

    for x in lst:
        holes[x - min_value].append(x)

    sorted_lst = []
    for hole in holes:
        sorted_lst.extend(hole)

    return sorted_lst

def product(lst1: list, lst2: list) -> list[tuple]:
    """Computes the Cartesian product of two lists."""
    return [(a, b) for a in lst1 for b in lst2]

def quick_sort(lst: list, key=lambda x: x) -> list: # O(n log n)
    """Sorts a list using the quick sort algorithm."""
    if len(lst) <= 1:
        return lst
    pivot = lst[len(lst) // 2]
    left = [x for x in lst if key(x) < key(pivot)]
    middle = [x for x in lst if key(x) == key(pivot)]
    right = [x for x in lst if key(x) > key(pivot)]
    return quick_sort(left, key) + middle + quick_sort(right, key)

def radix_sort(lst: list) -> list: # O(nk)
    """Sorts a list of non-negative integers using the radix sort algorithm."""
    if not lst:
        return lst

    max_num = max(lst)
    exp = 1
    while max_num // exp > 0:
        lst = _counting_sort_for_radix(lst, exp)
        exp *= 10
    return lst

def selection_sort(lst: list, key=lambda x: x) -> list: # O(n^2)
    """Sorts a list using the selection sort algorithm."""
    n = len(lst)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if key(lst[j]) < key(lst[min_idx]):
                min_idx = j
        lst[i], lst[min_idx] = lst[min_idx], lst[i]
    return lst

def shell_sort(lst: list, key=lambda x: x) -> list: # O(n log n) to O(n^(3/2))
    """Sorts a list using the shell sort algorithm."""
    n = len(lst)
    gap = n // 2

    while gap > 0:
        for i in range(gap, n):
            temp = lst[i]
            j = i
            while j >= gap and key(lst[j - gap]) > key(temp):
                lst[j] = lst[j - gap]
                j -= gap
            lst[j] = temp
        gap //= 2

    return lst

def sum_by_first_element(pairs: list[tuple[Any, int]]) -> list[tuple[Any, int]]:
    """Sums the second elements of tuples in a list grouped by their first elements."""
    result = {}
    for key, value in pairs:
        result[key] = result.get(key, 0) + value
    return list(result.items())

if __name__ == "__main__":
    TEST_LISTS = {
        "Already sorted": list(range(1000)),
        "Reverse sorted": list(range(1000, 0, -1)),
        "Random order": [random.randint(0, 1000) for _ in range(1000)],
        "All identical": [42] * 1000,
        "Empty list": [],
        "Single element": [7],
    }

    SORTING_ALGORITHMS = {
        "Bubble Sort": bubble_sort,
        "Cocktail Sort": cocktail_sort,
        "Gnome Sort": gnome_sort,
        "Insertion Sort": insertion_sort,
        "Merge Sort": merge_sort,
        "Pigeonhole Sort": pigeonhole_sort,
        "Quick Sort": quick_sort,
        "Radix Sort": radix_sort,
        "Selection Sort": selection_sort,
        "Shell Sort": shell_sort,
    }

    for name, alg in SORTING_ALGORITHMS.items():
        for test_name, test_list in TEST_LISTS.items():
            lst_copy = test_list.copy()

            start = datetime.datetime.now()
            assert is_sorted(alg(lst_copy)), f"{name} failed on {test_name}"
            end = datetime.datetime.now()
            duration = (end - start).total_seconds()
            print(f"{name} sorted {test_name} in {duration:.6f} seconds.")

    y_list = [1, 2, "3", "Chomsky", 4.0, 5, True, None, 6, "forthcoming"]

    print(find_index(y_list, lambda x: isinstance(x, int) and x > 4))  # Expected output: 5
    print(find_index(y_list, lambda x: isinstance(x, str) and x.startswith("C")))  # Expected output: 3
    print(find_index(y_list, lambda x: x is None))  # Expected output: 7
    print(find_index(y_list, lambda x: isinstance(x, float)))  # Expected output: 4

    f = [1,2,3,4,5]
    g = [2,4,6,8,10]
    print("Pearson correlation coefficient between f and g:", pearson(f, g))

    print(product([1, 2], ['a', 'b', 'c']))  # Expected output: [(1, 'a'), (1, 'b'), (1, 'c'), (2, 'a'), (2, 'b'), (2, 'c')]
    nested = [1, [2, [3, 4], 5], 6, [7, 8]]
    print("Denested list:", denest_list(nested))  # Expected output: [1, 2, 3, 4, 5, 6, 7, 8]