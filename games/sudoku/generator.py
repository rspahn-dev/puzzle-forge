"""Core sudoku generation — no external dependencies.

Fills a full grid via randomized backtracking, then removes cells one at
a time (in random order), keeping a removal only if the puzzle still has
exactly one solution.
"""
import random

SIZE = 9
BOX = 3

DIFFICULTY_GIVENS = {
    "easy": 42,
    "medium": 32,
    "hard": 26,
}


def _find_empty(grid):
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == 0:
                return r, c
    return None


def _candidates(grid, r, c):
    used = set(grid[r])
    used.update(grid[i][c] for i in range(SIZE))
    br, bc = (r // BOX) * BOX, (c // BOX) * BOX
    for i in range(br, br + BOX):
        for j in range(bc, bc + BOX):
            used.add(grid[i][j])
    return [n for n in range(1, 10) if n not in used]


def _solve_random(grid, rng):
    pos = _find_empty(grid)
    if pos is None:
        return True
    r, c = pos
    cands = _candidates(grid, r, c)
    rng.shuffle(cands)
    for n in cands:
        grid[r][c] = n
        if _solve_random(grid, rng):
            return True
        grid[r][c] = 0
    return False


def _count_solutions(grid, cap=2):
    pos = _find_empty(grid)
    if pos is None:
        return 1
    r, c = pos
    count = 0
    for n in _candidates(grid, r, c):
        grid[r][c] = n
        count += _count_solutions(grid, cap - count)
        grid[r][c] = 0
        if count >= cap:
            break
    return count


def generate_solution(rng):
    grid = [[0] * SIZE for _ in range(SIZE)]
    _solve_random(grid, rng)
    return grid


def make_puzzle(difficulty="medium", seed=None):
    rng = random.Random(seed)
    solution = generate_solution(rng)
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
    rng.shuffle(cells)
    target_givens = DIFFICULTY_GIVENS.get(difficulty, 32)
    givens = SIZE * SIZE

    for r, c in cells:
        if givens <= target_givens:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        probe = [row[:] for row in puzzle]
        if _count_solutions(probe, cap=2) == 1:
            givens -= 1
        else:
            puzzle[r][c] = backup

    return puzzle, solution


class SudokuPuzzle:
    def __init__(self, difficulty="medium", seed=None):
        self.difficulty = difficulty if difficulty in DIFFICULTY_GIVENS else "medium"
        self.puzzle, self.solution = make_puzzle(self.difficulty, seed=seed)

    def to_dict(self):
        return {
            "puzzle": self.puzzle,
            "solution": self.solution,
            "difficulty": self.difficulty,
        }
