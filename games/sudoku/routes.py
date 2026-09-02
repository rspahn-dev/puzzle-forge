import os
import tempfile

from flask import Blueprint, after_this_request, jsonify, render_template, request, send_file
from flask_login import current_user

from extensions import db, limiter
from games.access import anon_generation_gate
from models import Puzzle
from games.sudoku.generator import DIFFICULTY_GIVENS, SudokuPuzzle
from games.sudoku.pdf_export import export_pdf

sudoku_bp = Blueprint("sudoku", __name__, url_prefix="/sudoku")


@sudoku_bp.route("/")
def index():
    return render_template("sudoku/index.html")


@sudoku_bp.route("/generate", methods=["POST"])
@limiter.limit("60 per hour")
def generate():
    data = request.get_json(force=True) or {}
    difficulty = (data.get("difficulty") or "medium").strip().lower()
    if difficulty not in DIFFICULTY_GIVENS:
        difficulty = "medium"

    gate_response = anon_generation_gate()
    if gate_response:
        return gate_response

    puzzle = SudokuPuzzle(difficulty)
    result = puzzle.to_dict()

    row = Puzzle(
        user_id=current_user.id if current_user.is_authenticated else None,
        game_type="sudoku",
        params={"difficulty": difficulty},
        data=result,
    )
    db.session.add(row)
    db.session.commit()

    result["puzzle_id"] = row.id
    return jsonify(result)


@sudoku_bp.route("/download/<puzzle_id>.pdf")
@limiter.limit("40 per hour")
def download(puzzle_id):
    row = Puzzle.query.get(puzzle_id)
    if row is None or row.game_type != "sudoku":
        return "Puzzle not found — generate a new one.", 404

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    export_pdf(row.data, path)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(path)
        except OSError:
            pass
        return response

    difficulty = row.data.get("difficulty", "sudoku")
    return send_file(path, as_attachment=True, download_name=f"sudoku_{difficulty}.pdf")
