import argparse
import os
import multiprocessing as mp
import re
import time
import tracemalloc
from typing import Callable, Optional

from helperFunction.ParseInput import parse_input
from helperFunction.WriteOutput import parse_output, write_output
from state.PuzzleContext import PuzzleContext
from state.Board import Board

from algorithm.Backtracking import Backtracking
from algorithm.AC_3 import AC_3
from algorithm.AStar import AStar
from algorithm.ForwardChaining import ForwardChaining
from algorithm.BackwardChaining import BackwardChainingSolver
from helperFunction.GenerateKB import generate_KB


# Configurable via CLI in main().
_BACKWARD_TIMEOUT_S: float = 0.0
_PRINT_OUTPUT: bool = False
_WRITE_OUTPUT_FILES: bool = True


def _maybe_print_output(output: str) -> None:
    if not _PRINT_OUTPUT:
        return
    print("OUTPUT TEXT:")
    # Avoid double newlines; the output is typically already newline-terminated.
    print(output, end="" if output.endswith("\n") else "\n")


def _maybe_write_output(output_path: Optional[str], output: str) -> None:
    if not _WRITE_OUTPUT_FILES:
        return
    if not output_path:
        return
    write_output(output_path, output)


def _sorted_input_files(inputs_dir: str) -> list[str]:
    if not os.path.isdir(inputs_dir):
        raise FileNotFoundError(f"Inputs folder not found: {inputs_dir}")

    files = [
        os.path.join(inputs_dir, f)
        for f in os.listdir(inputs_dir)
        if f.lower().endswith(".txt") and f.lower().startswith("input")
    ]
    files.sort(key=lambda p: os.path.basename(p))
    return files


def _load_puzzle(input_path: str):
    N, given, less_h, greater_h, less_v, greater_v = parse_input(input_path)
    context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)
    board = Board(given.copy(), context)
    return N, given, less_h, greater_h, less_v, greater_v, context, board


def _grid_from_assignment(N: int, assignment: dict[tuple[int, int], int]) -> list[list[int]]:
    grid = [[0 for _ in range(N)] for _ in range(N)]
    for (r, c), v in assignment.items():
        grid[r - 1][c - 1] = v
    return grid


def _print_case_header(algo: str, input_path: str):
    name = os.path.basename(input_path)
    print("=" * 80)
    print(f"ALGO : {algo}")
    print(f"INPUT: {name}")
    print("-" * 80)


def _print_case_footer(
    ok: bool,
    seconds: Optional[float],
    peak_kb: Optional[float],
    expanded_nodes: Optional[int],
    output_path: Optional[str] = None,
):
    print("-" * 80)
    print(f"Solved: {ok}")
    if seconds is not None:
        print(f"Time:   {seconds:.4f}s")
    if peak_kb is not None:
        print(f"Memory: {peak_kb:.2f}KB")
    if expanded_nodes is not None:
        print(f"Expanded: {expanded_nodes} nodes")
    if output_path is not None:
        print(f"Output: {output_path}")
    print("=" * 80)


def _extract_input_index(input_path: str) -> Optional[int]:
    """Extract numeric index from filenames like input-01.txt, input_2.txt, input10.txt."""
    base = os.path.basename(input_path).lower()
    m = re.search(r"input\D*(\d+)", base)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _output_path_for_input(
    input_path: str,
    outputs_dir: str,
    algo_name: str,
    multi_algo: bool,
    fallback_index: int,
) -> str:
    idx = _extract_input_index(input_path)
    if idx is None:
        idx = fallback_index

    idx_str = f"{idx:02d}"
    if multi_algo:
        out_dir = os.path.join(outputs_dir, algo_name)
    else:
        out_dir = outputs_dir

    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, f"output-{idx_str}.txt")


def _backward_worker(input_path: str, result_queue):
    """Run backward chaining in a child process so we can enforce a hard timeout on Windows."""
    try:
        N, given, less_h, greater_h, less_v, greater_v = parse_input(input_path)
        context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)

        kb = generate_KB(input_path)
        solver = BackwardChainingSolver(kb, N, given.copy(), less_h, greater_h, less_v, greater_v)

        tracemalloc.start()
        start = time.perf_counter()
        ok = solver.solve()
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if ok:
            grid = _grid_from_assignment(N, solver.assignment)
            output = parse_output(grid, context)
        else:
            output = "No solution\n"

        result_queue.put(
            {
                "ok": ok,
                "seconds": elapsed,
                "peak_kb": peak / 1024,
                "expanded_nodes": getattr(solver, "expanded_nodes", None),
                "output": output,
            }
        )
    except Exception as ex:
        try:
            result_queue.put({"error": str(ex)})
        except Exception:
            pass


