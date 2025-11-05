"""Core driver program of moodsmith"""

import random
from typing import Literal, Optional
from .locales import (MOTIVATIONAL_TEMPLATES,FUNNY_TEMPLATE, NEGATIVE_MOTIVATIONAL,
                      POSITIVE_TEMPLATES)

Intensity = Literal["soft", "medium", "hard"]


def _bangs(intensity: int) -> str:
    """
    Converts intensity 0-5 to punctuation, if 0 then "."

    Args:
        intensity: how many "!"s will be added or "."
    """

    intensity = max(0, min(intensity, 5))
    return "!" * intensity if intensity else "."


def positive(
    language: str = "en",
    name: Optional[str] = None,
    enthusiasm: int = 2,
    seed: Optional[int] = None,
) -> str:
    """
    Return a short positive message.

    Args:
        language: e.g en, es, fr : defaults to english if empty
        name: Optional person to address.
        enthusiasm: 0-5, number of exclamation points (0 -> '.').
        seed: If provided, makes the random
            choice deterministic (useful for tests).
    """

    # use seed as the same number as running as in test to remove randomness
    # and you will always get the same output for e.g seed 123
    rnd = random.Random(seed)
    templates = POSITIVE_TEMPLATES.get(language, POSITIVE_TEMPLATES["en"])
    punct = _bangs(enthusiasm)
    base = rnd.choice(templates).format(punct=punct)
    prefix = f"{name}, " if name else ""
    return prefix + base


def funny(
    language: str = "en",
    name: Optional[str] = None,
    enthusiasm: int = 2,
    seed: Optional[int] = None,
) -> str:
    """
    Return a short positive message.

    Args:
        language: e.g en, es, fr : defaults to english if empty
        name: Optional person to address.
        enthusiasm: 0-5, number of exclamation points (0 -> '.').
        seed: If provided, makes the random
            choice deterministic (useful for tests).
    """

    # use seed as the same number as running as in test to remove randomness
    # and you will always get the same output for e.g seed 123
    rnd = random.Random(seed)
    templates = FUNNY_TEMPLATE.get(language, FUNNY_TEMPLATE["en"])
    punct = _bangs(enthusiasm)
    base = rnd.choice(templates).format(punct=punct)
    prefix = f"{name}, " if name else ""
    return prefix + base


def motivational(
    language: str = "en",
    intensity: Intensity = "medium",
    name: Optional[str] = None,
    seed: Optional[int] = None,
) -> str:
    """
    Return a short motivational sentence (pyjokes style: one line).
    Args:
        language: language key; falls back to 'en' if not found.
        intensity: 'soft' | 'medium' | 'hard' (affects tone/力度).
        name: Optional person to address (prefix).
        seed: deterministic selection if provided.
    """
    rnd = random.Random(seed)
    lang_table = (
        MOTIVATIONAL_TEMPLATES.get(language) or MOTIVATIONAL_TEMPLATES["en"]
    )
    pool = lang_table.get(intensity) or lang_table["medium"]
    msg = rnd.choice(pool)
    prefix = f"{name}, " if name else ""
    return prefix + msg


def negative(
    language: str = "en",
    name: Optional[str] = None,
    enthusiasm: int = 2,
    intensity: Intensity = "medium",
    seed: Optional[int] = None
) -> str:
    '''
    Return a short negative message to movitate the user

    Args:
        language: Language of message
        name: Optional name of person to address message to
        enthusiasm: number of explanation points (max 5)
        intensity: How mean/motivaitonal the message is
        seed: Seed for random functions (for testing purposes)
    '''

    rnd = random.Random(seed)
    lang_table = (
        NEGATIVE_MOTIVATIONAL.get(language, NEGATIVE_MOTIVATIONAL["en"])
    )
    pool = lang_table.get(intensity, lang_table.get("medium"))
    punct = _bangs(enthusiasm)
    msg = rnd.choice(pool).format(punct=punct)
    if name:
        return name + ", " + msg
    msg = msg[0].upper() + msg[1:]
    return msg
