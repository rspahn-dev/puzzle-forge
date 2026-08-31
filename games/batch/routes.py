"""Batch/book mode: generate several puzzles of one game type into a single
print-ready PDF (puzzles section, then an answer-key section) — the KDP/Etsy
puzzle-book workflow. Puzzles aren't persisted individually; the PDF is built
and streamed back in one request."""
import os
import random
import tempfile

from flask import Blueprint, after_this_request, current_app, jsonify, render_template, request, send_file
from flask_login import current_user

from crypto import decrypt_api_key
from extensions import limiter
from models import ApiKey
from games.crossword.clues import get_clues
from games.crossword.generator import build_best
from games.crossword.pdf_export import export_batch_pdf as export_crossword_batch
from games.sudoku.generator import DIFFICULTY_GIVENS, SudokuPuzzle
from games.sudoku.pdf_export import export_batch_pdf as export_sudoku_batch
from games.word_scramble.generator import WordScramblePuzzle
from games.word_scramble.pdf_export import export_batch_pdf as export_scramble_batch
from games.word_search.generator import WordSearchPuzzle
from games.word_search.pdf_export import export_batch_pdf as export_search_batch
from games.wordlists import get_word_list

batch_bp = Blueprint("batch", __name__, url_prefix="/batch")

MAX_THEMES = 20
MAX_SUDOKU_COUNT = 20
MAX_PER_THEME = 5
MAX_THEMED_PUZZLES = 60
THEMED_GAME_TYPES = ("word_search", "word_scramble", "crossword")


def _resolve_api_key():
    if current_user.is_authenticated:
        row = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first()
        if row:
            return decrypt_api_key(row.encrypted_key)
        return None
    # Dev-only convenience: never active under gunicorn/production (app.debug
    # is only ever True via `python app.py`'s explicit debug=True).
    if current_app.debug:
        return os.environ.get("ANTHROPIC_API_KEY")
    return None


@batch_bp.route("/")
def index():
    has_api_key = False
    if current_user.is_authenticated:
        has_api_key = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first() is not None
    return render_template("batch/index.html", has_api_key=has_api_key)


@batch_bp.route("/generate", methods=["POST"])
@limiter.limit("5 per hour")
def generate():
    data = request.get_json(force=True) or {}
    game_type = data.get("game_type")
    book_title = (data.get("book_title") or "").strip()[:80] or None

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(path)
        except OSError:
            pass
        return response

    if game_type == "sudoku":
        difficulty = (data.get("difficulty") or "medium").strip().lower()
        if difficulty not in DIFFICULTY_GIVENS:
            difficulty = "medium"
        try:
            count = int(data.get("count", 10))
        except (TypeError, ValueError):
            count = 10
        count = max(1, min(MAX_SUDOKU_COUNT, count))

        puzzles = [SudokuPuzzle(difficulty).to_dict() for _ in range(count)]
        export_sudoku_batch(puzzles, path, title=book_title)
        filename = f"sudoku_{difficulty}_batch.pdf"

    elif game_type in THEMED_GAME_TYPES:
        raw_themes = data.get("themes") or []
        themes = [t.strip() for t in raw_themes if t and t.strip()][:MAX_THEMES]
        if not themes:
            return jsonify({"error": "Enter at least one theme, one per line."}), 400

        def _clamped(key, default, lo, hi):
            try:
                return max(lo, min(hi, int(data.get(key, default))))
            except (TypeError, ValueError):
                return default

        size = _clamped("size", 15, 8, 25)
        count = _clamped("count", 12, 5, 20)
        min_len = _clamped("min_len", 4, 3, 10)
        max_len = max(min_len, _clamped("max_len", 8, min_len, 12))
        per_theme = _clamped("per_theme", 1, 1, MAX_PER_THEME)
        if len(themes) * per_theme > MAX_THEMED_PUZZLES:
            per_theme = max(1, MAX_THEMED_PUZZLES // len(themes))

        api_key = _resolve_api_key()
        entries = []
        skipped = []
        for theme in themes:
            # Fetch a wider pool once per theme (not once per puzzle, to avoid
            # multiplying LLM calls) and sample a fresh subset per repeat, so
            # "puzzles per theme" gives different words, not just a reshuffled
            # grid of the same words.
            pool_size = min(count * per_theme, 40) if per_theme > 1 else count
            pool, _source = get_word_list(theme, count=pool_size, min_len=min_len, max_len=max_len, api_key=api_key)

            for i in range(per_theme):
                label = theme if per_theme == 1 else f"{theme} #{i + 1}"
                words = random.sample(pool, count) if per_theme > 1 and len(pool) > count else pool[:count]
                if game_type == "word_search":
                    entries.append((WordSearchPuzzle(words, size=size), label))
                elif game_type == "word_scramble":
                    entries.append((WordScramblePuzzle(words), label))
                else:  # crossword
                    puzzle = build_best(words)
                    if puzzle is None or len(puzzle.placements) < 3:
                        skipped.append(label)
                        continue
                    placed_words = [p.word for p in puzzle.placements]
                    clues, _clue_source = get_clues(placed_words, theme, api_key=api_key)
                    entries.append((puzzle.to_dict(clues), label))

        if not entries:
            return jsonify({"error": "Couldn't build any puzzles from those themes — try different ones."}), 400

        if game_type == "word_search":
            export_search_batch(entries, path, title=book_title)
        elif game_type == "word_scramble":
            export_scramble_batch(entries, path, title=book_title)
        else:
            export_crossword_batch(entries, path, title=book_title)
        filename = f"{game_type}_batch.pdf"

    else:
        return jsonify({"error": "Unknown game type."}), 400

    response = send_file(path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    if game_type in THEMED_GAME_TYPES and skipped:
        response.headers["X-Batch-Skipped"] = ", ".join(skipped)
    return response
