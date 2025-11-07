"""Tests for pyarraytools core functions."""

from pyarraytools import (
    flatten,
    chunk,
    deduplicate,
    rotate,
    shuffle,
    group_by,
    batch,
)


def test_flatten():
    assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    assert flatten([1, [2, [3]]]) == [1, 2, 3]


def test_chunk():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_deduplicate():
    assert deduplicate([1, 2, 2, 3]) == [1, 2, 3]


def test_rotate():
    assert rotate([1, 2, 3, 4], 1) == [2, 3, 4, 1]


def test_group_by():
    items = [{"x": 1}, {"x": 1}, {"x": 2}]
    result = group_by(items, lambda i: i["x"])
    assert len(result[1]) == 2
    assert len(result[2]) == 1


def test_batch():
    batches = list(batch([1, 2, 3, 4, 5], 2))
    assert batches == [[1, 2], [3, 4], [5]]

