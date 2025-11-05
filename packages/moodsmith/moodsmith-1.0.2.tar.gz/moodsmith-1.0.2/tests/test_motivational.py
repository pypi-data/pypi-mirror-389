"""Tests for the motivational() function."""

from moodsmith import motivational


def test_seed_is_deterministic():
    '''Identical seed should return same quote'''
    a = motivational(intensity="medium", seed=123)
    b = motivational(intensity="medium", seed=123)
    assert a == b


def test_intensity_fallbacks():
    '''Test that unknown intensity falls back to medium'''
    x = motivational(intensity="medium", seed=1)
    y = motivational(intensity="unknown", seed=1)
    assert x == y


def test_name_prefix():
    '''Test that name, if provided, is at start of message'''
    s = motivational(name="Eason", seed=5)
    assert s.startswith("Eason, ")