def run_backtracking(input_path: str, output_path: str) -> None:
    N, given, less_h, greater_h, less_v, greater_v, context, board = _load_puzzle(input_path)
    solver = Backtracking()
    ok = solver.solve(board)

    if ok:
        grid = board.to_grid()
        output = parse_output(grid, context)
    else:
        output = "No solution\n"

    _maybe_write_output(output_path, output)
    _maybe_print_output(output)

    _print_case_footer(
        ok=ok,
        seconds=getattr(solver, "time", None),
        peak_kb=getattr(solver, "memory", None),
        expanded_nodes=getattr(solver, "expanded_nodes", None),
        output_path=output_path,
    )


def run_ac3(input_path: str, output_path: str) -> None:
    N, given, less_h, greater_h, less_v, greater_v, context, board = _load_puzzle(input_path)
    solver = AC_3()
    ok = solver.solve(board)

    if ok:
        grid = board.to_grid()
        output = parse_output(grid, context)
    else:
        output = "No solution\n"

    _maybe_write_output(output_path, output)
    _maybe_print_output(output)

    _print_case_footer(
        ok=ok,
        seconds=getattr(solver, "time", None),
        peak_kb=getattr(solver, "memory", None),
        expanded_nodes=getattr(solver, "expanded_nodes", None),
        output_path=output_path,
    )


def run_astar(input_path: str, output_path: str) -> None:
    N, given, less_h, greater_h, less_v, greater_v, context, board = _load_puzzle(input_path)
    solver = AStar()
    ok = solver.solve(board)

    if ok:
        grid = board.to_grid()
        output = parse_output(grid, context)
    else:
        output = "No solution\n"

    _maybe_write_output(output_path, output)
    _maybe_print_output(output)

    _print_case_footer(
        ok=ok,
        seconds=getattr(solver, "time", None),
        peak_kb=getattr(solver, "memory", None),
        expanded_nodes=getattr(solver, "expanded_nodes", None),
        output_path=output_path,
    )


def run_forward(input_path: str, output_path: str) -> None:
    N, given, less_h, greater_h, less_v, greater_v, context, _board = _load_puzzle(input_path)

    solver = ForwardChaining(input_path)

    ok = solver.solve()
    seconds = getattr(solver, "time", None)
    peak_kb = getattr(solver, "memory", None)

    if ok:
        grid = solver.get_grid()
        output = parse_output(grid, context)
    else:
        output = "No solution\n"

    _maybe_write_output(output_path, output)
    _maybe_print_output(output)

    _print_case_footer(
        ok=ok,
        seconds=seconds,
        peak_kb=peak_kb,
        expanded_nodes=None,
        output_path=output_path,
    )


def run_backward(input_path: str, output_path: str) -> None:
    if _BACKWARD_TIMEOUT_S and _BACKWARD_TIMEOUT_S > 0:
        ctx = mp.get_context("spawn")
        result_queue = ctx.Queue(maxsize=1)
        proc = ctx.Process(target=_backward_worker, args=(input_path, result_queue))
        proc.start()
        proc.join(_BACKWARD_TIMEOUT_S)

        if proc.is_alive():
            proc.terminate()
            proc.join(5)

            ok = False
            seconds: Optional[float] = _BACKWARD_TIMEOUT_S
            peak_kb: Optional[float] = None
            expanded_nodes: Optional[int] = None
            output = f"TIMEOUT after {_BACKWARD_TIMEOUT_S:.2f} seconds\n"

            _maybe_write_output(output_path, output)
            _maybe_print_output(output)
            _print_case_footer(ok=ok, seconds=seconds, peak_kb=peak_kb, expanded_nodes=expanded_nodes, output_path=output_path)
            return

        # Process finished within timeout.
        try:
            result = result_queue.get_nowait()
        except Exception:
            result = {"error": "No result returned from child process"}

        if "error" in result:
            ok = False
            output = f"ERROR: {result['error']}\n"
            _maybe_write_output(output_path, output)
            _maybe_print_output(output)
            _print_case_footer(ok=False, seconds=None, peak_kb=None, expanded_nodes=None, output_path=output_path)
            return

        ok = bool(result.get("ok", False))
        seconds = result.get("seconds")
        peak_kb = result.get("peak_kb")
        expanded_nodes = result.get("expanded_nodes")
        output = str(result.get("output", ""))

        _maybe_write_output(output_path, output)
        _maybe_print_output(output)
        _print_case_footer(ok=ok, seconds=seconds, peak_kb=peak_kb, expanded_nodes=expanded_nodes, output_path=output_path)
        return

    # No timeout: run in-process (faster, easier debugging).
    N, given, less_h, greater_h, less_v, greater_v, context, _board = _load_puzzle(input_path)

    kb = generate_KB(input_path)
    solver = BackwardChainingSolver(kb, N, given.copy(), less_h, greater_h, less_v, greater_v)

    ok = solver.solve()
    seconds = getattr(solver, "time", None)
    peak_kb = getattr(solver, "memory", None)

    if ok:
        grid = _grid_from_assignment(N, solver.assignment)
        output = parse_output(grid, context)
    else:
        output = "No solution\n"

    _maybe_write_output(output_path, output)
    _maybe_print_output(output)

    _print_case_footer(
        ok=ok,
        seconds=seconds,
        peak_kb=peak_kb,
        expanded_nodes=getattr(solver, "expanded_nodes", None),
        output_path=output_path,
    )


