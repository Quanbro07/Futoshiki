"""
Automatically generate Futoshiki test cases with sizes 4x4, 5x5, 6x6, 7x7, and 9x9.

Supports 3 types of test cases:
  - UNIQUE     : puzzle has exactly 1 solution (sufficient clues + constraints)
  - MULTIPLE   : puzzle has more than 1 solution (deliberately sparse clues)
  - NOSOLUTION : puzzle is unsolvable (contradictory constraints injected)
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


# ---------------------------------------------------------------------------
# Core generation functions for UNIQUE-solution puzzles
# ---------------------------------------------------------------------------

def generate_solution(n, seed=None):
    """Generate a valid Latin-square solution for an n×n Futoshiki grid."""
    if seed is not None:
        random.seed(seed)

    base = list(range(1, n + 1))
    grid = [base[i:] + base[:i] for i in range(n)]

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


def generate_constraints(solution, n, density=0.4, seed=None):
    """Generate inequality constraints derived from a valid solution."""
    if seed is not None:
        random.seed(seed)

    h_cons = [[0] * (n - 1) for _ in range(n)]
    v_cons = [[0] * n for _ in range(n - 1)]

    for i in range(n):
        for j in range(n - 1):
            if random.random() < density:
                h_cons[i][j] = 1 if solution[i][j] < solution[i][j + 1] else -1

    for i in range(n - 1):
        for j in range(n):
            if random.random() < density:
                v_cons[i][j] = 1 if solution[i][j] < solution[i + 1][j] else -1

    return h_cons, v_cons


def generate_givens(solution, n, ratio=0.3, seed=None):
    """Place a subset of solution values as given clues."""
    if seed is not None:
        random.seed(seed)

    min_givens = max(n, int(n * n * ratio))
    total_cells = [(i, j) for i in range(n) for j in range(n)]
    random.shuffle(total_cells)
    chosen = set(total_cells[:min_givens])

    puzzle = [[0] * n for _ in range(n)]
    for (i, j) in chosen:
        puzzle[i][j] = solution[i][j]
    return puzzle


def verify_constraints(solution, h_cons, v_cons, n):
    """Return True if all constraints are consistent with the given solution."""
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


# ---------------------------------------------------------------------------
# Helpers for MULTIPLE-solution puzzles
# ---------------------------------------------------------------------------

def generate_sparse_givens(solution, n, ratio=0.05, seed=None):
    if seed is not None:
        random.seed(seed)

    num_givens = max(1, int(n * n * ratio))
    total_cells = [(i, j) for i in range(n) for j in range(n)]
    random.shuffle(total_cells)
    chosen = set(total_cells[:num_givens])

    puzzle = [[0] * n for _ in range(n)]
    for (i, j) in chosen:
        puzzle[i][j] = solution[i][j]
    return puzzle


def generate_sparse_constraints(solution, n, density=0.05, seed=None):
    if seed is not None:
        random.seed(seed)

    h_cons = [[0] * (n - 1) for _ in range(n)]
    v_cons = [[0] * n for _ in range(n - 1)]

    for i in range(n):
        for j in range(n - 1):
            if random.random() < density:
                h_cons[i][j] = 1 if solution[i][j] < solution[i][j + 1] else -1

    for i in range(n - 1):
        for j in range(n):
            if random.random() < density:
                v_cons[i][j] = 1 if solution[i][j] < solution[i + 1][j] else -1

    return h_cons, v_cons


# ---------------------------------------------------------------------------
# Helpers for NO-SOLUTION puzzles
# ---------------------------------------------------------------------------

def inject_contradictory_constraints(solution, h_cons, v_cons, n, seed=None):
    if seed is not None:
        random.seed(seed)

    h = deepcopy(h_cons)
    v = deepcopy(v_cons)

    # Flip existing horizontal constraints
    h_positions = [(i, j) for i in range(n) for j in range(n - 1) if h[i][j] != 0]
    num_flip_h = max(1, len(h_positions) // 2)
    random.shuffle(h_positions)
    for i, j in h_positions[:num_flip_h]:
        h[i][j] = -h[i][j]

    # Flip existing vertical constraints
    v_positions = [(i, j) for i in range(n - 1) for j in range(n) if v[i][j] != 0]
    num_flip_v = max(1, len(v_positions) // 2)
    random.shuffle(v_positions)
    for i, j in v_positions[:num_flip_v]:
        v[i][j] = -v[i][j]

    # Inject extra wrong constraints in previously-empty horizontal slots
    empty_h = [(i, j) for i in range(n) for j in range(n - 1) if h[i][j] == 0]
    random.shuffle(empty_h)
    for i, j in empty_h[:max(2, n // 2)]:
        correct = 1 if solution[i][j] < solution[i][j + 1] else -1
        h[i][j] = -correct  # deliberately wrong direction

    # Inject extra wrong constraints in previously-empty vertical slots
    empty_v = [(i, j) for i in range(n - 1) for j in range(n) if v[i][j] == 0]
    random.shuffle(empty_v)
    for i, j in empty_v[:max(2, n // 2)]:
        correct = 1 if solution[i][j] < solution[i + 1][j] else -1
        v[i][j] = -correct  # deliberately wrong direction

    return h, v


def inject_contradictory_givens(solution, puzzle, n, seed=None):
    if seed is not None:
        random.seed(seed)

    p = deepcopy(puzzle)
    given_cells = [(i, j) for i in range(n) for j in range(n) if p[i][j] != 0]

    if not given_cells:
        # No givens to sabotage → just insert a duplicate in the top-left corner
        p[0][0] = solution[0][0]
        p[0][1] = solution[0][0]
        return p

    random.shuffle(given_cells)
    for ci, cj in given_cells:
        same_row_given = [k for k in range(n) if k != cj and p[ci][k] != 0]
        if same_row_given:
            k = random.choice(same_row_given)
            if p[ci][k] != p[ci][cj]:
                p[ci][cj] = p[ci][k]
                return p

    # If we couldn't create a duplicate from existing givens, forcibly insert one in the first row
    row0_givens = [j for j in range(n) if p[0][j] != 0]
    if len(row0_givens) >= 1:
        j1 = row0_givens[0]
        target_j = 0 if j1 != 0 else 1
        p[0][target_j] = p[0][j1]
    else:
        p[0][0] = solution[0][0]
        p[0][1] = solution[0][0]

    return p


# ---------------------------------------------------------------------------
# Board / solution-count utilities 
# ---------------------------------------------------------------------------

def build_board_from_puzzle(n, puzzle, h_cons, v_cons):
    """Convert matrix-form puzzle + constraints (-1/0/1) to Board/PuzzleContext."""
    given = {}
    for i in range(n):
        for j in range(n):
            val = puzzle[i][j]
            if val != 0:
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
    empty_cells = board.get_empty_cells()
    nodes_visited = 0

    def dfs(idx: int) -> int:
        nonlocal nodes_visited
        nodes_visited += 1
        if nodes_visited >= max_nodes:
            return limit  # treat as "at least limit"

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


def classify_puzzle(n, puzzle, h_cons, v_cons) -> str:
    """ Return 'UNIQUE', 'MULTIPLE', or 'NOSOLUTION' by counting solutions. """
    board = build_board_from_puzzle(n, puzzle, h_cons, v_cons)
    max_nodes = 50_000 if n <= 7 else 200_000
    num = count_solutions(board, limit=2, max_nodes=max_nodes)
    if num == 0:
        return "NOSOLUTION"
    if num == 1:
        return "UNIQUE"
    return "MULTIPLE"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def write_input_file(filepath, n, puzzle, h_cons, v_cons):
    lines = [str(n)]
    for i in range(n):
        lines.append(', '.join(str(puzzle[i][j]) for j in range(n)))
    for i in range(n):
        lines.append(', '.join(str(h_cons[i][j]) for j in range(n - 1)))
    for i in range(n - 1):
        lines.append(', '.join(str(v_cons[i][j]) for j in range(n)))
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------------------
# Per-type generation functions
# ---------------------------------------------------------------------------

def generate_unique(n, density, ratio, seed, max_tries=150):
    """
    Search up to *max_tries* seeds for a puzzle with exactly 1 solution.
    Returns (puzzle, h_cons, v_cons, attempts) or None if not found.
    """
    for attempt in range(max_tries):
        cur_seed = seed + attempt * 1000
        solution = generate_solution(n, seed=cur_seed)
        h_cons, v_cons = generate_constraints(solution, n, density=density, seed=cur_seed + 1)
        puzzle = generate_givens(solution, n, ratio=ratio, seed=cur_seed + 2)

        if not verify_constraints(solution, h_cons, v_cons, n):
            continue
        if classify_puzzle(n, puzzle, h_cons, v_cons) == "UNIQUE":
            return puzzle, h_cons, v_cons, attempt + 1

    return None


def generate_multiple(n, density, ratio, seed, max_tries=150):
    """
    Generate a puzzle guaranteed to have > 1 solution.

    Strategy: automatically reduce clue ratio and constraint density to very
    low values so the board is nearly unconstrained, then verify with
    classify_puzzle.  The original density/ratio are used only to derive
    the sparse values (keeping relative difficulty proportional).
    """
    # Auto-reduce to ~5 % of original to guarantee sparseness
    sparse_ratio   = min(ratio * 0.3, 0.05)
    sparse_density = min(density * 0.2, 0.05)

    for attempt in range(max_tries):
        cur_seed = seed + attempt * 1000
        solution = generate_solution(n, seed=cur_seed)
        h_cons, v_cons = generate_sparse_constraints(
            solution, n, density=sparse_density, seed=cur_seed + 1
        )
        puzzle = generate_sparse_givens(solution, n, ratio=sparse_ratio, seed=cur_seed + 2)

        if classify_puzzle(n, puzzle, h_cons, v_cons) == "MULTIPLE":
            return puzzle, h_cons, v_cons, attempt + 1

    return None


def generate_nosolution(n, density, ratio, seed, max_tries=150):
    """
    Generate an unsolvable puzzle by applying two sabotage methods together:
      1. inject_contradictory_constraints – flips half the constraints and
         adds extra wrong-direction ones.
      2. inject_contradictory_givens – inserts a duplicate value in a row,
         violating the Latin-square uniqueness requirement.

    Both methods are stacked to maximise robustness across board sizes.
    Verified with classify_puzzle before accepting.
    """
    for attempt in range(max_tries):
        cur_seed = seed + attempt * 1000
        solution = generate_solution(n, seed=cur_seed)
        h_cons, v_cons = generate_constraints(
            solution, n, density=density, seed=cur_seed + 1
        )
        puzzle = generate_givens(solution, n, ratio=ratio, seed=cur_seed + 2)

        # Sabotage 1: flip/add wrong constraints
        bad_h, bad_v = inject_contradictory_constraints(
            solution, h_cons, v_cons, n, seed=cur_seed + 3
        )
        # Sabotage 2: insert a duplicate given clue
        bad_puzzle = inject_contradictory_givens(
            solution, puzzle, n, seed=cur_seed + 4
        )

        if classify_puzzle(n, bad_puzzle, bad_h, bad_v) == "NOSOLUTION":
            return bad_puzzle, bad_h, bad_v, attempt + 1

    return None


# ---------------------------------------------------------------------------
# Test-case configuration
# ---------------------------------------------------------------------------

"""
TEST_CONFIGS format:
  (puzzle_type, n, density, ratio, seed)

