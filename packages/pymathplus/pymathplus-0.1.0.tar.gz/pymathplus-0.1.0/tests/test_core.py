"""Tests for pymathplus core functions."""

from pymathplus import factorial, is_prime, matrix_multiply


def test_factorial():
    assert factorial(5) == 120


def test_is_prime():
    assert is_prime(7) is True
    assert is_prime(8) is False
