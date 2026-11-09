"""Measure explicit Flyline startup scenarios through a temporary managed install."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import managed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import environment  # noqa: E402

from bench.scenarios import FLYLINE_SCENARIOS, run_scenario  # noqa: E402
from bench.stats import series_stats  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "bash", "library", "atuin", "skim", "starship", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    budgets = {"median_over_disabled_ms": 30, "p95_over_disabled_ms": 60}
    (args.output / "budgets.json").write_text(json.dumps(budgets, indent=2) + "\n")
    rows: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="flyline-startup-") as directory:
        home = Path(directory)
        (home / "bin").mkdir()
        for name, path in (
            ("bash", args.bash),
            ("atuin", args.atuin),
            ("sk", args.skim),
            ("starship", args.starship),
        ):
            (home / "bin" / name).symlink_to(path.resolve())
        env = environment(home, home / "bin")
        checkout = managed.install(args.repo, args.bash, args.library, home, env)
        # run_scenario deliberately reads the parent environment. This standalone
        # process supplies an allowlisted fixture environment, never user config.
        os.environ.clear()
        os.environ.update(env)
        for name in FLYLINE_SCENARIOS:
            result = run_scenario(
                name, checkout, home / "samples", args.iterations, args.warmup, 10
            )
            samples = [
                {
                    "ready_ms": s.ready_ms,
                    "returncode": s.returncode,
                    "timed_out": s.timed_out,
                    "output_tail": s.output_tail if s.returncode else "",
                }
                for s in result.samples
            ]
            valid = [
                s.ready_ms
                for s in result.samples
                if s.ready_ms is not None and s.returncode == 0 and not s.timed_out
            ]
            rows[name] = {
                "samples": samples,
                "stats": series_stats(valid) if valid else None,
                "passed": len(valid) == args.iterations,
            }
            print(
                json.dumps(
                    {"case": name, "stats": rows[name]["stats"], "passed": rows[name]["passed"]}
                ),
                flush=True,
            )
    checks = {}
    for history in ("bash", "atuin"):
        for cache in ("", "-warm-home"):
            on = rows[f"remote-ssh-flyline-on-{history}{cache}"]["stats"]
            off = rows[f"remote-ssh-flyline-off-{history}{cache}"]["stats"]
            checks[history + cache] = bool(
                on
                and off
                and on["median"] - off["median"] <= budgets["median_over_disabled_ms"]
                and on["p95"] - off["p95"] <= budgets["p95_over_disabled_ms"]
            )
    passed = all(r["passed"] for r in rows.values()) and all(checks.values())
    (args.output / "results.json").write_text(
        json.dumps(
            {
                "library_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
                "iterations": args.iterations,
                "warmup": args.warmup,
                "budgets": budgets,
                "checks": checks,
                "results": rows,
                "passed": passed,
            },
            indent=2,
        )
        + "\n"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
