"""Test for negative motivational quotes"""

import re

import pytest

from moodsmith.core import negative
from moodsmith.locales import NEGATIVE_MOTIVATIONAL

SEEDS = [0, 23, 44, 9999, -1, -9999]


def _count_trailing_exclamations(msg: str) -> int:
    '''Return number of exclamations at the end of a string'''
    match = re.search(r'!+$', msg)
    return len(match.group(0)) if match else 0


@pytest.mark.parametrize("seed", SEEDS)
def test_same_seed(seed):
    '''Same seed should generate the same output'''

    a = negative(seed=seed)
    b = negative(seed=seed)
    assert a == b


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("lang", ["en", "fr", "es", "unknown", None])
def test_lang(seed, lang):
    '''
    Test for correct language given input
    Unknown language should fall back to english
    '''

    if not lang:
        res = negative(enthusiasm=0, seed=seed).lower()
        lang = "en"
    else:
        res = negative(language=lang, enthusiasm=0, seed=seed).lower()
    total_pool = NEGATIVE_MOTIVATIONAL.get(lang, NEGATIVE_MOTIVATIONAL["en"])
    # Remove punctuation placeholder and replace with period
    pool = [
        s.format(punct=".").lower()
        for intensity in total_pool.values() for s in intensity
    ]
    assert res in pool


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize(
    "intensity", ["soft", "medium", "hard", "unknown", None]
)
def test_intensity(seed, intensity):
    '''
    Test for correct intensity of message given input.
    Unknown intensity should fall back to medium
    '''

    if not intensity:
        res = negative(enthusiasm=0, seed=seed).lower()
        intensity = "medium"
    else:
        res = negative(enthusiasm=0, intensity=intensity, seed=seed).lower()
    pool = [
        s.format(punct=".").lower()
        for lang in NEGATIVE_MOTIVATIONAL.keys()
        for s in NEGATIVE_MOTIVATIONAL[lang].get(
            intensity, NEGATIVE_MOTIVATIONAL[lang]["medium"]
        )
    ]
    assert res in pool


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("enthusiasm", [-1, 0, 1, 5, 7, None])
def test_enthusiasm(seed, enthusiasm):
    '''
    Test for correct number of exclamation marks at end of message.
    Should be between 0-5 inclusive.
    At 0 puncutation should a period.
    '''

    if not enthusiasm:
        res = negative(seed=seed)
        enthusiasm = 2
    else:
        res = negative(enthusiasm=enthusiasm, seed=seed)
    trailing_exclamations = _count_trailing_exclamations(res)
    if enthusiasm <= 0:
        assert res[-1] == "."
    else:
        assert trailing_exclamations == max(0, min(enthusiasm, 5))


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", ["My Name", "A1B2C3", "", None])
def test_name(seed, name):
    '''
    Test for name inserted correctly at beginnign of string
    '''

    if not name:
        res = negative(seed=seed)
        assert res[0].isupper()
    else:
        res = negative(name=name, seed=seed)
        match = re.search(fr'^(?:{name}, )', res)
        assert match
