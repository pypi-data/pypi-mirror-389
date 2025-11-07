"""Tests for pystatkit core functions."""

from pystatkit import mean, median, std_dev, variance


def test_mean():
    assert mean([1, 2, 3, 4, 5]) == 3.0


def test_median():
    assert median([1, 2, 3, 4, 5]) == 3.0
