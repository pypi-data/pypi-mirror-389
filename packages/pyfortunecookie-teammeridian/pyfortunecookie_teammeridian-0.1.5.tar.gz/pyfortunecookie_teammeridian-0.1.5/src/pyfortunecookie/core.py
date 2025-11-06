import random
from typing import Optional

_TAROT = {
    "The Fool": "New beginnings, take a leap of faith.",
    "The Magician": "Your skills will shape reality.",
    "The High Priestess": "Trust your intuition.",
    "The Empress": "Abundance grows where you nurture.",
    "The Emperor": "Structure brings stability.",
    "The Hierophant": "Tradition and guidance shape your path.",
    "The Lovers": "Meaningful connections influence your decisions.",
    "The Chariot": "Focus and willpower drive victory.",
    "Strength": "Quiet courage overcomes fear.",
    "The Hermit": "Solitude reveals deeper answers.",
    "Wheel of Fortune": "Things will shift—be adaptable.",
    "Justice": "Balance and fairness will restore order.",
    "The Hanged Man": "Change perspective to see clearly.",
    "Death": "A chapter ends so something new can begin.",
    "Temperance": "Moderation creates harmony.",
    "The Devil": "Beware of illusions and temptation.",
    "The Tower": "Old structures must fall before renewal.",
    "The Star": "Hope quietly returns.",
    "The Moon": "The truth is hidden beneath uncertainty.",
    "The Sun": "Joy, clarity, and success await.",
    "Judgement": "Your past transforms into resolution.",
    "The World": "Completion brings fulfillment."
}

_TAROT_GROUP = {
    "seeking_change": [
        "The Fool", "The Tower", "Death", "The Chariot", "Judgement", "Wheel of Fortune"
    ],
    "needing_clarity": [
        "The High Priestess", "The Moon", "The Hermit", "The Hanged Man", "Justice"
    ],
    "needing_support": [
        "Strength", "Temperance", "The Star", "The Sun", "The Empress", "The World"
    ]
}
_FORTUNES = [
    "Today is a good day to start small.",
    "A pleasant surprise is waiting for you.",
    "Your code will compile on the first try.",
    "Help others and luck will help you.",
    "Take a short walk; ideas will follow.",
    "A cup of coffee will solve half your problems. ☕",
    "You will soon discover a hidden strength. 💪",
    "Your curiosity is your superpower. 🔍"
]

_PALETTES = {
    "soft": ["peach", "mint", "lavender", "sky", "lemon"],
    "bold": ["crimson", "indigo", "emerald", "amber", "teal"],
    "mono": ["black", "white", "gray"]
}

_LUCKY_DAYS = {
    "Friday": "A blessed day awaits you.",
    "Saturday": "A day of rest and rejuvenation.",
    "Sunday": "A day of reflection and self-care.",
    "Monday": "A fresh start to the week brings new opportunities.",
    "Tuesday": "Your determination will pay off today.",
    "Wednesday": "Communication leads to breakthroughs.",
    "Thursday": "Expansion and growth are in your favor.",
}

_RUNES = {
    "Fehu": "Wealth, new beginnings, prosperity.",
    "Uruz": "Strength and endurance.",
    "Thurisaz": "Conflict, challenge, or protection.",
    "Ansuz": "Wisdom, communication, divine inspiration.",
    "Raidho": "Journey, movement, or progress.",
    "Kenaz": "Creativity, revelation, transformation.",
    "Gebo": "Gift, partnership, generosity.",
    "Wunjo": "Joy, harmony, well-being."
}

def get_fortune(rng: Optional[random.Random] = None) -> str:
    """Return a random fortune sentence."""
    rng = rng or random
    return rng.choice(_FORTUNES)

def get_lucky_number(seed: Optional[int] = None, min_value: int = 1, max_value: int = 99) -> int:
    """Return a lucky number (optionally deterministic if seed provided)."""
    if min_value > max_value:
        raise ValueError("min_value must be <= max_value")
    rng = random.Random(seed) if seed is not None else random
    return rng.randint(min_value, max_value)

def get_color(palette: str = "soft", rng: Optional[random.Random] = None) -> str:
    """Return a lucky color from the selected palette."""
    if palette not in _PALETTES:
        raise ValueError(f"Unknown palette '{palette}'. Valid: {', '.join(_PALETTES)}")
    rng = rng or random
    return rng.choice(_PALETTES[palette])

