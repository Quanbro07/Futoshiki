"""Benchmark number of inferences for solvable Futoshiki puzzles.

This project doesn't expose a single unified "inference" counter across all
solvers, so this benchmark uses the best available proxy per algorithm:

- Backtracking / AC_3 / AStar / BackwardChaining: `expanded_nodes`.
- ForwardChaining: counts how many domain values are removed (pruning events)
  while running the rules.

Usage:
    python testing/benchmark/BenchmarkNumOfInferences.py
    python testing/benchmark/BenchmarkNumOfInferences.py --repeats 3 --timeout 600

"""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helperFunction.ParseInput import parse_input
from state.Board import Board
from state.PuzzleContext import PuzzleContext

from algorithm.Backtracking import Backtracking
from algorithm.AC_3 import AC_3
from algorithm.AStar import AStar
from algorithm.ForwardChaining import ForwardChaining
from algorithm.BackwardChaining import BackwardChainingSolver
from helperFunction.GenerateKB import generate_KB


REPEATS = 10
DEFAULT_TIMEOUT_SECONDS = 600.0


@dataclass(frozen=True)
class BenchmarkResult:
    avg_inferences: float
    solved: bool


@dataclass(frozen=True)
class BenchmarkCell:
    status: Literal["ok", "timeout", "error"]
    avg_inferences: float | None = None
    solved: bool | None = None


def _build_board(input_path: str | Path) -> Board:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(str(input_path))
    assignment = given.copy()
    ctx = PuzzleContext(N, assignment, less_h, greater_h, less_v, greater_v)
    return Board(assignment, ctx)


class _ForwardChainingWithInferences(ForwardChaining):
    """ForwardChaining with a lightweight inference counter.

    We count how many domain values are removed across pruning operations.
    """

    def __init__(self, input_path: str | Path):
        super().__init__(str(input_path))
        self.inferences = 0

    def prune_row_col(self, r, c, val):
        res = False
        for k in range(1, self.N + 1):
            if k != c and val in self.domains[(r, k)]:
                self.domains[(r, k)].remove(val)
                self.inferences += 1
                res = True
            if k != r and val in self.domains[(k, c)]:
                self.domains[(k, c)].remove(val)
                self.inferences += 1
                res = True
        return res

    def constrain_pair(self, S, B):
        """Override to count domain pruning events.

        Base semantics: enforce S < B.
        """
        if S not in self.domains or B not in self.domains:
            return False
        if not self.domains[S] or not self.domains[B]:
            return False

        res = False

        # Prune S: values must be < max(B)
        max_B = max(self.domains[B])
        before_S = len(self.domains[S])
        new_S = [v for v in self.domains[S] if v < max_B]
        if len(new_S) < before_S:
            self.inferences += before_S - len(new_S)
            self.domains[S] = new_S
            res = True
            if not self.domains[S]:
                return res

        # Prune B: values must be > min(S)
        min_S = min(self.domains[S])
        before_B = len(self.domains[B])
        new_B = [v for v in self.domains[B] if v > min_S]
        if len(new_B) < before_B:
            self.inferences += before_B - len(new_B)
            self.domains[B] = new_B
            res = True

        return res

    def fill_hidden_singles(self):
        res = False
        for r in range(1, self.N + 1):
            for val in range(1, self.N + 1):
                possible_cols = [c for c in range(1, self.N + 1) if val in self.domains[(r, c)]]
                if len(possible_cols) == 1:
                    target_c = possible_cols[0]
                    before = len(self.domains[(r, target_c)])
                    if before > 1:
                        self.domains[(r, target_c)] = [val]
                        self.inferences += before - 1
                        res = True
        for c in range(1, self.N + 1):
            for val in range(1, self.N + 1):
                possible_rows = [r for r in range(1, self.N + 1) if val in self.domains[(r, c)]]
                if len(possible_rows) == 1:
                    target_r = possible_rows[0]
                    before = len(self.domains[(target_r, c)])
                    if before > 1:
                        self.domains[(target_r, c)] = [val]
                        self.inferences += before - 1
                        res = True
        return res


def _run_backtracking_inferences(input_path: str | Path) -> tuple[bool, int]:
    board = _build_board(input_path)
    solver = Backtracking()
    ok = solver.solve(board)
    return ok, int(getattr(solver, "expanded_nodes", 0) or 0)


def _run_ac3_inferences(input_path: str | Path) -> tuple[bool, int]:
    board = _build_board(input_path)
    solver = AC_3()
    ok = solver.solve(board)
    return ok, int(getattr(solver, "expanded_nodes", 0) or 0)


