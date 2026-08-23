"""Print-ready PDF export: a puzzle page followed by an answer-key page."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

MARGIN = 0.7 * inch
SIZE = 9
BOX = 3


def export_pdf(data: dict, path: str):
    c = canvas.Canvas(path, pagesize=letter)
    _draw_page(c, data, show_answers=False)
    c.showPage()
    _draw_page(c, data, show_answers=True)
    c.showPage()
    c.save()


def _draw_page(c, data, show_answers):
    width, height = letter
    difficulty = data["difficulty"].capitalize()

    c.setFont("Helvetica-Bold", 18)
    title = f"Sudoku ({difficulty})" + (" — Answer Key" if show_answers else "")
    c.drawCentredString(width / 2, height - 0.9 * inch, title)

    grid_area = min(width - 2 * MARGIN, height - 2.4 * inch)
    cell = grid_area / SIZE
    grid_left = (width - cell * SIZE) / 2
    grid_top = height - 1.5 * inch

    puzzle = data["puzzle"]
    solution = data["solution"]

    c.setFont("Helvetica", cell * 0.5)
    for r in range(SIZE):
        for col in range(SIZE):
            x = grid_left + col * cell
            y = grid_top - (r + 1) * cell
            given = puzzle[r][col]
            if show_answers:
                c.setFillColorRGB(0, 0, 0) if given else c.setFillColorRGB(0.18, 0.43, 0.31)
                c.drawCentredString(x + cell / 2, y + cell * 0.28, str(solution[r][col]))
                c.setFillColorRGB(0, 0, 0)
            elif given:
                c.setFillColorRGB(0, 0, 0)
                c.drawCentredString(x + cell / 2, y + cell * 0.28, str(given))

    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.5)
    for i in range(SIZE + 1):
        x = grid_left + i * cell
        c.line(x, grid_top - SIZE * cell, x, grid_top)
    for i in range(SIZE + 1):
        y = grid_top - i * cell
        c.line(grid_left, y, grid_left + SIZE * cell, y)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1.6)
    for i in range(0, SIZE + 1, BOX):
        x = grid_left + i * cell
        c.line(x, grid_top - SIZE * cell, x, grid_top)
        y = grid_top - i * cell
        c.line(grid_left, y, grid_left + SIZE * cell, y)
