import os
import tempfile

from flask import Blueprint, after_this_request, jsonify, render_template, request, send_file

from extensions import db
from models import Puzzle
from games.word_search.generator import WordSearchPuzzle
from games.word_search.pdf_export import export_pdf
from games.wordlists import get_word_list

word_search_bp = Blueprint("word_search", __name__)


@word_search_bp.route("/")
def index():
    return render_template("word_search/index.html")


@word_search_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True) or {}
    theme = (data.get("theme") or "").strip()
    size = int(data.get("size", 15))
    count = int(data.get("count", 12))

    if not theme:
        return jsonify({"error": "Please enter a theme."}), 400
    size = max(8, min(25, size))
    count = max(5, min(20, count))

    words, source = get_word_list(theme, count=count)

    puzzle = WordSearchPuzzle(words, size=size)

    row = Puzzle(
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
def download(puzzle_id):
    row = Puzzle.query.get(puzzle_id)
    if row is None:
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
