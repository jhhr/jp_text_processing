from itertools import combinations
from typing import Sequence, TypeVar

T = TypeVar("T", bound=Sequence)


def get_ordered_sublists(list_to_split: T, split_count: int) -> list[list[T]]:
    """
    Splits a sequence into all possible combinations of N subsequences while preserving order.

    Args:
        list_to_split: The sequence to split (list, string, tuple, etc.)
        split_count: Number of subsequences to create (N)

    Returns:
        A list of all possible ways to split the input into N subsequences.
        Each way is represented as a list of N subsequences.

    Example:
        >>> get_ordered_sublists([1, 2, 3], 2)
        [[[1], [2, 3]], [[1, 2], [3]]]
        >>> get_ordered_sublists("abc", 2)
        [['a', 'bc'], ['ab', 'c']]
    """
    n = len(list_to_split)

    # Return nothing for invalid split counts
    if split_count <= 0 or split_count > n:
        return []

    if split_count == 1:
        return [[list_to_split]]

    if split_count == n:
        return [[list_to_split[i : i + 1] for i in range(n)]]

    results = []

    # Choose positions where to split (between elements)
    for split_positions in combinations(range(1, n), split_count - 1):
        # Convert split positions to actual subsequences
        sublists = []
        prev = 0

        for pos in split_positions:
            sublists.append(list_to_split[prev:pos])
            prev = pos

        # Add the last subsequence
        sublists.append(list_to_split[prev:])

        results.append(sublists)

    return results
