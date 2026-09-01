"""One-time batch generation of offline crossword clue banks.

Calls the live Anthropic API for each theme already in games/offline_words.py
(both hand-curated THEME_BANKS and anything scripts/generate_word_banks.py
produced) and writes real clues to games/data/clue_banks.json, which
games/crossword/clues.py loads to serve real offline clues instead of the
generic "N-letter word related to X" placeholder.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...   # a real key with a small amount of credit
    python scripts/generate_clue_banks.py               # generate only missing themes
    python scripts/generate_clue_banks.py --overwrite   # regenerate everything
    python scripts/generate_clue_banks.py --only gardening flowers  # just these themes

Resumable: re-running skips themes already present in the output file
unless --overwrite is passed. Each theme's words are sent in chunks (the
Anthropic API call caps response length, so a 50-word theme needs a few
calls); a chunk failure doesn't lose the rest of the theme's clues, and the
crossword offline fallback gracefully fills in any word missing from the
bank with a generic clue.
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

from games.crossword.clues import generate_clues, ClueGenerationError  # noqa: E402
from games.offline_words import THEME_BANKS  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "games" / "data" / "clue_banks.json"

CHUNK_SIZE = 20
SLEEP_BETWEEN_CALLS = 1.0


def load_existing() -> dict:
    if OUTPUT_PATH.exists():
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    return {}


def save(banks: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(banks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def generate_theme_clues(theme: str, words: list[str], api_key: str) -> tuple[dict, int]:
    clues: dict[str, str] = {}
    failed_chunks = 0
    for i in range(0, len(words), CHUNK_SIZE):
        chunk = words[i:i + CHUNK_SIZE]
        try:
            clues.update(generate_clues(chunk, theme, api_key))
        except ClueGenerationError:
            failed_chunks += 1
        except Exception:
            failed_chunks += 1
        if i + CHUNK_SIZE < len(words):
            time.sleep(SLEEP_BETWEEN_CALLS)
    return clues, failed_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Regenerate themes that already have data")
    parser.add_argument("--only", nargs="*", help="Only generate these specific theme names")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set. Export a real key with a small amount of credit and re-run.")
        sys.exit(1)

    themes = args.only if args.only else sorted(THEME_BANKS.keys())
    clue_banks = load_existing()

    todo = [t for t in themes if args.overwrite or t not in clue_banks]
    if not todo:
        print(f"Nothing to do — all {len(themes)} requested themes already have clue data. Use --overwrite to regenerate.")
        return

    print(f"Generating clues for {len(todo)} theme(s), skipping {len(themes) - len(todo)} already done...")

    for i, theme in enumerate(todo, 1):
        words = THEME_BANKS.get(theme)
        if not words:
            print(f"[{i}/{len(todo)}] {theme}: SKIPPED (no words found for this theme)")
            continue

        clues, failed_chunks = generate_theme_clues(theme, list(words), api_key)
        if not clues:
            print(f"[{i}/{len(todo)}] {theme}: FAILED (no clues generated)")
        else:
            clue_banks[theme] = clues
            note = f" ({failed_chunks} chunk(s) failed, using generic fallback for those words)" if failed_chunks else ""
            print(f"[{i}/{len(todo)}] {theme}: {len(clues)}/{len(words)} clues{note}")
            save(clue_banks)

        if i < len(todo):
            time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"Done. {len(clue_banks)} themes total in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
