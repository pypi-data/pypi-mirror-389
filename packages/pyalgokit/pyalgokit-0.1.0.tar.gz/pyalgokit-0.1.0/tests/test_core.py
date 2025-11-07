"""Tests for pyalgokit core functions."""

from pyalgokit import sort


def test_sort():
    assert sort([3, 1, 2]) == [1, 2, 3]
