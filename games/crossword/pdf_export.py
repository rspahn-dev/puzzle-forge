"""Print-ready PDF export: a puzzle page followed by an answer-key page."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from games.pdf_common import draw_cover_page

MARGIN = 0.7 * inch
CLUE_BLOCK_HEIGHT = 2.4 * inch
MAX_CELL = 0.42 * inch


def export_pdf(data: dict, theme: str, path: str):
    c = canvas.Canvas(path, pagesize=letter)
    _draw_page(c, data, theme, show_answers=False)
    c.showPage()
    _draw_page(c, data, theme, show_answers=True)
    c.showPage()
    c.save()


def export_batch_pdf(entries: list[tuple], path: str):
    """entries: list of (puzzle_data, theme) pairs, puzzles first, answer key section after."""
    c = canvas.Canvas(path, pagesize=letter)
    draw_cover_page(c, "Crossword Puzzles", len(entries))
    for data, theme in entries:
        _draw_page(c, data, theme, show_answers=False)
        c.showPage()
    for data, theme in entries:
        _draw_page(c, data, theme, show_answers=True)
        c.showPage()
    c.save()


def _draw_page(c, data, theme, show_answers):
    width, height = letter
    rows, cols = data["rows"], data["cols"]
    blocks = data["blocks"]
    solution = data["solution"]
    numbers = data["numbers"]

    c.setFont("Helvetica-Bold", 18)
    title = f"Crossword: {theme}" + (" — Answer Key" if show_answers else "")
    c.drawCentredString(width / 2, height - 0.75 * inch, title)

    grid_top = height - 1.25 * inch
    grid_area_h = grid_top - MARGIN - CLUE_BLOCK_HEIGHT
    grid_area_w = width - 2 * MARGIN
    cell = min(grid_area_w / cols, grid_area_h / rows, MAX_CELL)
    grid_left = (width - cell * cols) / 2

    c.setLineWidth(0.6)
    for r in range(rows):
        for col in range(cols):
            x = grid_left + col * cell
            y = grid_top - (r + 1) * cell
            if not blocks[r][col]:
                c.setFillColorRGB(0.15, 0.15, 0.15)
                c.rect(x, y, cell, cell, fill=1, stroke=0)
                continue
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(x, y, cell, cell, fill=1, stroke=1)
            num = numbers.get(f"{r},{col}")
            if num:
                c.setFont("Helvetica", max(5, cell * 0.24))
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x + cell * 0.08, y + cell * 0.66, str(num))
            if show_answers:
                c.setFont("Helvetica-Bold", max(7, cell * 0.5))
                c.setFillColorRGB(0.18, 0.43, 0.31)
                c.drawCentredString(x + cell / 2, y + cell * 0.22, solution[r][col])
            c.setFillColorRGB(0, 0, 0)

    clues_top = grid_top - rows * cell - 0.35 * inch
    col_width = (width - 2 * MARGIN) / 2

    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, clues_top, "Across")
    c.drawString(MARGIN + col_width, clues_top, "Down")

    line_h = 0.16 * inch
    font_size = 8.2
    for entries, x in ((data["across"], MARGIN), (data["down"], MARGIN + col_width)):
        y = clues_top - 0.22 * inch
        c.setFont("Helvetica", font_size)
        for e in entries:
            text = f'{e["number"]}. {e["clue"]}'
            c.drawString(x, y, _truncate(c, text, col_width - 0.3 * inch, "Helvetica", font_size))
            y -= line_h
            if y < MARGIN * 0.6:
                break


def _truncate(c, text, max_width, font, size):
    if c.stringWidth(text, font, size) <= max_width:
        return text
    while text and c.stringWidth(text + "…", font, size) > max_width:
        text = text[:-1]
    return text + "…"