ALGO_RUNNERS: dict[str, Callable[[str, str], None]] = {
    "backtracking": run_backtracking,
    "bt": run_backtracking,
    "ac3": run_ac3,
    "ac-3": run_ac3,
    "astar": run_astar,
    "a*": run_astar,
    "forward": run_forward,
    "fc": run_forward,
    "backward": run_backward,
    "bc": run_backward,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Futoshiki solvers over Inputs/*.txt and write results to Outputs/output-XX.txt.")
    parser.add_argument(
        "--algo",
        "--algorithm",
        dest="algo",
        default="all",
        help="Algorithm name: backtracking|ac3|astar|forward|backward or all (default).",
    )
    parser.add_argument(
        "--inputs",
        dest="inputs_dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Inputs"),
        help="Path to Inputs folder (default: ./Inputs).",
    )
    parser.add_argument(
        "--outputs",
        dest="outputs_dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Outputs"),
        help="Path to Outputs folder (default: ./Outputs).",
    )
    parser.add_argument(
        "--backward-timeout",
        dest="backward_timeout",
        type=float,
        default=0.0,
        help="Timeout in seconds for backward chaining (0 = no timeout).",
    )
    parser.add_argument(
        "--print-output",
        dest="print_output",
        action="store_true",
        help="Also print the output text to the terminal for each case (in addition to writing the output file).",
    )
    parser.add_argument(
        "--cases",
        dest="cases",
        default="",
        help="Comma-separated input indices to run (e.g. 13,14). If omitted, runs all inputs.",
    )

    args = parser.parse_args()

    global _BACKWARD_TIMEOUT_S
    _BACKWARD_TIMEOUT_S = float(args.backward_timeout or 0.0)

    global _PRINT_OUTPUT
    _PRINT_OUTPUT = bool(args.print_output)

    global _WRITE_OUTPUT_FILES
    # Requirement: if --print-output is set, do not create/write output files.
    _WRITE_OUTPUT_FILES = not _PRINT_OUTPUT

    input_files = _sorted_input_files(args.inputs_dir)

    # Optional filtering by input indices (e.g., input-13.txt -> 13).
    cases_raw = str(args.cases or "").strip()
    if cases_raw:
        try:
            selected = {int(x) for x in re.split(r"[ ,;]+", cases_raw) if x.strip()}
        except ValueError:
            print(f"Invalid --cases value: {args.cases}. Expected comma-separated integers like 13,14")
            return 2

        filtered: list[str] = []
        for p in input_files:
            idx = _extract_input_index(p)
            if idx is not None and idx in selected:
                filtered.append(p)
        input_files = filtered
    if not input_files:
        if cases_raw:
            print(f"No matching input files for --cases={args.cases} in: {args.inputs_dir}")
            return 1
        print(f"No input files found in: {args.inputs_dir}")
        return 1

    algo = str(args.algo).strip().lower()

    if algo == "all":
        algo_list = ["backtracking", "ac3", "astar", "forward", "backward"]
    else:
        if algo not in ALGO_RUNNERS:
            print(f"Invalid algorithm: {args.algo}")
            print("Valid values: backtracking, ac3, astar, forward, backward, all")
            return 2
        # normalize alias -> canonical by mapping
        canonical = {
            "bt": "backtracking",
            "ac-3": "ac3",
            "a*": "astar",
            "fc": "forward",
            "bc": "backward",
        }.get(algo, algo)
        algo_list = [canonical]

    multi_algo = len(algo_list) > 1
    if _WRITE_OUTPUT_FILES:
        os.makedirs(args.outputs_dir, exist_ok=True)

    for algo_name in algo_list:
        runner = ALGO_RUNNERS[algo_name]
        for idx, input_path in enumerate(input_files, start=1):
            output_path: str
            if _WRITE_OUTPUT_FILES:
                output_path = _output_path_for_input(
                    input_path=input_path,
                    outputs_dir=args.outputs_dir,
                    algo_name=algo_name,
                    multi_algo=multi_algo,
                    fallback_index=idx,
                )
            else:
                # Placeholder path for printing; no file will be created.
                output_path = ""
            _print_case_header(algo_name, input_path)
            try:
                runner(input_path, output_path)
            except Exception as ex:
                print(f"ERROR while running {algo_name} on {os.path.basename(input_path)}: {ex}")
                try:
                    output = f"ERROR: {ex}\n"
                    _maybe_write_output(output_path, output)
                    _maybe_print_output(output)
                except Exception:
                    pass
                _print_case_footer(ok=False, seconds=None, peak_kb=None, expanded_nodes=None, output_path=(output_path or None))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
