"""One task-only paired diagnostic of frozen/current cold Atuin editor startup.

This compares enabled editor implementations, not the 30/60 ms acceptance gate.
All samples and the pre-sampling declaration are preserved. No downloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any

parser = argparse.ArgumentParser(description=__doc__)
for name in ("repo", "bash", "library", "atuin", "skim", "starship", "before", "output"):
    parser.add_argument(f"--{name}", type=Path, required=True)
args = parser.parse_args()
for name in ("repo", "bash", "library", "atuin", "skim", "starship", "before", "output"):
    setattr(args, name, getattr(args, name).resolve())
sys.path.insert(0, str(args.repo / "dev"))
sys.path.insert(0, str(args.repo / "dev/flyline"))
sys.path.insert(0, str(args.repo / "dev/docs/interactive-tools-performance-evidence"))
import managed  # noqa: E402
from bench.scenarios import run_sample  # noqa: E402
from bench.stats import series_stats  # noqa: E402
from benchmark import environment  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


args.output.mkdir(parents=True, exist_ok=False)
if sha(args.library) != "ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57":
    parser.error("Requires unchanged qualified R5 library")
current = args.repo / "shell/rc.d/29-flyline.sh"
declaration = {
    "purpose": "Causal diagnostic only; not startup acceptance and cannot invalidate either full failed gate",
    "pairs": 20,
    "warmup_per_variant": 2,
    "scenario": "remote-ssh-flyline-on-atuin",
    "order": "before,current on even pair; current,before on odd pair; same pattern for warmups",
    "difference": "Only frozen/current shell/rc.d/29-flyline.sh bytes in equal-length isolated checkout roots",
    "environment": "Existing run_sample cold-HOME semantics and identical allowlisted native inputs; one common managed prefix",
    "failures": "All 40 measured samples retained; state mismatch or timeout nonzero; no overhead acceptance threshold applied",
    "no_concurrent_tests_or_benchmarks": True,
    "source_sha256": {"before": sha(args.before), "current": sha(current)},
    "input_sha256": {name: sha(getattr(args, name)) for name in ("bash", "library", "atuin", "skim", "starship")},
    "script_sha256": sha(Path(__file__)),
}
(args.output / "declaration.json").write_text(json.dumps(declaration, indent=2) + "\n")
results: list[dict[str, Any]] = []
warmups: list[dict[str, Any]] = []
with tempfile.TemporaryDirectory(prefix="flyline-paired-startup-") as directory:
    home = Path(directory)
    for sub in ("config", "data", "state", "cache", "bin"):
        (home / sub).mkdir()
    for name, path in (("bash", args.bash), ("atuin", args.atuin), ("sk", args.skim), ("starship", args.starship)):
        (home / "bin" / name).symlink_to(path)
    env = environment(home, home / "bin")
    candidate = managed.install(args.repo, args.bash, args.library, home, env)
    before = home / "oldcheck"
    shutil.copytree(candidate, before)
    (before / "shell/rc.d/29-flyline.sh").write_bytes(args.before.read_bytes())
    # Verify copied runtime bytes differ only in the declared module.
    differences = []
    for path in candidate.rglob("*"):
        if path.is_file() and not path.is_symlink():
            relative = path.relative_to(candidate)
            if path.read_bytes() != (before / relative).read_bytes():
                differences.append(str(relative))
    if differences != ["shell/rc.d/29-flyline.sh"]:
        raise RuntimeError(f"Unexpected fixture differences: {differences}")
    checkouts = {"before": before, "current": candidate}
    os.environ.clear()
    os.environ.update(env)
    for pair in range(-2, 20):
        order = ("before", "current") if pair % 2 == 0 else ("current", "before")
        for variant in order:
            sample = run_sample(
                "remote-ssh-flyline-on-atuin", checkouts[variant], home / "samples",
                pair, 10, sample_dir=home / "samples" / str(pair) / variant,
            )
            row = {"pair": pair, "variant": variant, "ready_ms": sample.ready_ms,
                   "returncode": sample.returncode, "timed_out": sample.timed_out,
                   "output_tail": sample.output_tail,
                   "valid": sample.ready_ms is not None and sample.returncode == 0 and not sample.timed_out}
            (warmups if pair < 0 else results).append(row)
            print(json.dumps(row), flush=True)
    (args.output / "install.txt").write_text((home / "install.log").read_text())
valid = all(row["valid"] for row in results + warmups)
stats = {}
for variant in ("before", "current"):
    values = [row["ready_ms"] for row in results if row["variant"] == variant and row["valid"]]
    stats[variant] = series_stats(values) if values else None
paired = [{"pair": pair, "current_minus_before_ms":
           next(row["ready_ms"] for row in results if row["pair"] == pair and row["variant"] == "current")
           - next(row["ready_ms"] for row in results if row["pair"] == pair and row["variant"] == "before")}
          for pair in range(20)] if valid else []
report = {"declaration": declaration, "warmups": warmups, "results": results,
          "stats": stats, "paired_deltas": paired,
          "paired_median_delta_ms": statistics.median(row["current_minus_before_ms"] for row in paired) if paired else None,
          "difference_of_medians_ms": (stats["current"]["median"] - stats["before"]["median"]) if stats["current"] and stats["before"] else None,
          "valid": valid,
          "acceptance": "No acceptance judgment; both full-startup failures remain unmet"}
(args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"stats": stats, "paired_median_delta_ms": report["paired_median_delta_ms"], "valid": valid}), flush=True)
raise SystemExit(0 if valid else 1)
