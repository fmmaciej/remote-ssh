from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from bench.model import BenchConfigError
from bench.references import load_reference_scenarios
from bench.report import print_table, report_json
from bench.scenarios import run_named_scenario, selected_scenario_names, validate_scenario_names
from bench.stats import baseline_ready_median


def repo_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark remote-ssh shell startup locally.")
    parser.add_argument("--repo", type=Path, default=repo_dir(), help="remote-ssh repository path")
    parser.add_argument("--iterations", type=int, default=20, help="measured samples per scenario")
    parser.add_argument("--warmup", type=int, default=3, help="discarded warmup samples per scenario")
    parser.add_argument("--timeout", type=float, default=10.0, help="timeout per sample in seconds")
    parser.add_argument(
        "--scenario",
        action="append",
        help="scenario to run; may be passed more than once",
    )
    parser.add_argument("--format", choices=("table", "json"), default="table")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")
    if args.warmup < 0:
        raise SystemExit("--warmup must be at least 0")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than 0")
    if not (args.repo / "shell" / "rc.sh").is_file():
        raise SystemExit(f"missing remote-ssh rc.sh under repo: {args.repo}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validate_args(args)

    current_repo = args.repo.resolve()
    try:
        reference_scenarios = load_reference_scenarios(current_repo)
        reference_map = {reference.name: reference for reference in reference_scenarios}
        scenario_names = selected_scenario_names(args.scenario, tuple(reference_map))
        validate_scenario_names(scenario_names, reference_map)
    except BenchConfigError as exc:
        print(f"bench_shell_startup: {exc}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="remote-ssh-shell-bench.") as tmp:
        bench_root = Path(tmp)
        results = [
            run_named_scenario(
                name,
                reference_map,
                current_repo,
                bench_root,
                args.iterations,
                args.warmup,
                args.timeout,
            )
            for name in scenario_names
        ]

    baseline_median = baseline_ready_median(results)
    if args.format == "json":
        print(
            json.dumps(
                report_json(results, current_repo, args.iterations, args.warmup, args.timeout),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_table(results, baseline_median)

    return 1 if any(not sample.ok for result in results for sample in result.samples) else 0
