"""LLM-backed crossword clue generation, with a generic offline fallback."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from games.llm_client import get_client
from games.offline_words import resolve_bank_key

DEFAULT_MODEL = os.environ.get("CROSSWORD_MODEL", "claude-haiku-4-5-20251001")

GENERATED_CLUES_PATH = Path(__file__).resolve().parent.parent / "data" / "clue_banks.json"


def _load_generated_clues() -> dict:
    """Clue banks produced by scripts/generate_clue_banks.py, if it's been run."""
    if not GENERATED_CLUES_PATH.exists():
        return {}
    try:
        return json.loads(GENERATED_CLUES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


CLUE_BANKS = _load_generated_clues()


class ClueGenerationError(RuntimeError):
    pass


def generate_clues(words: list[str], theme: str, api_key: str) -> dict[str, str]:
    client = get_client(api_key)
    if client is None:
        raise ClueGenerationError("No API key available")

    word_list = ", ".join(words)
    prompt = (
        f'Write a short crossword clue for each of these words, themed "{theme}":\n'
        f"{word_list}\n\n"
        "Rules:\n"
        "- One concise clue per word, under 10 words\n"
        "- Never include the answer word itself (or an obvious substring of it) in its clue\n"
        "- Return ONLY a JSON object mapping each word to its clue, nothing else. "
        'Example: {"APPLE": "Common orchard fruit"}'
    )
    resp = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ClueGenerationError(f"Could not find a JSON object in the model response: {text!r}")

    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ClueGenerationError(f"Model response was not valid JSON: {text!r}") from e

    clues = {}
    for w in words:
        clue = raw.get(w) or raw.get(w.title()) or raw.get(w.capitalize())
        if clue:
            clues[w] = str(clue).strip()

    if len(clues) < len(words):
        raise ClueGenerationError("Model response was missing clues for some words")

    return clues


def offline_clues(words: list[str], theme: str) -> dict[str, str]:
    bank_key = resolve_bank_key(theme)
    bank = CLUE_BANKS.get(bank_key, {}) if bank_key else {}
    label = theme.strip() or "this puzzle"
    return {w: bank.get(w, f"A {len(w)}-letter word related to {label}") for w in words}


def get_clues(words: list[str], theme: str, api_key: str | None = None) -> tuple[dict[str, str], str]:
    """Return (clues, source) where source is "llm" or "offline"."""
    if api_key:
        try:
            return generate_clues(words, theme, api_key), "llm"
        except Exception:
            pass
    return offline_clues(words, theme), "offline"
