import os
import tempfile

from flask import Blueprint, after_this_request, current_app, jsonify, render_template, request, send_file
from flask_login import current_user

from crypto import decrypt_api_key
from extensions import db, limiter
from games.access import anon_generation_gate
from models import ApiKey, Puzzle
from games.word_search.generator import WordSearchPuzzle
from games.word_search.pdf_export import export_pdf
from games.wordlists import get_word_list

word_search_bp = Blueprint("word_search", __name__)


def _resolve_api_key():
    if current_user.is_authenticated:
        if current_user.prefer_offline_wordbank:
            return None
        row = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first()
        if row:
            return decrypt_api_key(row.encrypted_key)
        return None
    # Dev-only convenience: never active under gunicorn/production (app.debug
    # is only ever True via `python app.py`'s explicit debug=True).
    if current_app.debug:
        return os.environ.get("ANTHROPIC_API_KEY")
    return None


@word_search_bp.route("/")
def index():
    has_api_key = False
    prefer_offline = False
    if current_user.is_authenticated:
        has_api_key = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first() is not None
        prefer_offline = current_user.prefer_offline_wordbank
    return render_template("word_search/index.html", has_api_key=has_api_key, prefer_offline=prefer_offline)


@word_search_bp.route("/generate", methods=["POST"])
@limiter.limit("20 per hour")
def generate():
    data = request.get_json(force=True) or {}
    theme = (data.get("theme") or "").strip()
    size = int(data.get("size", 15))
    count = int(data.get("count", 12))

    if not theme:
        return jsonify({"error": "Please enter a theme."}), 400
    size = max(8, min(25, size))
    count = max(5, min(20, count))

    gate_response = anon_generation_gate()
    if gate_response:
        return gate_response

    api_key = _resolve_api_key()
    words, source = get_word_list(theme, count=count, api_key=api_key)

    puzzle = WordSearchPuzzle(words, size=size)

    row = Puzzle(
        user_id=current_user.id if current_user.is_authenticated else None,
        game_type="word_search",
        theme=theme,
        params={"size": size, "count": count},
        data=puzzle.to_storage_dict(),
        source=source,
    )
    db.session.add(row)
    db.session.commit()

    result = puzzle.to_dict()
    result["puzzle_id"] = row.id
    result["source"] = source
    return jsonify(result)


@word_search_bp.route("/download/<puzzle_id>.pdf")
@limiter.limit("40 per hour")
def download(puzzle_id):
    row = Puzzle.query.get(puzzle_id)
    if row is None or row.game_type != "word_search":
        return "Puzzle not found — generate a new one.", 404
    puzzle = WordSearchPuzzle.from_placements(**row.data)
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
    return send_file(path, as_attachment=True, download_name=f"word_search_{safe_theme}.pdf")
