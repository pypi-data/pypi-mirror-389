"""Tests for pynumtools core functions."""

from pynumtools import round_to, to_base, clamp


def test_round_to():
    assert round_to(3.14159, 2) == 3.14


def test_to_base():
    assert to_base(10, 2) == "1010"


def test_clamp():
    assert clamp(5, 1, 10) == 5
    assert clamp(15, 1, 10) == 10
