import os
import tempfile

from flask import Blueprint, after_this_request, current_app, jsonify, render_template, request, send_file
from flask_login import current_user

from crypto import decrypt_api_key
from extensions import db, limiter
from games.access import anon_generation_gate
from models import ApiKey, Puzzle
from games.crossword.clues import get_clues
from games.crossword.generator import build_best
from games.crossword.pdf_export import export_pdf
from games.wordlists import get_word_list

crossword_bp = Blueprint("crossword", __name__, url_prefix="/crossword")


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


@crossword_bp.route("/")
def index():
    has_api_key = False
    prefer_offline = False
    if current_user.is_authenticated:
        has_api_key = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first() is not None
        prefer_offline = current_user.prefer_offline_wordbank
    return render_template("crossword/index.html", has_api_key=has_api_key, prefer_offline=prefer_offline)


@crossword_bp.route("/generate", methods=["POST"])
@limiter.limit("15 per hour")
def generate():
    data = request.get_json(force=True) or {}
    theme = (data.get("theme") or "").strip()
    count = int(data.get("count", 12))
    min_len = int(data.get("min_len", 4))
    max_len = int(data.get("max_len", 8))

    if not theme:
        return jsonify({"error": "Please enter a theme."}), 400
    count = max(6, min(18, count))
    min_len = max(3, min(10, min_len))
    max_len = max(min_len, min(12, max_len))

    gate_response = anon_generation_gate()
    if gate_response:
        return gate_response

    api_key = _resolve_api_key()
    words, word_source = get_word_list(theme, count=count, min_len=min_len, max_len=max_len, api_key=api_key)

    puzzle = build_best(words)
    if puzzle is None or len(puzzle.placements) < 3:
        return jsonify({"error": "Couldn't build a crossword from that theme — try a different one."}), 400

    placed_words = [p.word for p in puzzle.placements]
    clues, clue_source = get_clues(placed_words, theme, api_key=api_key)
    source = "llm" if word_source == "llm" and clue_source == "llm" else "offline"

    result = puzzle.to_dict(clues)

    row = Puzzle(
        user_id=current_user.id if current_user.is_authenticated else None,
        game_type="crossword",
        theme=theme,
        params={"count": count, "min_len": min_len, "max_len": max_len},
        data=result,
        source=source,
    )
    db.session.add(row)
    db.session.commit()

    result["puzzle_id"] = row.id
    result["source"] = source
    return jsonify(result)


@crossword_bp.route("/download/<puzzle_id>.pdf")
@limiter.limit("40 per hour")
def download(puzzle_id):
    row = Puzzle.query.get(puzzle_id)
    if row is None or row.game_type != "crossword":
        return "Puzzle not found — generate a new one.", 404
    theme = row.theme

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    export_pdf(row.data, theme, path)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(path)
        except OSError:
            pass
        return response

    safe_theme = "".join(ch if ch.isalnum() else "_" for ch in theme.lower())
    return send_file(path, as_attachment=True, download_name=f"crossword_{safe_theme}.pdf")