# fortune summary influenced by zodiac/MBTI.
def is_valid_zodiac(z: Optional[str]) -> bool:
    """Check if zodiac string is one of 12 Western zodiac signs."""
    if not z:
        return False
    z = z.strip().lower()
    return z in {
        "aries","taurus","gemini","cancer","leo","virgo",
        "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
    }

def is_valid_mbti(m: Optional[str]) -> bool:
    """Check if MBTI is one of the 16 types."""
    if not m:
        return False
    m = m.strip().upper()
    return m in {
        "INTJ","INTP","ENTJ","ENTP","INFJ","INFP","ENFJ","ENFP",
        "ISTJ","ISFJ","ESTJ","ESFJ","ISTP","ISFP","ESTP","ESFP"
    }

def get_zodiac_mbti_summary(zodiac: Optional[str] = None,
                         mbti: Optional[str] = None,
                         rng: Optional[random.Random] = None) -> dict:
   
    rng = rng or random

    # normalize inputs
    z = (zodiac or "").strip().lower()
    m = (mbti or "").strip().upper()

    # zodiac -> palette preference (only affects color choice)
    palette_map = {
        "aries": "bold", "leo": "bold", "sagittarius": "bold",
        "taurus": "mono", "virgo": "mono", "capricorn": "mono",
        "gemini": "soft", "libra": "soft", "aquarius": "soft",
        "cancer": "soft", "scorpio": "bold", "pisces": "soft",
    }
    palette = palette_map.get(z, "soft")

    # MBTI tilt on fortune tone
    prefer_action = ("T" in m) or ("J" in m)
    prefer_idea = "N" in m

    sentence = get_fortune(rng=rng)
    if prefer_action:
        sentence += " Take action with confidence!"
    elif prefer_idea:
        sentence += " Let your imagination guide you!"

    # lucky color/number/day
    color = get_color(palette=palette, rng=rng)
    number = get_lucky_number()               
    day = get_lucky_day(rng=rng)

    return {
        "fortune": sentence,
        "lucky_color": color,
        "lucky_number": number,
        "lucky_day": day,          
        "zodiac": z or None,
        "mbti": m or None,
        "palette_used": palette,
    }


def get_tarot_reading(intent: Optional[str] = None, rng: Optional[random.Random] = None) -> str:
    """
    Return a tarot reading with slight bias based on intent.
    Valid intents: seeking_change, needing_clarity, needing_support
    """
    rng = rng or random

    if intent in _TAROT_GROUP:
        if rng.random() < 0.7:
            pool = _TAROT_GROUP[intent]
        else:
            pool = [c for c in _TAROT.keys() if c not in _TAROT_GROUP[intent]]
    else:
        pool = list(_TAROT.keys())

    card = rng.choice(pool)
    meaning = _TAROT[card]
    return f"{card}: {meaning}"

def get_rune_reading(n=3, rng: Optional[random.Random] = None) -> str:
    """Return a rune reading with n runes."""
    if n < 1:
        raise ValueError("n must be at least 1")
    rng = rng or random
    selected_runes = rng.sample(list(_RUNES.keys()), k=n)
    readings = [f"{rune}: {_RUNES[rune]}" for rune in selected_runes]
    return readings

