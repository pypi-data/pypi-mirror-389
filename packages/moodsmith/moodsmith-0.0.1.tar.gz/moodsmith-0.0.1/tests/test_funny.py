"""funny test for various improper inputs"""


from moodsmith.core import funny


def test_funny_seed_is_active():
    """test if seed produces the same string"""
    a=funny("er", None, 1, 54)
    b=funny("er", None, 1, 54)
    assert a==b


def test_intensity_not_in_range_handling():
    """places intensity in range if out of scope"""
    test = funny("hi", None, 10, 54)
    assert test.count("!")==5


def test_name_in_output_string():
    """assures that name is in returned string"""
    test = funny("fr", "joy", 1, 54)
    assert "joy" in (test)
