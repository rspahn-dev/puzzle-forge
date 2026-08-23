import os
import tempfile

from flask import Blueprint, after_this_request, current_app, jsonify, render_template, request, send_file
from flask_login import current_user

from crypto import decrypt_api_key
from extensions import db, limiter
from models import ApiKey, Puzzle
from games.word_scramble.generator import WordScramblePuzzle
from games.word_scramble.pdf_export import export_pdf
from games.wordlists import get_word_list

word_scramble_bp = Blueprint("word_scramble", __name__, url_prefix="/word-scramble")


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


@word_scramble_bp.route("/")
def index():
    has_api_key = False
    if current_user.is_authenticated:
        has_api_key = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first() is not None
    return render_template("word_scramble/index.html", has_api_key=has_api_key)


@word_scramble_bp.route("/generate", methods=["POST"])
@limiter.limit("20 per hour")
def generate():
    data = request.get_json(force=True) or {}
    theme = (data.get("theme") or "").strip()
    count = int(data.get("count", 10))
    min_len = int(data.get("min_len", 4))
    max_len = int(data.get("max_len", 8))

    if not theme:
        return jsonify({"error": "Please enter a theme."}), 400
    count = max(5, min(20, count))
    min_len = max(3, min(10, min_len))
    max_len = max(min_len, min(12, max_len))

    api_key = _resolve_api_key()
    words, source = get_word_list(theme, count=count, min_len=min_len, max_len=max_len, api_key=api_key)

    puzzle = WordScramblePuzzle(words)

    row = Puzzle(
        user_id=current_user.id if current_user.is_authenticated else None,
        game_type="word_scramble",
        theme=theme,
        params={"count": count, "min_len": min_len, "max_len": max_len},
        data=puzzle.to_storage_dict(),
        source=source,
    )
    db.session.add(row)
    db.session.commit()

    result = puzzle.to_dict()
    result["puzzle_id"] = row.id
    result["source"] = source
    return jsonify(result)


@word_scramble_bp.route("/download/<puzzle_id>.pdf")
@limiter.limit("40 per hour")
def download(puzzle_id):
    row = Puzzle.query.get(puzzle_id)
    if row is None or row.game_type != "word_scramble":
        return "Puzzle not found — generate a new one.", 404
    puzzle = WordScramblePuzzle.from_items(row.data["items"])
    theme = row.theme

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    export_pdf(puzzle, theme, path)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(path)
        except OSError:
            pass
        return response

    safe_theme = "".join(ch if ch.isalnum() else "_" for ch in theme.lower())
    return send_file(path, as_attachment=True, download_name=f"word_scramble_{safe_theme}.pdf")
