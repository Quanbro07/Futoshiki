"""
Automatically generate Futoshiki test cases with sizes 4x4, 5x5, 6x6, 7x7, and 9x9.

Goal: generate puzzles that (as much as possible) have a unique solution.
"""

import random
from copy import deepcopy
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from state.Board import Board
from state.PuzzleContext import PuzzleContext

# Generate a valid solution for a Sudoku puzzle
def generate_solution(n, seed=None):
    if seed is not None:
        random.seed(seed)

    base = list(range(1, n + 1))
    grid = []
    for i in range(n):
        row = base[i:] + base[:i]
        grid.append(row)

    rows = list(range(n))
    random.shuffle(rows)
    grid = [grid[r] for r in rows]

    cols = list(range(n))
    random.shuffle(cols)
    grid = [[row[c] for c in cols] for row in grid]

    perm = list(range(1, n + 1))
    random.shuffle(perm)
    mapping = {i + 1: perm[i] for i in range(n)}
    grid = [[mapping[cell] for cell in row] for row in grid]
    return grid


# Generate constraints for a Sudoku puzzle
def generate_constraints(solution, n , density=0.4, seed=None):
    if seed is not None:
        random.seed(seed)

        h_cons = [[0] * (n - 1) for _ in range(n)]
        v_cons = [[0] * n for _ in range(n - 1)]

        # Horizontal constraints
        for i in range(n):
            for j in range(n - 1):
                if random.random() < density:
                    left = solution[i][j]
                    right = solution[i][j + 1]
                    h_cons[i][j] = 1 if left < right else -1

        # Vertical constraints
        for i in range(n - 1):
            for j in range(n):
                if random.random() < density:
                    top = solution[i][j]
                    bot = solution[i + 1][j]
                    v_cons[i][j] = 1 if top < bot else -1

        return h_cons, v_cons
    


# Generate the given clues for a Sudoku puzzle
def generate_givens(solution, n, ratio=0.3, seed=None):
    if seed is not None:
        random.seed(seed)

    min_givens = max(n, int(n * n * ratio))
    total_cells = [(i,j) for i in range(n) for j in range(n)]
    random.shuffle(total_cells)
    chosen = set(total_cells[:min_givens])

    puzzle = [[0] * n for _ in range(n)]
    for (i, j) in chosen:
        puzzle[i][j] = solution[i][j]
    return puzzle


# Write input files for the generated test cases
def write_input_file(filepath, n, puzzle, h_cons, v_cons):
    lines = []
    lines.append(str(n))

    # Grid
    for i in range(n):
        lines.append(', '.join(str(puzzle[i][j]) for j in range(n)))

    # Horizontal constraints
    for i in range(n):
        lines.append(', '.join(str(h_cons[i][j]) for j in range(n - 1)))

    # Vertical constraints
    for i in range(n - 1):
        lines.append(', '.join(str(v_cons[i][j]) for j in range(n)))
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines) + '\n')


# Verify constraints match the solution
def verify_constraints(solution, h_cons, v_cons, n):
    for i in range(n):
        for j in range(n - 1):
            c = h_cons[i][j]
            if c == 1 and not (solution[i][j] < solution[i][j + 1]):
                return False
            if c == -1 and not (solution[i][j] > solution[i][j + 1]):
                return False
    for i in range(n - 1):
        for j in range(n):
            c = v_cons[i][j]
            if c == 1 and not (solution[i][j] < solution[i + 1][j]):
                return False
            if c == -1 and not (solution[i][j] > solution[i + 1][j]):
                return False
    return True



# Check uniqueness of the solution using backtracking

def build_board_from_puzzle(n, puzzle, h_cons, v_cons):
    """Convert matrix-form puzzle + constraints (-1/0/1) to Board/PuzzleContext."""
    given = {}
    for i in range(n):
        for j in range(n):
            val = puzzle[i][j]
            if val != 0:
                # Board/PuzzleContext uses 1-based indices
                given[(i + 1, j + 1)] = val

    less_h, greater_h = set(), set()
    for i in range(n):
        for j in range(n - 1):
            c = h_cons[i][j]
            if c == 1:
                less_h.add((i + 1, j + 1))
            elif c == -1:
                greater_h.add((i + 1, j + 1))

    less_v, greater_v = set(), set()
    for i in range(n - 1):
        for j in range(n):
            c = v_cons[i][j]
            if c == 1:
                less_v.add((i + 1, j + 1))
            elif c == -1:
                greater_v.add((i + 1, j + 1))

    context = PuzzleContext(n, given, less_h, greater_h, less_v, greater_v)
    board = Board(dict(given), context)
    return board


