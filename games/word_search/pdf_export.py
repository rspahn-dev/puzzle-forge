"""Print-ready PDF export: a puzzle page followed by an answer-key page."""
from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from games.pdf_common import draw_cover_page

MARGIN = 0.7 * inch


def export_pdf(puzzle, theme: str, path: str):
    c = canvas.Canvas(path, pagesize=letter)
    _draw_page(c, puzzle, theme, show_answers=False)
    c.showPage()
    _draw_page(c, puzzle, theme, show_answers=True)
    c.showPage()
    c.save()


def export_batch_pdf(entries: list[tuple], path: str, title: str | None = None):
    """entries: list of (WordSearchPuzzle, theme) pairs, puzzles first, answer key section after."""
    c = canvas.Canvas(path, pagesize=letter)
    draw_cover_page(c, title or "Word Search Puzzles", len(entries), show_credit=title is None)
    for puzzle, theme in entries:
        _draw_page(c, puzzle, theme, show_answers=False)
        c.showPage()
    for puzzle, theme in entries:
        _draw_page(c, puzzle, theme, show_answers=True)
        c.showPage()
    c.save()


def _draw_page(c, puzzle, theme, show_answers):
    width, height = letter
    size = puzzle.size

    c.setFont("Helvetica-Bold", 18)
    title = f"Word Search: {theme}" + (" — Answer Key" if show_answers else "")
    c.drawCentredString(width / 2, height - 0.75 * inch, title)

    word_list = sorted(w.word for w in puzzle.placements) if show_answers else sorted(puzzle.words)
    word_block_height = 1.6 * inch
    grid_top = height - 1.3 * inch
    grid_area_h = grid_top - MARGIN - word_block_height
    grid_area_w = width - 2 * MARGIN
    cell = min(grid_area_w, grid_area_h) / size
    grid_left = (width - cell * size) / 2

    if show_answers:
        answer_cells = set()
        for p in puzzle.placements:
            answer_cells.update(p.cells)

    c.setLineWidth(0.5)
    font_size = max(7, min(14, cell * 0.55))
    c.setFont("Helvetica", font_size)
    for r in range(size):
        for col in range(size):
            x = grid_left + col * cell
            y = grid_top - (r + 1) * cell
            if show_answers and (r, col) in answer_cells:
                c.setFillColorRGB(0.82, 0.89, 1.0)
                c.rect(x, y, cell, cell, fill=1, stroke=0)
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.rect(x, y, cell, cell, fill=0, stroke=1)
            c.setFillColorRGB(0, 0, 0)
            c.drawCentredString(x + cell / 2, y + cell * 0.28, puzzle.grid[r][col])

    words_top = grid_top - cell * size - 0.35 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN, words_top, "Find these words:")

    c.setFont("Helvetica", 10.5)
    cols = 4
    col_width = (width - 2 * MARGIN) / cols
    row_height = 0.22 * inch
    start_y = words_top - 0.3 * inch
    for i, word in enumerate(word_list):
        col_i = i % cols
        row_i = i // cols
        x = MARGIN + col_i * col_width
        y = start_y - row_i * row_height
        c.drawString(x, y, word)

    if puzzle.skipped:
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(MARGIN, MARGIN * 0.5, f"Not placed (grid too small): {', '.join(puzzle.skipped)}")
        c.setFillColorRGB(0, 0, 0)
