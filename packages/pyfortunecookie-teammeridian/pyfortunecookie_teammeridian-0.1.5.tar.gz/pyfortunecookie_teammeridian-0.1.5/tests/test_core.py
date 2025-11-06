import pytest, random
from pyfortunecookie.core import get_fortune, get_lucky_number, get_color, get_tarot_reading, get_fortune_by_choice, get_lucky_day, get_rune_reading

def test_get_fortune():
    result = get_fortune()
    assert isinstance(result, str)
    assert len(result) > 0

def test_get_lucky_number():
    num = get_lucky_number()
    assert isinstance(num, int)
    assert 1 <= num <= 99

def test_get_color():
    color = get_color()
    assert isinstance(color, str)
    assert len(color) > 0

def test_get_tarot_reading_basic():
    text = get_tarot_reading()
    assert isinstance(text, str)
    assert ":" in text
    assert len(text) > 0

def test_get_tarot_reading_with_intent():
    text = get_tarot_reading(intent="needing_clarity")
    assert isinstance(text, str)
    assert ":" in text

def test_get_tarot_reading_invalid_intent_fallback():
    text = get_tarot_reading(intent="nonsense_value")
    assert isinstance(text, str)
    assert ":" in text

def test_get_rune_reading_correct_format():
    rng = random.Random(42)
    result = get_rune_reading(n=3, rng=rng)
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(r, str) for r in result)
    assert all(":" in r for r in result)

def test_get_rune_reading_uniqueness():
    a = random.Random(100)
    b = random.Random(100)
    ra = get_rune_reading(n=3, rng=a)
    rb = get_rune_reading(n=3, rng=b)
    assert ra == rb

def test_get_rune_reading_invalid_n():
    with pytest.raises(ValueError):
        get_rune_reading(n=0)
        
def test_get_fortune_by_choice_returns_dict():
        """Test that function returns a dictionary."""
        result = get_fortune_by_choice("fire", "dawn", "star")
        assert isinstance(result, dict)

def test_get_fortune_by_choice_has_required_keys():
        """Test that returned dict has all required keys."""
        result = get_fortune_by_choice("fire", "dawn", "star")
        required_keys = ["fortune", "element", "time", "symbol", "combination", "lucky_number", "lucky_color"]
        for key in required_keys:
            assert key in result

def test_get_fortune_by_choice_valid_elements():
        """Test all valid element choices."""
        elements = ["fire", "water", "earth", "air"]
        for element in elements:
            result = get_fortune_by_choice(element, "dawn", "star")
            assert result["element"] == element
            assert isinstance(result["fortune"], str)
            assert len(result["fortune"]) > 0

def test_get_lucky_day_returns_dict():
    """Test that get_lucky_day returns a dictionary."""
    result = get_lucky_day()
    assert isinstance(result, dict)

def test_get_lucky_day_has_required_keys():
    """Test that the returned dict has all required keys."""
    result = get_lucky_day()
    assert "day" in result
    assert "message" in result
    assert isinstance(result["day"], str)
    assert isinstance(result["message"], str)

def test_get_lucky_day_valid_days():
    """Test that the day returned is a valid day of the week."""
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = get_lucky_day()
    assert result["day"] in valid_days
    assert len(result["message"]) > 0

# tests for zodiac + MBTI fortune
from pyfortunecookie.core import (
    get_zodiac_mbti_summary,
    is_valid_zodiac,
    is_valid_mbti,
)

def test_personality_summary_structure_and_types():
    s = get_zodiac_mbti_summary(zodiac=None, mbti=None)
    assert isinstance(s, dict)
    # required keys
    for k in ["fortune", "lucky_color", "lucky_number", "lucky_day"]:
        assert k in s
    # types
    assert isinstance(s["fortune"], str)
    assert isinstance(s["lucky_color"], str)
    assert isinstance(s["lucky_number"], int)
    assert isinstance(s["lucky_day"], dict)
    assert "day" in s["lucky_day"] and "message" in s["lucky_day"]

def test_mbti_tilt_messages():
    """INTJ biases to action message; INFP biases to imagination message."""
    s_action = get_zodiac_mbti_summary(zodiac="Libra", mbti="INTJ")
    assert "Take action with confidence!" in s_action["fortune"]

    s_imagination = get_zodiac_mbti_summary(zodiac="Libra", mbti="INFP")
    assert "Let your imagination guide you!" in s_imagination["fortune"]

def test_validators_accept_valid_and_reject_invalid():
    """Validators accept real values and reject typos like 'entl'."""
    # zodiac
    assert is_valid_zodiac("Aries")
    assert is_valid_zodiac("pisces")
    assert not is_valid_zodiac("dragon")
    assert not is_valid_zodiac("")
    # mbti
    assert is_valid_mbti("ENTP")
    assert is_valid_mbti("infj")
    assert not is_valid_mbti("entl")   # typo should be rejected
    assert not is_valid_mbti("abcd")

def test_color_present_with_zodiac():
    """Smoke test: with a zodiac provided, summary still returns a non-empty color."""
    s = get_zodiac_mbti_summary(zodiac="Aries", mbti=None)
    assert isinstance(s["lucky_color"], str)
    assert len(s["lucky_color"]) > 0