def _run_astar_inferences(input_path: str | Path) -> tuple[bool, int]:
    board = _build_board(input_path)
    solver = AStar()
    ok = solver.solve(board)
    return ok, int(getattr(solver, "expanded_nodes", 0) or 0)


def _run_forward_inferences(input_path: str | Path) -> tuple[bool, int]:
    solver = _ForwardChainingWithInferences(input_path)
    ok = solver.solve()
    return ok, int(getattr(solver, "inferences", 0) or 0)


def _normalize_algo_token(token: str) -> str | None:
    t = str(token).strip().lower()
    if not t:
        return None
    aliases = {
        "backtracking": "backtracking",
        "bt": "backtracking",
        "ac3": "ac3",
        "ac-3": "ac3",
        "astar": "astar",
        "a*": "astar",
        "a-star": "astar",
        "forward": "forward",
        "fc": "forward",
        "forwardchaining": "forward",
        "backward": "backward",
        "bc": "backward",
        "backwardchaining": "backward",
    }
    return aliases.get(t)


def _run_backward_inferences(input_path: str | Path) -> tuple[bool, int]:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(str(input_path))
    kb = generate_KB(str(input_path))
    solver = BackwardChainingSolver(kb, N, given.copy(), less_h, greater_h, less_v, greater_v)
    ok = solver.solve()
    return ok, int(getattr(solver, "expanded_nodes", 0) or 0)


def _benchmark_one(
    solver_fn: Callable[[str | Path], tuple[bool, int]],
    input_path: Path,
    repeats: int,
) -> BenchmarkResult:
    counts: list[int] = []
    solved = False

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        for _ in range(repeats):
            solved, cnt = solver_fn(input_path)
            counts.append(int(cnt))

    return BenchmarkResult(avg_inferences=statistics.fmean(counts), solved=solved)


def _benchmark_worker(
    solver_name: str,
    input_path: str,
    repeats: int,
    out_queue: "mp.Queue",
) -> None:
    """Run benchmark in a child process."""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    solver_map: dict[str, Callable[[str | Path], tuple[bool, int]]] = {
        "Backtracking": _run_backtracking_inferences,
        "AC_3": _run_ac3_inferences,
        "AStar": _run_astar_inferences,
        "ForwardChaining": _run_forward_inferences,
        "BackwardChaining": _run_backward_inferences,
    }

    solver_fn = solver_map[solver_name]
    try:
        result = _benchmark_one(solver_fn, Path(input_path), repeats=repeats)
        out_queue.put(("ok", result.avg_inferences, result.solved))
    except Exception as ex:
        out_queue.put(("error", repr(ex), None))


def _benchmark_one_with_timeout(
    solver_name: str,
    solver_fn: Callable[[str | Path], tuple[bool, int]],
    input_path: Path,
    repeats: int,
    timeout_seconds: float | None,
    isolate: bool,
) -> BenchmarkCell:
    if not isolate:
        try:
            result = _benchmark_one(solver_fn, input_path, repeats=repeats)
            return BenchmarkCell(status="ok", avg_inferences=result.avg_inferences, solved=result.solved)
        except Exception:
            return BenchmarkCell(status="error")

    ctx = mp.get_context("spawn")
    out_queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_benchmark_worker,
        args=(solver_name, str(input_path), repeats, out_queue),
        daemon=True,
    )

    proc.start()
    proc.join(timeout=timeout_seconds)

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2)
        return BenchmarkCell(status="timeout")

    try:
        status, payload1, payload2 = out_queue.get_nowait()
    except Exception:
        return BenchmarkCell(status="error")

    if status == "ok":
        return BenchmarkCell(status="ok", avg_inferences=float(payload1), solved=bool(payload2))
    return BenchmarkCell(status="error")


def _inputs_to_benchmark(project_root: Path) -> list[Path]:
    inputs_dir = project_root / "Inputs"

    selected: list[str] = [
        *(f"input-{i:02d}.txt" for i in range(1, 11)),
        *(f"input-{i:02d}.txt" for i in range(18, 23)),
        # *(f"input-{i:02d}.txt" for i in range(11, 18)),
    ]

    paths = [inputs_dir / name for name in selected]
    missing = [p for p in paths if not p.exists()]
    if missing:
        missing_str = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(f"Missing input files: {missing_str}")

    return paths


