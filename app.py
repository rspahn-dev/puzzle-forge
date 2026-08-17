import os
import tempfile

from dotenv import load_dotenv
from flask import Flask, after_this_request, jsonify, render_template, request, send_file

load_dotenv()

from config import Config
from extensions import db, migrate
from models import Puzzle
from wordsearch.generator import WordSearchPuzzle
from wordsearch.pdf_export import export_pdf
from wordsearch.themes import get_word_list

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
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


@app.route("/download/<puzzle_id>.pdf")
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
