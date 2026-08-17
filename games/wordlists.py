"""LLM-backed theme word list generation via the Anthropic API."""
from __future__ import annotations

import json
import os
import re

from games.llm_client import get_client
from games.offline_words import get_offline_word_list

DEFAULT_MODEL = os.environ.get("WORDSEARCH_MODEL", "claude-haiku-4-5-20251001")


class ThemeGenerationError(RuntimeError):
    pass


def generate_word_list(theme: str, api_key: str, count: int = 12, min_len: int = 4, max_len: int = 10) -> list[str]:
    theme = theme.strip()
    if not theme:
        raise ValueError("theme must not be empty")

    client = get_client(api_key)
    if client is None:
        raise ThemeGenerationError("No API key available")

    prompt = (
        f'Generate exactly {count} words for a word search puzzle themed "{theme}".\n\n'
        "Rules:\n"
        f"- Each word must be {min_len}-{max_len} letters long, A-Z only (no spaces, hyphens, or punctuation)\n"
        f'- Words should be clearly and specifically related to the theme "{theme}"\n'
        "- No duplicate words\n"
        "- Return ONLY a JSON array of uppercase strings, nothing else. "
        'Example: ["APPLE", "BANANA"]'
    )

    resp = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ThemeGenerationError(f"Could not find a JSON array in the model response: {text!r}")

    try:
        raw_words = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ThemeGenerationError(f"Model response was not valid JSON: {text!r}") from e

    cleaned = []
    seen = set()
    for w in raw_words:
        cleaned_word = "".join(ch for ch in str(w).upper() if ch.isalpha())
        if min_len <= len(cleaned_word) <= max_len and cleaned_word not in seen:
            cleaned.append(cleaned_word)
            seen.add(cleaned_word)

    if not cleaned:
        raise ThemeGenerationError(f"No usable words survived cleaning for theme {theme!r}")

    return cleaned[:count]


def get_word_list(theme: str, count: int = 12, min_len: int = 4, max_len: int = 10, api_key: str | None = None) -> tuple[list[str], str]:
    """Return (words, source) where source is "llm" or "offline".

    Uses the live Anthropic API when api_key is provided, falling back to
    the built-in word banks if no key is given or the API call fails.
    """
    if api_key:
        try:
            return generate_word_list(theme, api_key, count=count, min_len=min_len, max_len=max_len), "llm"
        except Exception:
            pass
    return get_offline_word_list(theme, count=count, min_len=min_len, max_len=max_len), "offline"