def _print_table(
    input_names: Iterable[str],
    solver_names: list[str],
    matrix_cells: list[list[BenchmarkCell]],
) -> None:
    headers = ["Testcase", *solver_names]

    rows: list[list[str]] = []
    for r, test_name in enumerate(input_names):
        row: list[str] = [test_name]
        for c in range(len(solver_names)):
            cell = matrix_cells[r][c]
            if cell.status == "timeout":
                row.append("TIMEOUT")
            elif cell.status == "error" or cell.avg_inferences is None:
                row.append("ERR")
            else:
                suffix = "" if cell.solved else " (unsolved)"
                # Usually integer-ish, but we report avg -> float.
                value = cell.avg_inferences
                if abs(value - round(value)) < 1e-9:
                    row.append(f"{int(round(value))}{suffix}")
                else:
                    row.append(f"{value:.2f}{suffix}")
        rows.append(row)

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(cells))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt_row(row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark number of inferences for solvable Futoshiki puzzles")
    parser.add_argument("--repeats", type=int, default=REPEATS, help="Number of runs per (testcase, algorithm)")
    parser.add_argument(
        "--algo",
        "--algorithm",
        dest="algo",
        default="all",
        help=(
            "Which algorithm(s) to benchmark: backtracking|ac3|astar|forward|backward or all. "
            "You can pass a comma/space-separated list, e.g. 'ac3,forward'."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout (seconds) per (testcase, algorithm) when isolated",
    )
    parser.add_argument(
        "--isolation",
        choices=("all", "backward", "none"),
        default="all",
        help="Isolation mode: all=timeout all solvers, backward=only BackwardChaining, none=in-process (no timeout)",
    )
    args = parser.parse_args()

    solvers_all: list[tuple[str, str, Callable[[str | Path], tuple[bool, int]]]] = [
        ("backtracking", "Backtracking", _run_backtracking_inferences),
        ("ac3", "AC_3", _run_ac3_inferences),
        ("astar", "AStar", _run_astar_inferences),
        ("forward", "ForwardChaining", _run_forward_inferences),
        ("backward", "BackwardChaining", _run_backward_inferences),
    ]

    algo_raw = str(args.algo or "all").strip().lower()
    if algo_raw in ("", "all", "*"):
        solvers = solvers_all
    else:
        tokens = [t for t in re.split(r"[ ,;]+", algo_raw) if t.strip()]
        selected: set[str] = set()
        unknown: list[str] = []
        for tok in tokens:
            key = _normalize_algo_token(tok)
            if key is None:
                unknown.append(tok)
            else:
                selected.add(key)
        if unknown:
            raise SystemExit(
                "Unknown --algo value(s): "
                + ", ".join(unknown)
                + ". Expected backtracking|ac3|astar|forward|backward|all (aliases: bt, ac-3, a*, fc, bc)."
            )
        solvers = [s for s in solvers_all if s[0] in selected]
        if not solvers:
            raise SystemExit("No algorithms selected. Use --algo all or a non-empty list like 'ac3,forward'.")

    input_paths = _inputs_to_benchmark(PROJECT_ROOT)

    solver_names = [name for _key, name, _fn in solvers]
    input_names = [p.name for p in input_paths]

    matrix_cells: list[list[BenchmarkCell]] = [[BenchmarkCell(status="error")] * len(solvers) for _ in input_paths]

    for r, input_path in enumerate(input_paths):
        for c, (_key, solver_name, solver_fn) in enumerate(solvers):
            if args.isolation == "all":
                isolate = True
            elif args.isolation == "backward":
                isolate = solver_name == "BackwardChaining"
            else:  # none
                isolate = False

            timeout_seconds = float(args.timeout) if isolate else None

            cell = _benchmark_one_with_timeout(
                solver_name,
                solver_fn,
                input_path,
                repeats=int(args.repeats),
                timeout_seconds=timeout_seconds,
                isolate=isolate,
            )
            matrix_cells[r][c] = cell

    print(f"Benchmark repeats per (testcase, algorithm): {int(args.repeats)}")
    if args.isolation == "all":
        print(f"Isolation: all solvers (timeout={float(args.timeout)}s)")
    elif args.isolation == "backward":
        print(f"Isolation: BackwardChaining only (timeout={float(args.timeout)}s)")
    else:
        print("Isolation: none (no timeout)")
    print("Inferences are average counts (lower is better).")
    _print_table(input_names, solver_names, matrix_cells)


if __name__ == "__main__":
    main()
