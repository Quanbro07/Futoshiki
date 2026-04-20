"""Benchmark peak memory usage for solvable Futoshiki puzzles.

- For each testcase, each algorithm is run N times; report average peak memory.

Usage:
    python testing/benchmark/BenchmarkMemoryUsage.py
    python testing/benchmark/BenchmarkMemoryUsage.py --repeats 5 --timeout 600
"""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import statistics
import sys
import time
import tracemalloc
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
    avg_peak_kb: float
    solved: bool


@dataclass(frozen=True)
class BenchmarkCell:
    status: Literal["ok", "timeout", "error"]
    avg_peak_kb: float | None = None
    solved: bool | None = None


def _build_board(input_path: str | Path) -> Board:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(str(input_path))
    assignment = given.copy()
    ctx = PuzzleContext(N, assignment, less_h, greater_h, less_v, greater_v)
    return Board(assignment, ctx)


def _measure_peak_kb(fn: Callable[[], bool]) -> tuple[bool, float]:
    """Return (ok, peak_kb) using tracemalloc for functions that don't stop it."""
    tracing_before = tracemalloc.is_tracing()
    if not tracing_before:
        tracemalloc.start()

    ok = fn()

    if tracemalloc.is_tracing():
        _, peak = tracemalloc.get_traced_memory()
        peak_kb = peak / 1024
    else:
        peak_kb = 0.0

    if not tracing_before and tracemalloc.is_tracing():
        tracemalloc.stop()

    return ok, peak_kb


def _run_backtracking_peak_kb(input_path: str | Path) -> tuple[bool, float]:
    board = _build_board(input_path)
    solver = Backtracking()
    ok = solver.solve(board)
    peak_kb = float(getattr(solver, "memory", 0.0) or 0.0)
    return ok, peak_kb


def _run_ac3_peak_kb(input_path: str | Path) -> tuple[bool, float]:
    board = _build_board(input_path)
    solver = AC_3()
    ok = solver.solve(board)
    peak_kb = float(getattr(solver, "memory", 0.0) or 0.0)
    return ok, peak_kb


def _run_astar_peak_kb(input_path: str | Path) -> tuple[bool, float]:
    board = _build_board(input_path)
    solver = AStar()
    ok = solver.solve(board)
    peak_kb = float(getattr(solver, "memory", 0.0) or 0.0)
    return ok, peak_kb


def _run_forward_peak_kb(input_path: str | Path) -> tuple[bool, float]:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(str(input_path))
    solver = ForwardChaining(N, given.copy(), less_h, greater_h, less_v, greater_v)

    def _solve() -> bool:
        return solver.solve()

    return _measure_peak_kb(_solve)


def _run_backward_peak_kb(input_path: str | Path) -> tuple[bool, float]:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(str(input_path))
    kb = generate_KB(str(input_path))
    solver = BackwardChainingSolver(kb, N, given.copy(), less_h, greater_h, less_v, greater_v)

    def _solve() -> bool:
        return solver.solve()

    return _measure_peak_kb(_solve)


def _benchmark_one(
    solver_fn: Callable[[str | Path], tuple[bool, float]],
    input_path: Path,
    repeats: int,
) -> BenchmarkResult:
    peaks: list[float] = []
    solved = False

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        for _ in range(repeats):
            solved, peak_kb = solver_fn(input_path)
            peaks.append(float(peak_kb))

    return BenchmarkResult(avg_peak_kb=statistics.fmean(peaks), solved=solved)


def _benchmark_worker(
    solver_name: str,
    input_path: str,
    repeats: int,
    out_queue: "mp.Queue",
) -> None:
    """Run benchmark in a child process.

    We keep mapping by name to avoid pickling issues with callables on Windows.
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    solver_map: dict[str, Callable[[str | Path], tuple[bool, float]]] = {
        "Backtracking": _run_backtracking_peak_kb,
        "AC_3": _run_ac3_peak_kb,
        "AStar": _run_astar_peak_kb,
        "ForwardChaining": _run_forward_peak_kb,
        "BackwardChaining": _run_backward_peak_kb,
    }

    solver_fn = solver_map[solver_name]
    try:
        result = _benchmark_one(solver_fn, Path(input_path), repeats=repeats)
        out_queue.put(("ok", result.avg_peak_kb, result.solved))
    except Exception as ex:
        out_queue.put(("error", repr(ex), None))


def _benchmark_one_with_timeout(
    solver_name: str,
    solver_fn: Callable[[str | Path], tuple[bool, float]],
    input_path: Path,
    repeats: int,
    timeout_seconds: float | None,
    isolate: bool,
) -> BenchmarkCell:
    """Benchmark with optional subprocess isolation + timeout.

    If isolate is False, runs in-process and ignores timeout_seconds.
    """
    if not isolate:
        try:
            result = _benchmark_one(solver_fn, input_path, repeats=repeats)
            return BenchmarkCell(status="ok", avg_peak_kb=result.avg_peak_kb, solved=result.solved)
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
        return BenchmarkCell(status="ok", avg_peak_kb=float(payload1), solved=bool(payload2))
    return BenchmarkCell(status="error")


def _inputs_to_benchmark(project_root: Path) -> list[Path]:
    inputs_dir = project_root / "Inputs"

    selected: list[str] = [
        # *(f"input-{i:02d}.txt" for i in range(1, 11)),
        # *(f"input-{i:02d}.txt" for i in range(18, 23)),
        *(f"input-{i:02d}.txt" for i in range(11, 18)),
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
            elif cell.status == "error" or cell.avg_peak_kb is None:
                row.append("ERR")
            else:
                suffix = "" if cell.solved else " (unsolved)"
                row.append(f"{cell.avg_peak_kb:.2f}{suffix}")
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
    parser = argparse.ArgumentParser(description="Benchmark peak memory usage for solvable Futoshiki puzzles")
    parser.add_argument("--repeats", type=int, default=REPEATS, help="Number of runs per (testcase, algorithm)")
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

    solvers: list[tuple[str, Callable[[str | Path], tuple[bool, float]]]] = [
        ("Backtracking", _run_backtracking_peak_kb),
        ("AC_3", _run_ac3_peak_kb),
        ("AStar", _run_astar_peak_kb),
        ("ForwardChaining", _run_forward_peak_kb),
        ("BackwardChaining", _run_backward_peak_kb),
    ]

    input_paths = _inputs_to_benchmark(PROJECT_ROOT)

    solver_names = [name for name, _ in solvers]
    input_names = [p.name for p in input_paths]

    matrix_cells: list[list[BenchmarkCell]] = [[BenchmarkCell(status="error")] * len(solvers) for _ in input_paths]

    for r, input_path in enumerate(input_paths):
        for c, (solver_name, solver_fn) in enumerate(solvers):
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
    print("Peak memory is average KB (lower is better).")
    _print_table(input_names, solver_names, matrix_cells)


if __name__ == "__main__":
    main()
