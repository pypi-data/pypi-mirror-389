"""Core algorithm functions."""

from typing import Any, Callable, List


def sort(arr: List[Any], key: Callable = None) -> List[Any]:
    """Sort array."""
    return sorted(arr, key=key)


def graph_algorithms():
    """Graph algorithm utilities."""
    return {"dfs": "depth-first search", "bfs": "breadth-first search"}


def dp():
    """Dynamic programming utilities."""
    return {"fibonacci": "fibonacci sequence"}
