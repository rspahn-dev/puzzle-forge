"""Core word search grid generation — no external dependencies."""
import random
import string

DIRECTIONS = [
    (0, 1), (0, -1), (1, 0), (-1, 0),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]


class PlacedWord:
    def __init__(self, word, row, col, dr, dc):
        self.word = word
        self.row = row
        self.col = col
        self.dr = dr
        self.dc = dc

    @property
    def cells(self):
        return [(self.row + i * self.dr, self.col + i * self.dc) for i in range(len(self.word))]


class WordSearchPuzzle:
    def __init__(self, words, size=15, seed=None):
        self.size = size
        self.words = [w.upper().strip() for w in words if w.strip()]
        self.grid = [[None] * size for _ in range(size)]
        self.placements = []
        self.skipped = []
        self._rng = random.Random(seed)
        self._generate()

    def _generate(self):
        for word in sorted(self.words, key=len, reverse=True):
            if not self._place_word(word):
                self.skipped.append(word)
        self._fill_blanks()

    def _place_word(self, word, attempts=200):
        n = len(word)
        if n > self.size:
            return False
        for _ in range(attempts):
            dr, dc = self._rng.choice(DIRECTIONS)
            row = self._rng.randrange(self.size)
            col = self._rng.randrange(self.size)
            end_row = row + dr * (n - 1)
            end_col = col + dc * (n - 1)
            if not (0 <= end_row < self.size and 0 <= end_col < self.size):
                continue
            cells = [(row + i * dr, col + i * dc) for i in range(n)]
            if all(self.grid[r][c] in (None, word[i]) for i, (r, c) in enumerate(cells)):
                for i, (r, c) in enumerate(cells):
                    self.grid[r][c] = word[i]
                self.placements.append(PlacedWord(word, row, col, dr, dc))
                return True
        return False

    def _fill_blanks(self):
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    self.grid[r][c] = self._rng.choice(string.ascii_uppercase)

    def to_dict(self):
        return {
            "size": self.size,
            "grid": self.grid,
            "words": sorted(self.words),
            "skipped": self.skipped,
        }