puzzle_type : "UNIQUE" | "MULTIPLE" | "NOSOLUTION"
n           : grid size (4–9)
density     : base probability of placing a constraint edge
ratio       : base fraction of cells revealed as given clues
seed        : base random seed

For MULTIPLE  → density/ratio are automatically reduced internally.
For NOSOLUTION → density/ratio control the base puzzle before sabotage.
"""

TEST_CONFIGS = [
    # ── UNIQUE solutions ──────────────────────────────────────────────────
    ("UNIQUE",     4, 0.30, 0.20,  42),   # 01: 4×4 medium
    ("UNIQUE",     5, 0.35, 0.20,  55),   # 02: 5×5 medium
    ("UNIQUE",     6, 0.35, 0.22,  64),   # 03: 6×6 medium
    ("UNIQUE",     7, 0.28, 0.16,  37),   # 04: 7×7 medium
    ("UNIQUE",     9, 0.35, 0.22,  19),   # 05: 9×9 medium

    # ── MULTIPLE solutions ────────────────────────────────────────────────
    ("MULTIPLE",   4, 0.50, 0.45,  14),   # 06: 4×4
    ("MULTIPLE",   5, 0.38, 0.40,  88),   # 07: 5×5
    ("MULTIPLE",   6, 0.45, 0.30,  72),   # 08: 6×6
    ("MULTIPLE",   7, 0.40, 0.35,  56),   # 09: 7×7
    ("MULTIPLE",   9, 0.42, 0.32,  37),   # 10: 9×9

    # ── NO solution ───────────────────────────────────────────────────────
    ("NOSOLUTION", 4, 0.40, 0.30,  77),   # 11: 4×4
    ("NOSOLUTION", 5, 0.25, 0.20,  23),   # 12: 5×5
    ("NOSOLUTION", 6, 0.30, 0.18,  17),   # 13: 6×6
    ("NOSOLUTION", 7, 0.38, 0.25,  47),   # 14: 7×7
    ("NOSOLUTION", 9, 0.35, 0.20,  61),   # 15: 9×9
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    output_dir = "Inputs"
    os.makedirs(output_dir, exist_ok=True)

    print("Generating Futoshiki test cases (UNIQUE / MULTIPLE / NOSOLUTION)…\n")
    print(f"{'#':>3}  {'Type':<12} {'N':>2}  {'Status':<35}  {'Attempts':>8}")
    print("-" * 65)

    summary = {"UNIQUE": 0, "MULTIPLE": 0, "NOSOLUTION": 0, "FAILED": 0}

    for idx, (ptype, n, density, ratio, seed) in enumerate(TEST_CONFIGS, start=1):

        if ptype == "UNIQUE":
            result = generate_unique(n, density, ratio, seed)
        elif ptype == "MULTIPLE":
            result = generate_multiple(n, density, ratio, seed)
        else:  # NOSOLUTION
            result = generate_nosolution(n, density, ratio, seed)

        if result is not None:
            puzzle, h_cons, v_cons, attempts = result
            filepath = os.path.join(output_dir, f"input-{idx:02d}.txt")
            write_input_file(filepath, n, puzzle, h_cons, v_cons)
            status = f"OK → {filepath}"
            summary[ptype] += 1
        else:
            attempts = 150
            status = "FAILED (adjust config or increase max_tries)"
            summary["FAILED"] += 1

        print(f"{idx:>3}  {ptype:<12} {n:>2}  {status:<35}  {attempts:>8}")

    print("\n" + "=" * 65)
    print("Summary:")
    for k, v in summary.items():
        print(f"  {k:<12}: {v}")
    print(f"\nAll files saved to ./{output_dir}/")
    

if __name__ == "__main__":
    main()