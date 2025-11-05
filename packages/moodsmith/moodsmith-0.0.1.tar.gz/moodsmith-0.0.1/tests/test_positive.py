"""Tests for the positive_quote() function."""

import re

from moodsmith import positive


def _count_trailing_bangs(s: str) -> int:
    """Return the number of '!' at the end of a string."""
    m = re.search(r"!+$", s)
    return len(m.group(0)) if m else 0


def test_seed_is_deterministic():
    """Same seed -> same output."""
    a = positive(language="en", seed=42)
    b = positive(language="en", seed=42)
    assert a == b


def test_incorrect_language():
    """Unknown language should fall back to English and respect enthusiasm."""
    msg = positive(language="xx", enthusiasm=3, seed=7)
    assert _count_trailing_bangs(msg) == 3
    english_snippets = ["Steve Jobs", "You are", "you are", "Love the"]
    assert any(snippet in msg for snippet in english_snippets)


def test_empty_language():
    """No language argument should default to English."""
    msg = positive(enthusiasm=4, seed=7)
    assert _count_trailing_bangs(msg) == 4
    english_snippets = ["Steve Jobs", "You are", "you are", "Love the"]
    assert any(snippet in msg for snippet in english_snippets)


def test_same_seed_different_language():
    """Same seed across different languages should produce different text."""
    a = positive(language="es", seed=42)
    b = positive(language="fr", seed=42)
    assert a != b


def test_enthusiasm_zero_ends_with_fullstop():
    """Enthusiasm 0 should end with '.'."""
    msg = positive(language="en", enthusiasm=0, seed=3)
    assert msg.endswith(".")
