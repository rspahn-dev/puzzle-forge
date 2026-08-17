import os
import tempfile
import uuid

from dotenv import load_dotenv
from flask import Flask, after_this_request, jsonify, render_template, request, send_file

load_dotenv()

from wordsearch.generator import WordSearchPuzzle
from wordsearch.pdf_export import export_pdf
from wordsearch.themes import get_word_list

app = Flask(__name__)

# In-memory store so a browser can request a PDF right after generating a
# puzzle, without re-running the LLM call. Fine for a single-process MVP.
_puzzles = {}


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
    puzzle_id = str(uuid.uuid4())
    _puzzles[puzzle_id] = (puzzle, theme)

    result = puzzle.to_dict()
    result["puzzle_id"] = puzzle_id
    result["source"] = source
    return jsonify(result)


@app.route("/download/<puzzle_id>.pdf")
def download(puzzle_id):
    entry = _puzzles.get(puzzle_id)
    if entry is None:
        return "Puzzle not found — generate a new one.", 404
    puzzle, theme = entry

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
