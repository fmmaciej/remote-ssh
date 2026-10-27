"""One-off execution evidence for the config loader refactor, not a public CLI."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARTIFACTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "dev"))

from bench.pty_runner import run_pty_sample  # noqa: E402
from bench.scenarios import clean_parent_env, scenario_args, scenario_environment  # noqa: E402

BASHES = ("/bin/bash", "/opt/homebrew/bin/bash")
RUNTIME_FILES = ("shell/config/parse.sh", "shell/config/load.sh", "shell/config/markers.sh")


def summarize(samples: list[float]) -> dict[str, float | list[float]]:
    ordered = sorted(samples)
    return {
        "samples_ms": samples,
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "p95_ms": ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)],
    }


def freeze_fixture() -> bytes:
    fixture_path = ARTIFACTS / "ninekeys.conf"
    if not fixture_path.exists():
        entries = subprocess.run(
            [
                BASHES[0],
                "--noprofile",
                "--norc",
                "-c",
                '. "$1/shell/config/entries.sh"; remote_ssh_config_entries',
                "_",
                str(REPO),
            ],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
        fixture_path.write_text(
            "".join(
                f"{key}={'' if default == '[unset]' else default}\n"
                for key, default in (line.split("|", 1) for line in entries.splitlines())
            )
        )
    return fixture_path.read_bytes()


def setup_fixture(env: dict[str, str], fixture: bytes | None) -> None:
    if fixture is not None:
        path = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fixture)


def parent_environment(shim: Path) -> dict[str, str]:
    env = clean_parent_env(os.environ)
    for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS"):
        env.pop(name, None)
    env.update({"PATH": f"{shim}:/usr/bin:/bin", "LC_ALL": "C", "TERM": "xterm-256color"})
    return env


def measure_loader(bash: str, root: Path, parent: dict[str, str], fixture: bytes) -> dict:
    results = {}
    for case in ("baseline", "disabled", "missing", "empty", "ninekeys"):
        sample_dir = root / "loader" / case
        sample_dir.mkdir(parents=True)
        env = scenario_environment("bash-baseline", parent, sample_dir, REPO)
        setup_fixture(
            env, fixture if case in {"disabled", "ninekeys"} else b"" if case == "empty" else None
        )
        if case == "disabled":
            env["REMOTE_SSH_CONFIG"] = "0"
        command = (
            ":" if case == "baseline" else '. "$1/shell/config.lib.sh"; remote_ssh_config_load'
        )
        args = [bash, "--noprofile", "--norc", "-c", command, "_", str(REPO)]
        samples = []
        for index in range(8):
            start = time.perf_counter_ns()
            result = subprocess.run(args, env=env, cwd=REPO, capture_output=True, timeout=20)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            if result.returncode or result.stdout or result.stderr:
                raise RuntimeError(f"loader {case} failed: {result!r}")
            if index:
                samples.append(elapsed)
        results[case] = summarize(samples)
        print(f"loader {bash} {case}: {results[case]['median_ms']:.3f} ms", flush=True)
    return results


def measure_startup(bash: str, root: Path, parent: dict[str, str], fixture: bytes) -> dict:
    results = {}
    for scenario in ("bash-baseline", "remote-ssh-min", "remote-ssh-welcome"):
        for config in ("missing", "ninekeys"):
            samples = []
            for index in range(23):
                sample_dir = root / "pty" / scenario / config / str(index)
                # Each config belongs to this freshly generated HOME, after setup.
                env = scenario_environment(scenario, parent, sample_dir, REPO)
                setup_fixture(env, fixture if config == "ninekeys" else None)
                marker = f"__CONFIG_MEASURE_READY_{os.getpid()}_{index}__"
                args = scenario_args(scenario, REPO, marker)
                args[0] = bash
                sample = run_pty_sample(args, env, REPO, marker, 20)
                if not sample.ok:
                    raise RuntimeError(f"startup {bash}/{scenario}/{config}: {sample!r}")
                if index >= 3:
                    samples.append(dataclasses.asdict(sample))
            key = f"{scenario}/{config}"
            results[key] = {
                "samples": samples,
                "ready": summarize([sample["ready_ms"] for sample in samples]),
                "total": summarize([sample["total_ms"] for sample in samples]),
            }
            print(
                f"pty {bash} {key}: {results[key]['ready']['median_ms']:.3f} ms ready", flush=True
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    parser.add_argument("--mode", choices=("loader", "pty"), required=True)
    parser.add_argument("--bash", choices=BASHES, required=True)
    args = parser.parse_args()
    fixture = freeze_fixture()
    with tempfile.TemporaryDirectory(prefix="config-loader-measure-") as directory:
        root = Path(directory)
        shim = root / "bin"
        shim.mkdir()
        (shim / "bash").symlink_to(args.bash)
        parent = parent_environment(shim)
        results = (
            measure_loader(args.bash, root, parent, fixture)
            if args.mode == "loader"
            else measure_startup(args.bash, root, parent, fixture)
        )
        output = {
            "checkpoint": args.checkpoint,
            "mode": args.mode,
            "bash": args.bash,
            "bash_version": subprocess.run(
                [args.bash, "--version"], capture_output=True, text=True, check=True
            ).stdout.splitlines()[0],
            "os": platform.platform(),
            "python": sys.version,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "repo": str(REPO),
            "fixture_utf8": fixture.decode(),
            "fixture_sha256": hashlib.sha256(fixture).hexdigest(),
            "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "runtime_files": {
                name: {
                    "sha256": hashlib.sha256((REPO / name).read_bytes()).hexdigest(),
                    "source": (REPO / name).read_text(),
                }
                for name in RUNTIME_FILES
            },
            "environment": {
                "PATH": "<temporary bash shim>:/usr/bin:/bin",
                "LC_ALL": "C",
                "TERM": "xterm-256color",
                "cleaned": "REMOTE_SSH_*, NO_COLOR, BASH_ENV, ENV, SHELLOPTS, BASHOPTS",
                "loader_home": "isolated; fresh per case, reused across 1 warmup + 7 samples",
                "pty_home": "isolated; fresh for every warmup and measured sample",
                "scenario_overrides": {
                    name: {
                        key: value
                        for key, value in scenario_environment(
                            name, parent, root / "metadata" / name, REPO
                        ).items()
                        if key.startswith("REMOTE_SSH_")
                    }
                    for name in ("bash-baseline", "remote-ssh-min", "remote-ssh-welcome")
                },
                "optional_tools": {
                    tool: shutil.which(tool, path=parent["PATH"])
                    for tool in ("starship", "atuin", "fzf", "navi", "eza", "bat", "git", "python3")
                },
            },
            "sampling": {
                "warmup": 1 if args.mode == "loader" else 3,
                "measured": 7 if args.mode == "loader" else 20,
            },
            "command": shlex.join(sys.argv),
            "results": results,
        }
    label = "bash32" if args.bash == BASHES[0] else "bash53"
    output_path = ARTIFACTS / f"{args.checkpoint}-{args.mode}-{label}.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(output_path, flush=True)


if __name__ == "__main__":
    main()