def count_solutions(board: Board, limit: int = 2, max_nodes: int = 200_000) -> int:
    """Count number of solutions (up to ``limit``) with a safety node limit.

    ``max_nodes`` bounds the total number of recursive nodes explored so that
    large 9x9 instances cannot run indefinitely. If the search hits
    ``max_nodes``, we conservatively return ``limit`` (">= limit solutions").
    """
    empty_cells = board.get_empty_cells()
    nodes_visited = 0

    def dfs(idx: int) -> int:
        nonlocal nodes_visited
        # Count this recursive node and enforce the safety cutoff.
        nodes_visited += 1
        if nodes_visited >= max_nodes:
            # Treat this as "at least ``limit`` solutions" to stop search.
            return limit

        if idx == len(empty_cells):
            return 1

        i, j = empty_cells[idx]
        total = 0
        for v in board.get_valid_values(i, j):
            board.assign_value(i, j, v)
            total += dfs(idx + 1)
            board.unassign_value(i, j)
            if total >= limit or nodes_visited >= max_nodes:
                break
        return total

    return dfs(0)


def has_unique_solution(n, puzzle, h_cons, v_cons) -> bool:
    """Return True if the puzzle has exactly 1 solution, False otherwise."""
    board = build_board_from_puzzle(n, puzzle, h_cons, v_cons)
    # Use a higher node limit for larger boards; tweak if needed.
    max_nodes = 50_000 if n <= 7 else 200_000
    num = count_solutions(board, limit=2, max_nodes=max_nodes)
    return num == 1


"""
Configuration for 20 test cases with different sizes and densities

(size, density, ratio, seed)
density: probability of placing a constraint
ratio: percentage of given clues
multiple difficulties: easy (more givens, more constraints), medium (balanced), hard (fewer givens, fewer constraints)
"""

TEST_CONFIGS = [
    # 4x4 — 4 cases
    (4, 0.6, 0.45, 42),    # 01: easy
    (4, 0.4, 0.30, 77),    # 02: medium
    (4, 0.3, 0.20, 13),    # 03: hard
    (4, 0.5, 0.35, 99),    # 04: easy-medium
 
    # 5x5 — 4 cases
    (5, 0.6, 0.45, 11),    # 05: easy
    (5, 0.4, 0.30, 55),    # 06: medium
    (5, 0.3, 0.20, 23),    # 07: hard
    (5, 0.5, 0.35, 88),    # 08: easy-medium
 
    # 6x6 — 4 cases
    (6, 0.55, 0.40, 31),   # 09: easy
    (6, 0.40, 0.28, 64),   # 10: medium
    (6, 0.30, 0.18, 17),   # 11: hard
    (6, 0.45, 0.32, 72),   # 12: medium
 
    # 7x7 — 4 cases
    (7, 0.50, 0.38, 19),   # 13: easy
    (7, 0.38, 0.25, 83),   # 14: medium
    (7, 0.28, 0.16, 37),   # 15: hard
    (7, 0.42, 0.30, 56),   # 16: medium
 
    # 9x9 — 4 cases
    (9, 0.45, 0.35, 29),   # 17: easy
    (9, 0.35, 0.22, 19),   # 18: medium - 40 attempts
    (9, 0.25, 0.14, 47),   # 19: hard - NON-UNIQUE fallback after 40 attempts
    (9, 0.40, 0.28, 44),   # 20: medium
]


def main():
    output_dir = "Inputs"
    os.makedirs(output_dir, exist_ok=True)
 
    print("Generating 20 Futoshiki test cases...\n")
 
    for idx, (n, density, ratio, seed) in enumerate(TEST_CONFIGS, start=1):
        # Try to find a testcase with a unique solution (or stop after max_tries)
        max_tries = 40
        attempt = 0
        unique = False

        while attempt < max_tries and not unique:
            cur_seed = seed + attempt * 1000

            solution = generate_solution(n, seed=cur_seed)

            h_cons, v_cons = generate_constraints(solution, n, density=density, seed=cur_seed + 1)

            puzzle = generate_givens(solution, n, ratio=ratio, seed=cur_seed + 2)

            if not verify_constraints(solution, h_cons, v_cons, n):
                attempt += 1
                continue

            unique = has_unique_solution(n, puzzle, h_cons, v_cons)
            if not unique:
                attempt += 1

        if unique:
            filepath = os.path.join(output_dir, f"input-{idx:02d}.txt")
            write_input_file(filepath, n, puzzle, h_cons, v_cons)
            print(f"\nDone! Files saved to ./{output_dir}/")

        status = "UNIQUE" if unique else "NON-UNIQUE (fallback)"
        print(f"Test {idx:02d}: N={n}, density={density}, ratio={ratio} -> {status}, attempts={attempt + 1 if unique else attempt}")
 
    print("\nNote: The generator tries to create puzzles with a unique solution.")
    print("If some tests are still NON-UNIQUE, adjust the configs or increase max_tries.")
 
 
if __name__ == "__main__":
    main()    