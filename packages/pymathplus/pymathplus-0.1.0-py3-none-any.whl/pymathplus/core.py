"""Core math functions."""

import math


def factorial(n: int) -> int:
    """Calculate factorial."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    return math.factorial(n)


def is_prime(n: int) -> bool:
    """Check if number is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


def matrix_multiply(a: list, b: list) -> list:
    """Multiply two matrices."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    if cols_a != rows_b:
        raise ValueError("Cannot multiply matrices")
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result
