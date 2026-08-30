"""One-time batch generation of offline word banks.

Calls the live Anthropic API once per seed theme and writes the results to
games/data/theme_banks.json, which games/offline_words.py loads at import
time to supplement the hand-curated THEME_BANKS. This turns a recurring
per-puzzle API cost into a one-time cost, and gives the no-API-key/offline
mode real coverage instead of falling back to GENERIC_BANK for anything
not hand-curated.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...   # a real key with a small amount of credit
    python scripts/generate_word_banks.py            # generate only missing themes
    python scripts/generate_word_banks.py --overwrite  # regenerate everything
    python scripts/generate_word_banks.py --only dogs cats  # just these themes
    python scripts/generate_word_banks.py --only dogs --append 15  # add 15 more words to an existing theme

Resumable: re-running skips themes already present in the output file
unless --overwrite is passed, so a rate-limit error or Ctrl-C partway
through just means running it again picks up where it left off.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from games.wordlists import generate_word_list, ThemeGenerationError  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "games" / "data" / "theme_banks.json"

WORDS_PER_THEME = 50
MIN_LEN = 3
MAX_LEN = 12
SLEEP_BETWEEN_CALLS = 1.0

SEED_THEMES = [
    # Animals
    "cats", "horses", "farm animals", "insects", "reptiles", "big cats",
    "forest animals", "arctic animals", "jungle animals", "pets", "bugs",
    "sea creatures", "amphibians", "monkeys", "bears", "wolves", "foxes",
    "owls", "bees", "butterflies", "spiders", "snakes", "turtles", "frogs",
    # Nature & outdoors
    "trees", "mountains", "rivers", "deserts", "rainforest", "gardening",
    "camping", "hiking", "national parks", "rocks and minerals", "volcanoes",
    "caves", "waterfalls", "forests", "seasons", "autumn", "spring",
    "summer", "winter", "rain", "snow", "sunshine", "storms",
    # Food & drink
    "coffee", "tea", "baking", "barbecue", "breakfast", "desserts",
    "italian food", "mexican food", "japanese food", "seafood", "cheese",
    "wine", "beer", "chocolate", "candy", "ice cream", "pizza toppings",
    "farmers market", "spices", "herbs",
    # Holidays & celebrations
    "thanksgiving", "easter", "valentines day", "st patricks day",
    "new years eve", "fourth of july", "hanukkah", "birthday party",
    "wedding", "baby shower", "graduation", "retirement", "anniversary",
    # Hobbies
    "knitting", "sewing", "painting", "photography", "fishing", "golf",
    "yoga", "chess", "board games", "video games", "reading", "gaming",
    "scrapbooking", "woodworking", "pottery", "collecting", "puzzles",
    "crafting", "jigsaw puzzles",
    # Occupations
    "doctors", "firefighters", "police officers", "teachers", "farmers",
    "construction workers", "nurses", "pilots", "chefs", "scientists",
    "artists", "engineers", "lawyers", "veterinarians", "astronauts",
    "musicians", "athletes", "librarians",
    # Transportation
    "trains", "boats", "race cars", "trucks", "motorcycles", "airplanes",
    "space travel", "sailing", "submarines", "bicycles",
    # Places
    "beach", "camping", "zoo", "aquarium", "amusement park", "farms",
    "cities", "countries", "world capitals", "islands", "deserts of the world",
    "castles", "lighthouses", "national monuments",
    # Body, health & science
    "human body", "exercise", "nutrition", "first aid", "the five senses",
    "dentist visit", "doctor visit", "chemistry", "physics", "biology",
    "the solar system", "weather science", "the human brain",
    # Technology
    "computers", "robots", "the internet", "video games", "science fiction",
    "smartphones", "coding", "artificial intelligence",
    # Arts & entertainment
    "movies", "theater", "dance", "art supplies", "superheroes",
    "fairy tales", "mythology", "circus", "carnival", "magic tricks",
    "pirates", "knights", "castles and dragons", "unicorns", "mermaids",
    "outer space", "aliens", "ghosts and monsters",
    # School & learning
    "math class", "geography", "history", "english class", "art class",
    "kindergarten", "back to school", "college life",
    # Music
    "rock music", "jazz", "classical music", "country music", "hip hop",
    "musical instruments", "singing",
    # Sports (beyond existing "sports" bank)
    "football", "basketball players", "baseball", "skiing", "surfing",
    "skateboarding", "martial arts", "gymnastics", "track and field",
    # Home & everyday life
    "kitchen tools", "tools and hardware", "cleaning supplies", "furniture",
    "clothing", "shoes", "jewelry", "office supplies", "gardening tools",
    # Misc popular puzzle-book themes
    "cars", "trucks and tractors", "dinosaurs and fossils", "under the sea",
    "farm life", "jungle safari", "arctic animals and ice", "bugs and insects",
    "princess and castles", "space exploration", "wild west", "safari",
]


def load_existing() -> dict:
    if OUTPUT_PATH.exists():
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    return {}


def save(banks: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(banks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    import httpx
    print(f"Python: {sys.executable}")
    print(f"httpx:  {httpx.__version__} ({httpx.__file__})")

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--overwrite", action="store_true", help="Regenerate themes that already have data")
    mode.add_argument("--append", type=int, metavar="N", help="Add N new words to themes that already have data, without duplicating existing words")
    parser.add_argument("--only", nargs="*", help="Only generate these specific theme names")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set. Export a real key with a small amount of credit and re-run.")
        sys.exit(1)

    themes = args.only if args.only else SEED_THEMES
    banks = load_existing()

    if args.append:
        todo = [t for t in themes if t in banks]
        missing = [t for t in themes if t not in banks]
        if missing:
            print(f"Skipping {len(missing)} theme(s) with no existing data (run without --append first): {', '.join(missing)}")
        if not todo:
            print("No existing themes to append to.")
            return

        print(f"Appending up to {args.append} new word(s) each to {len(todo)} theme(s)...")
        for i, theme in enumerate(todo, 1):
            existing = banks[theme]
            existing_set = set(existing)
            try:
                new_words = generate_word_list(
                    theme, api_key, count=args.append, min_len=MIN_LEN, max_len=MAX_LEN, exclude=existing
                )
                added = [w for w in new_words if w not in existing_set]
                banks[theme] = existing + added
                dupes = len(new_words) - len(added)
                print(f"[{i}/{len(todo)}] {theme}: +{len(added)} new word(s)" + (f" ({dupes} duplicate(s) discarded)" if dupes else ""))
                save(banks)
            except ThemeGenerationError as e:
                print(f"[{i}/{len(todo)}] {theme}: FAILED ({e})")
            except Exception as e:
                print(f"[{i}/{len(todo)}] {theme}: FAILED (unexpected: {e})")

            if i < len(todo):
                time.sleep(SLEEP_BETWEEN_CALLS)

        print(f"Done. {len(banks)} themes total in {OUTPUT_PATH}")
        return

    todo = [t for t in themes if args.overwrite or t not in banks]
    if not todo:
        print(f"Nothing to do — all {len(themes)} requested themes already have data. Use --overwrite to regenerate.")
        return

    print(f"Generating {len(todo)} theme(s), skipping {len(themes) - len(todo)} already done...")

    for i, theme in enumerate(todo, 1):
        try:
            words = generate_word_list(theme, api_key, count=WORDS_PER_THEME, min_len=MIN_LEN, max_len=MAX_LEN)
            banks[theme] = words
            print(f"[{i}/{len(todo)}] {theme}: {len(words)} words")
            save(banks)
        except ThemeGenerationError as e:
            print(f"[{i}/{len(todo)}] {theme}: FAILED ({e})")
        except Exception as e:
            print(f"[{i}/{len(todo)}] {theme}: FAILED (unexpected: {e})")

        if i < len(todo):
            time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"Done. {len(banks)} themes total in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
