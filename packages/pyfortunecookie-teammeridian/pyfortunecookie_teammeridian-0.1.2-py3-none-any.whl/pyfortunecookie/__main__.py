# Categories:
#   1 = Zodiac & MBTI Summary - Written By Sina
#   2 = Tarot Reading
#   3 = Personalized Fortune
#   4 = Rune Reading
#   5 = Lucky Day

from __future__ import annotations
import argparse
import re
from typing import Optional, Union

from .core import (
    get_lucky_day,
    get_zodiac_mbti_summary,
    get_tarot_reading,
    get_fortune_by_choice,
    get_rune_reading,
    is_valid_zodiac, 
    is_valid_mbti
)

# ---- helpers ----
def parse_category_from_attribute(attr: str) -> Optional[int]:
    """Parse strings like 'fortune(category=1)' → 1."""
    if not attr:
        return None
    m = re.search(r"category\s*=\s*(\d+)", attr)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None

def normalize_category(cat: Optional[Union[str, int]]) -> Optional[int]:
    """Allow 1/2/3/4/5 or names: astro|tarot|personal|runes|day."""
    if cat is None:
        return None
    if isinstance(cat, int):
        return cat if cat in (1, 2, 3, 4, 5) else None
    s = str(cat).strip().lower()
    if s in {"1", "astro", "astrology", "zodiac"}:
        return 1
    if s in {"2", "tarot"}:
        return 2
    if s in {"3", "personal", "personalized"}:
        return 3
    if s in {"4", "runes", "runes"}:
        return 4
    if s in {"5", "day", "lucky_day", "luckyday"}:
        return 5
    return None

def ask_choice(label: str, options: list[str]) -> str:
    while True:
        ans = input(f"{label} {options}: ").strip().lower()
        if ans in options:
            return ans
        print(f"Invalid choice. Please choose one of {options}.")

def main():
    parser = argparse.ArgumentParser(
        description="PyFortune Cookie CLI (choose a category to run)."
    )
    parser.add_argument("--category", type=str, default=None,
                        help="1|2|3 or names: astro|tarot|personal")
    parser.add_argument("--attribute", type=str, default=None,
                        help='Alternative selector text, e.g. "fortune(category=1)"')
    parser.add_argument("--zodiac", type=str, default=None,
                        help="Your zodiac (e.g., aries, libra, pisces) for category 1")
    parser.add_argument("--mbti", type=str, default=None,
                        help="Your MBTI (e.g., INFP, ESTJ) for category 1")
    parser.add_argument("--no-input", action="store_true",
                        help="Skip zodiac/MBTI prompts for category 1")
    parser.add_argument("--rune-reading", type=str, default=None,
                        help="Get a rune reading for category 4")
    args = parser.parse_args()

    print("🥠 Welcome to PyFortune Cookie!")

    while True:
        cat: Optional[int] = normalize_category(args.category)
        if cat is None and args.attribute:
            cat = parse_category_from_attribute(args.attribute)
        if cat is None:
            print("\nSelect a category:")
            print("  1) Zodiac & MBTI Summary")
            print("  2) Tarot Reading")
            print("  3) Personalized Fortune")
            print("  4) Rune Reading")
            print("  5) Lucky Day")
            while True:
                raw = input("Enter 1 / 2 / 3 / 4 / 5: ").strip()
                if raw in {"1", "2", "3", "4", "5"}:
                    cat = int(raw)
                    break
                print("Please enter number between 1-5.")

        # Run category
        if cat == 1:
            # Zodiac & MBTI Summary
            zodiac = args.zodiac
            mbti = args.mbti

            if not args.no_input and (zodiac is None and mbti is None):
                # zodiac: loop until valid or skipped
                while True:
                    z = input("Enter your zodiac (e.g., Aries, Libra, Pisces) or press Enter to skip: ").strip()
                    if z == "" or is_valid_zodiac(z):
                        zodiac = z or None
                        break
                    print("Not a valid zodiac. Please try again (e.g., Aries, Libra).")

                # mbti: loop until valid or skipped
                while True:
                    m = input("Enter your MBTI (e.g., INFP, ESTJ) or press Enter to skip: ").strip()
                    if m == "" or is_valid_mbti(m):
                        mbti = m or None
                        break
                    print("Not a valid MBTI. Please try again (e.g., INFP, ESTJ).")

                summary = get_zodiac_mbti_summary(zodiac=zodiac, mbti=mbti)

                print("\n🌙 Your Fortune Summary 🌙")
                if summary["zodiac"] or summary["mbti"]:
                    print(f"Zodiac: {summary['zodiac'].title() if summary['zodiac'] else '-'} | MBTI: {summary['mbti'] or '-'}")
                print(f"Fortune: {summary['fortune']}")
                print(f"Lucky Number: {summary['lucky_number']}")
                print(f"Lucky Color: {summary['lucky_color']}")
                
        elif cat == 2:
            # Tarot Reading
            print("\n🔮 Tarot Reading:")
            print(get_tarot_reading())

        elif cat == 3:
            # Personalized Fortune
            print("\n🎴 Personalized Fortune (by your choices):")
            elements = ["fire", "water", "earth", "air"]
            times = ["dawn", "noon", "dusk", "midnight"]
            symbols = ["star", "moon", "sun", "cloud"]

            c1 = ask_choice("Choose an element", elements)
            c2 = ask_choice("Choose a time", times)
            c3 = ask_choice("Choose a symbol", symbols)

            result = get_fortune_by_choice(c1, c2, c3)

            print("\n✨ Your Personalized Fortune ✨")
            print(f"Element: {result['element']}")
            print(f"Time: {result['time']}")
            print(f"Symbol: {result['symbol']}")
            print(f"Combination: {result['combination']}")
            print(f"Fortune: {result['fortune']}")
        
        elif cat == 4:
            # Rune Reading
            readings = get_rune_reading()
            print("\n🔮 Rune Reading:")
            for reading in readings:
                print(f" - {reading}")

        elif cat == 5:
            # Lucky Day
            print("\n Lucky Day:")
            lucky_day = get_lucky_day()
            print(f"Day: {lucky_day['day']}")
        else:
            print("Unknown category. Please choose 1, 2, 3, 4 or 5.")

        # Ask if user wants to continue / exit
        again = input("\nWould you like to choose another category? (y/n): ").strip().lower()
        if again not in {"y", "yes"}:
            # exit
            print("\n🌟 Thank you for using PyFortune Cookie! Goodbye! 🌟")
            break
        else:
            #continue
            args.category = None
            args.attribute = None

if __name__ == "__main__":
    main()
