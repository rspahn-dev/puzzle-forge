"""Core crossword grid generation — no external dependencies.

Greedily places the longest words first, then threads each remaining word
through a matching letter on an already-placed word (perpendicular to it),
skipping any word that can't be connected to the grid.
"""
import random

ACROSS = (0, 1)
DOWN = (1, 0)


class PlacedWord:
    def __init__(self, word, row, col, direction):
        self.word = word
        self.row = row
        self.col = col
        self.direction = direction
        self.number = None

    @property
    def is_across(self):
        return self.direction == ACROSS

    @property
    def cells(self):
        dr, dc = self.direction
        return [(self.row + i * dr, self.col + i * dc) for i in range(len(self.word))]


class CrosswordPuzzle:
    def __init__(self, words, seed=None):
        self.words = self._dedupe(words)
        self._rng = random.Random(seed)
        self.grid = {}
        self.placements = []
        self.skipped = []
        self.rows = 0
        self.cols = 0
        self._generate()
        self._normalize()
        self._assign_numbers()

    @staticmethod
    def _dedupe(words):
        seen = set()
        cleaned = []
        for w in words:
            cleaned_word = "".join(ch for ch in w.upper().strip() if ch.isalpha())
            if cleaned_word and cleaned_word not in seen:
                seen.add(cleaned_word)
                cleaned.append(cleaned_word)
        return cleaned

    def _generate(self):
        if not self.words:
            return
        ordered = sorted(self.words, key=lambda w: (-len(w), self._rng.random()))
        self._place(ordered[0], 0, 0, ACROSS)
        for word in ordered[1:]:
            if not self._place_intersecting(word):
                self.skipped.append(word)

    def _place(self, word, row, col, direction):
        dr, dc = direction
        for i, ch in enumerate(word):
            self.grid[(row + i * dr, col + i * dc)] = ch
        self.placements.append(PlacedWord(word, row, col, direction))

    def _can_place(self, word, row, col, direction):
        dr, dc = direction
        n = len(word)
        cells = [(row + i * dr, col + i * dc) for i in range(n)]
        before = (row - dr, col - dc)
        after = (row + n * dr, col + n * dc)
        if before in self.grid or after in self.grid:
            return False
        has_intersection = False
        pr, pc = dc, dr  # perpendicular unit step
        for i, (r, c) in enumerate(cells):
            existing = self.grid.get((r, c))
            if existing is not None:
                if existing != word[i]:
                    return False
                has_intersection = True
            elif (r + pr, c + pc) in self.grid or (r - pr, c - pc) in self.grid:
                return False
        return has_intersection

    def _place_intersecting(self, word):
        candidates = []
        for placement in self.placements:
            other_dir = DOWN if placement.is_across else ACROSS
            dr, dc = other_dir
            for i, ch in enumerate(word):
                for j, existing_ch in enumerate(placement.word):
                    if ch != existing_ch:
                        continue
                    r, c = placement.cells[j]
                    candidates.append((r - i * dr, c - i * dc, other_dir))
        self._rng.shuffle(candidates)
        for row, col, direction in candidates:
            if self._can_place(word, row, col, direction):
                self._place(word, row, col, direction)
                return True
        return False

    def _normalize(self):
        if not self.grid:
            return
        min_r = min(r for r, c in self.grid)
        min_c = min(c for r, c in self.grid)
        if min_r or min_c:
            self.grid = {(r - min_r, c - min_c): ch for (r, c), ch in self.grid.items()}
            for p in self.placements:
                p.row -= min_r
                p.col -= min_c
        self.rows = max(r for r, c in self.grid) + 1
        self.cols = max(c for r, c in self.grid) + 1

    def _assign_numbers(self):
        starts = {}
        for p in self.placements:
            starts.setdefault((p.row, p.col), []).append(p)
        number = 1
        for r, c in sorted(starts):
            for p in starts[(r, c)]:
                p.number = number
            number += 1

    def to_dict(self, clues=None):
        clues = clues or {}
        cells = [[None] * self.cols for _ in range(self.rows)]
        for (r, c), ch in self.grid.items():
            cells[r][c] = ch
        blocks = [[cells[r][c] is not None for c in range(self.cols)] for r in range(self.rows)]
        numbers = {f"{p.row},{p.col}": p.number for p in self.placements}

        def entry(p):
            return {
                "number": p.number,
                "row": p.row,
                "col": p.col,
                "length": len(p.word),
                "answer": p.word,
                "clue": clues.get(p.word, ""),
            }

        across = sorted((entry(p) for p in self.placements if p.is_across), key=lambda e: e["number"])
        down = sorted((entry(p) for p in self.placements if not p.is_across), key=lambda e: e["number"])

        return {
            "rows": self.rows,
            "cols": self.cols,
            "blocks": blocks,
            "solution": cells,
            "numbers": numbers,
            "across": across,
            "down": down,
            "skipped": self.skipped,
        }


def build_best(words, attempts=6, seed=None):
    """Try a few random layouts and keep the one that places the most words."""
    rng = random.Random(seed)
    best = None
    for _ in range(attempts):
        candidate = CrosswordPuzzle(words, seed=rng.random())
        if best is None or len(candidate.placements) > len(best.placements):
            best = candidate
        if not candidate.skipped:
            break
    return best
