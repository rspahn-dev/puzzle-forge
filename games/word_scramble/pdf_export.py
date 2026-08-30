"""Print-ready PDF export: a puzzle page followed by an answer-key page."""
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


def export_batch_pdf(entries: list[tuple], path: str):
    """entries: list of (WordScramblePuzzle, theme) pairs, puzzles first, answer key section after."""
    c = canvas.Canvas(path, pagesize=letter)
    draw_cover_page(c, "Word Scramble Puzzles", len(entries))
    for puzzle, theme in entries:
        _draw_page(c, puzzle, theme, show_answers=False)
        c.showPage()
    for puzzle, theme in entries:
        _draw_page(c, puzzle, theme, show_answers=True)
        c.showPage()
    c.save()


def _draw_page(c, puzzle, theme, show_answers):
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    title = f"Word Scramble: {theme}" + (" — Answer Key" if show_answers else "")
    c.drawCentredString(width / 2, height - 0.75 * inch, title)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(width / 2, height - 1.05 * inch, "Unscramble each word.")
    c.setFillColorRGB(0, 0, 0)

    row_height = 0.5 * inch
    top = height - 1.6 * inch
    col_width = (width - 2 * MARGIN) / 2
    rows_per_col = int((top - MARGIN) / row_height)

    for i, item in enumerate(puzzle.items):
        col = i // rows_per_col
        row = i % rows_per_col
        x = MARGIN + col * col_width
        y = top - row * row_height

        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, f"{i + 1}. {item.scrambled}")

        if show_answers:
            c.setFont("Helvetica", 12)
            c.setFillColorRGB(0.18, 0.43, 0.31)
            c.drawString(x, y - 0.24 * inch, item.answer)
            c.setFillColorRGB(0, 0, 0)
        else:
            c.setLineWidth(0.7)
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            line_y = y - 0.22 * inch
            c.line(x, line_y, x + col_width - 0.4 * inch, line_y)
