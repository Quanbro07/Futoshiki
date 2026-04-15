"""Experiment helper for tuning density and ratio for Futoshiki test generation.

This module samples many random puzzles for given (n, density, ratio) settings
and reports how often they have a unique solution, plus some basic statistics
(number of givens and constraints).
"""

from __future__ import annotations

from typing import Iterable, List, Dict, Any

from GenerateTestcases import (
    generate_solution,
    generate_constraints,
    generate_givens,
    verify_constraints,
    has_unique_solution,
)


def _count_givens(puzzle: List[List[int]]) -> int:
    return sum(1 for row in puzzle for v in row if v != 0)


def _count_constraints(h_cons, v_cons) -> int:
    h = sum(1 for row in h_cons for c in row if c != 0)
    v = sum(1 for row in v_cons for c in row if c != 0)
    return h + v


def experiment(
    n: int,
    density_list: Iterable[float],
    ratio_list: Iterable[float],
    trials: int = 50,
    max_tries_per_trial: int = 10,
    base_seed: int = 1234,
) -> List[Dict[str, Any]]:
    """Run a grid-search style experiment over (density, ratio).

    For each pair (density, ratio), we:
    - generate up to ``trials`` random puzzles,
    - for each trial, try up to ``max_tries_per_trial`` seeds until
      constraints are consistent with the full solution,
    - check whether the resulting puzzle has a unique solution.

    Returns a list of result dicts and also prints a compact summary table.
    """

    results: List[Dict[str, Any]] = []

    for density in density_list:
        for ratio in ratio_list:
            unique_count = 0
            valid_trials = 0
            total_givens = 0
            total_constraints = 0

            for t in range(trials):
                attempt = 0
                puzzle = None
                h_cons = v_cons = None

                while attempt < max_tries_per_trial:
                    cur_seed = base_seed + t * 1000 + attempt

                    solution = generate_solution(n, seed=cur_seed)
                    h_cons, v_cons = generate_constraints(
                        solution, n, density=density, seed=cur_seed + 1
                    )
                    puzzle = generate_givens(
                        solution, n, ratio=ratio, seed=cur_seed + 2
                    )

                    if verify_constraints(solution, h_cons, v_cons, n):
                        break

                    attempt += 1

                # Could not find a valid puzzle for this trial
                if attempt == max_tries_per_trial or puzzle is None:
                    continue

                valid_trials += 1
                total_givens += _count_givens(puzzle)
                total_constraints += _count_constraints(h_cons, v_cons)

                if has_unique_solution(n, puzzle, h_cons, v_cons):
                    unique_count += 1

            if valid_trials == 0:
                unique_rate = 0.0
                avg_givens = 0.0
                avg_constraints = 0.0
            else:
                unique_rate = unique_count / valid_trials
                avg_givens = total_givens / valid_trials
                avg_constraints = total_constraints / valid_trials

            results.append(
                {
                    "n": n,
                    "density": float(density),
                    "ratio": float(ratio),
                    "trials": trials,
                    "valid_trials": valid_trials,
                    "unique_count": unique_count,
                    "unique_rate": unique_rate,
                    "avg_givens": avg_givens,
                    "avg_constraints": avg_constraints,
                }
            )

    # Print summary
    print(
        "n  density  ratio   valid  unique  unique_%   avg_givens  avg_constraints"
    )
    for r in results:
        print(
            f"{r['n']:>2}  "
            f"{r['density']:.2f}    "
            f"{r['ratio']:.2f}   "
            f"{r['valid_trials']:>5}  "
            f"{r['unique_count']:>6}  "
            f"{r['unique_rate']*100:7.2f}  "
            f"{r['avg_givens']:11.2f}  "
            f"{r['avg_constraints']:15.2f}"
        )

    return results


if __name__ == "__main__":
    # Example usage: tune parameters for n = 5
    n = 5
    density_list = [0.30, 0.40, 0.50]
    ratio_list = [0.20, 0.30, 0.40]

    experiment(n, density_list, ratio_list, trials=30)
