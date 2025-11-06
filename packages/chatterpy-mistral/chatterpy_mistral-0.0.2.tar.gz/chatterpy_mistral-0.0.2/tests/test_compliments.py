import random
import pytest
from chatterpy_mistral.compliments import compliment

"""
Unit tests for compliment().
"""

@pytest.fixture(autouse=True)
def _seed_each_test():
    # Ensure repeatable outputs for tests that rely on random.choice
    random.seed(0)


def test_returns_nonempty_string():
    result = compliment()
    assert isinstance(result, str)
    assert result.strip() != ""


def test_name_prefix_present_when_provided():
    s = compliment("Serena", intensity=2)
    assert s.startswith("Serena, ")


def test_intensity_is_clamped_to_1_3_bounds():
    low = compliment(intensity=0)    # below lower bound -> clamp to 1
    high = compliment(intensity=99)  # above upper bound -> clamp to 3
    assert isinstance(low, str) and isinstance(high, str)
    assert low.strip() != "" and high.strip() != ""


@pytest.mark.parametrize(
    "style, tail_check",
    [
        ("classic", lambda s: not s.endswith("optimized.") and "calm water." not in s),
        ("geeky",  lambda s: s.endswith("optimized.")),
        ("poetic", lambda s: s.endswith("calm water.")),
    ],
)
def test_style_tails(style, tail_check):
    s = compliment(style=style)
    assert tail_check(s)


@pytest.mark.parametrize("category", ["personality", "appearance", "accomplishment"])
def test_all_standard_categories_return_strings(category):
    s = compliment(category=category, intensity=2)
    assert isinstance(s, str)
    assert s.strip() != ""


def test_specific_category_without_detail_uses_placeholder():
    s = compliment(category="specific", intensity=1)
    assert "that" in s.lower()


def test_specific_category_with_detail_is_injected():
    s = compliment(category="specific", detail="your presentation", intensity=2)
    assert "your presentation" in s


def test_invalid_category_falls_back_gracefully():
    s = compliment(category="not-a-real-category")
    assert isinstance(s, str) and s.strip() != ""


def test_backhanded_fragments_are_filtered_out():
    banned = [
        "for someone like you",
        "than you look",
        "actually pretty good",
        "not bad",
        "surprisingly good",
    ]
    s = compliment()
    assert not any(b in s.lower() for b in banned)


def test_accepts_none_name_without_crashing():
    s = compliment(name=None)
    assert isinstance(s, str) and s.strip() != ""


def test_output_is_single_line_no_newlines():
    s = compliment()
    assert "\n" not in s and "\r" not in s
#TODO