def get_fortune_by_choice(choice1: str, choice2: str, choice3: str, rng: Optional[random.Random] = None) -> dict:
    """
    Get a personalized fortune based on three interactive choices.
    A fun, interactive way to get a fortune that feels tailored to you.
    
    Args:
        choice1: Choose an element - "fire", "water", "earth", or "air"
        choice2: Choose a time - "dawn", "noon", "dusk", or "midnight"  
        choice3: Choose a symbol - "star", "moon", "sun", or "cloud"
        rng: Optional random number generator for testing
    
    Returns:
        Dictionary containing:
            - fortune: Personalized fortune message
            - element: The element chosen
            - time: The time chosen
            - symbol: The symbol chosen
            - combination: A description of what your choices mean
            - lucky_number: A number based on your choices
            - lucky_color: A color based on your element
    
    Raises:
        ValueError: If any choice is not from the valid options
    
    Example:
        >>> result = get_fortune_by_choice("fire", "dawn", "star")
        >>> print(result['fortune'])
        "Your fiery spirit at dawn attracts stellar opportunities! ⭐🔥"
    """
    # Valid options
    valid_elements = ["fire", "water", "earth", "air"]
    valid_times = ["dawn", "noon", "dusk", "midnight"]
    valid_symbols = ["star", "moon", "sun", "cloud"]
    
    # Validate inputs
    if choice1 not in valid_elements:
        raise ValueError(f"Invalid element '{choice1}'. Valid: {', '.join(valid_elements)}")
    if choice2 not in valid_times:
        raise ValueError(f"Invalid time '{choice2}'. Valid: {', '.join(valid_times)}")
    if choice3 not in valid_symbols:
        raise ValueError(f"Invalid symbol '{choice3}'. Valid: {', '.join(valid_symbols)}")
    
    rng = rng or random
    
    # Element meanings and colors
    element_data = {
        "fire": {
            "trait": "passionate and energetic",
            "color": "crimson",
            "emoji": "🔥"
        },
        "water": {
            "trait": "adaptable and intuitive",
            "color": "teal",
            "emoji": "💧"
        },
        "earth": {
            "trait": "grounded and stable",
            "color": "emerald",
            "emoji": "🌍"
        },
        "air": {
            "trait": "free-spirited and intellectual",
            "color": "sky",
            "emoji": "💨"
        }
    }
    
    # Time meanings
    time_data = {
        "dawn": {
            "meaning": "new beginnings",
            "emoji": "🌅"
        },
        "noon": {
            "meaning": "peak energy and clarity",
            "emoji": "☀️"
        },
        "dusk": {
            "meaning": "reflection and transformation",
            "emoji": "🌆"
        },
        "midnight": {
            "meaning": "mystery and deep insight",
            "emoji": "🌙"
        }
    }
    
    # Symbol meanings
    symbol_data = {
        "star": {
            "meaning": "guidance and aspiration",
            "emoji": "⭐",
            "fortunes": [
                "Your path is illuminated by cosmic guidance!",
                "Reach for the stars; they're closer than you think!",
                "Stellar opportunities align in your favor!"
            ]
        },
        "moon": {
            "meaning": "intuition and cycles",
            "emoji": "🌙",
            "fortunes": [
                "Trust your intuition; it knows the way!",
                "Embrace the cycles of change in your life!",
                "Your inner wisdom shines like moonlight!"
            ]
        },
        "sun": {
            "meaning": "vitality and success",
            "emoji": "☀️",
            "fortunes": [
                "Your energy radiates success and warmth!",
                "Bright opportunities are on the horizon!",
                "Your light will inspire others today!"
            ]
        },
        "cloud": {
            "meaning": "imagination and possibility",
            "emoji": "☁️",
            "fortunes": [
                "Your imagination opens doors to new possibilities!",
                "Dream big; the sky is not the limit!",
                "Creative solutions float into your awareness!"
            ]
        }
    }
    
    # Get data for chosen options
    element_info = element_data[choice1]
    time_info = time_data[choice2]
    symbol_info = symbol_data[choice3]
    
    # Generate personalized fortune
    base_fortune = rng.choice(symbol_info["fortunes"])
    
    # Create combination description
    combination = (
        f"You are {element_info['trait']}, seeking {time_info['meaning']}, "
        f"guided by {symbol_info['meaning']}."
    )
    
    # Generate lucky number based on choices (deterministic for same choices)
    choice_seed = hash(f"{choice1}{choice2}{choice3}") % 10000
    temp_rng = random.Random(choice_seed)
    lucky_num = temp_rng.randint(1, 99)
    
    # Build full fortune message
    full_fortune = (
        f"{element_info['emoji']} {time_info['emoji']} {symbol_info['emoji']} "
        f"{base_fortune}"
    )
    
    return {
        "fortune": full_fortune,
        "element": choice1,
        "time": choice2,
        "symbol": choice3,
        "combination": combination,
        "lucky_number": lucky_num,
        "lucky_color": element_info["color"]
    }

def get_lucky_day(rng: Optional[random.Random] = None) -> dict:
    """
    Return a lucky day of the week and its lucky meaning.
    
    Returns:
        Dictionary containing:
            - day: The name of the lucky day
            - message: A message about what makes this day special
    """
    rng = rng or random
    day = rng.choice(list(_LUCKY_DAYS.keys()))
    message = _LUCKY_DAYS[day]
    
    return {
        "day": day,
        "message": message
    }
