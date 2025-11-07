"""Core array/list utility functions."""

import random
from typing import Any, Callable, Iterable, List


def flatten(nested_list: List[Any]) -> List[Any]:
    """Flatten a nested list."""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk(items: List[Any], size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [items[i : i + size] for i in range(0, len(items), size)]


def deduplicate(items: List[Any]) -> List[Any]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def rotate(items: List[Any], n: int) -> List[Any]:
    """Rotate list by n positions."""
    if not items:
        return items
    n = n % len(items)
    return items[n:] + items[:n]


def shuffle(items: List[Any], seed: int = None) -> List[Any]:
    """Shuffle list (returns new list)."""
    result = items.copy()
    if seed is not None:
        random.seed(seed)
    random.shuffle(result)
    return result


def group_by(items: List[Any], key: Callable[[Any], Any]) -> dict:
    """Group items by key function."""
    result = {}
    for item in items:
        k = key(item)
        if k not in result:
            result[k] = []
        result[k].append(item)
    return result


def batch(items: Iterable[Any], size: int) -> Iterable[List[Any]]:
    """Batch iterator into chunks."""
    batch_list = []
    for item in items:
        batch_list.append(item)
        if len(batch_list) >= size:
            yield batch_list
            batch_list = []
    if batch_list:
        yield batch_list

