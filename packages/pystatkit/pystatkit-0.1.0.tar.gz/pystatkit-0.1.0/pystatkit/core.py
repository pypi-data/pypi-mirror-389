"""Core statistics functions."""

from typing import List


def mean(values: List[float]) -> float:
    """Calculate mean."""
    return sum(values) / len(values) if values else 0


def median(values: List[float]) -> float:
    """Calculate median."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
    return sorted_vals[n//2]


def std_dev(values: List[float]) -> float:
    """Calculate standard deviation."""
    if not values:
        return 0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return variance ** 0.5


def variance(values: List[float]) -> float:
    """Calculate variance."""
    if not values:
        return 0
    m = mean(values)
    return sum((x - m) ** 2 for x in values) / len(values)
