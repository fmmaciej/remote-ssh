"""Isolated developer-only Atuin comparison using the existing PTY benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

from bench.pty_runner import run_pty_sample
from bench.scenarios import scenario_args, scenario_environment, write_atuin_import_marker


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--atuin", type=Path, required=True)
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=15)
    args = parser.parse_args()
    repo = args.repo.resolve()
    version = subprocess.check_output([str(args.atuin), "--version"], text=True).strip()
    if not version.startswith("atuin 18.14.1 "):
        raise RuntimeError(f"expected pinned Atuin 18.14.1, got {version}")
    fingerprints = {
        str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in ("shell", "dots/atuin")
        for p in sorted((repo / directory).rglob("*"))
        if p.is_file()
    }
    results = {}
    with tempfile.TemporaryDirectory(prefix="atuin-startup-measure.") as tmp:
        for case in ("disabled", "absent", "working-preseed", "first-import"):
            samples = []
            for index in range(-2, args.iterations):
                sample_dir = Path(tmp) / case / str(index)
                env = scenario_environment("remote-ssh-min", {}, sample_dir, repo)
                home = Path(env["HOME"])
                bindir = home / ".local/bin"
                bindir.mkdir(parents=True)
                (bindir / "bash").symlink_to(args.bash.resolve())
                if case != "absent":
                    (bindir / "atuin").symlink_to(args.atuin.resolve())
                env.update(
                    {
                        "PATH": f"{bindir}:/usr/bin:/bin",
                        "TERM": "xterm-256color",
                        "XDG_DATA_HOME": str(home / ".local/share"),
                        "XDG_CACHE_HOME": str(home / ".cache"),
                        "REMOTE_SSH_CONFIG": "0",
                        "REMOTE_SSH_ENABLE_ATUIN": "0" if case == "disabled" else "1",
                        "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
                    }
                )
                if case != "first-import":
                    write_atuin_import_marker(Path(env["XDG_STATE_HOME"]))
                else:
                    (home / ".bash_history").write_text("echo isolated-import-marker\n")
                marker = f"ATUIN_MEASURE_READY_{os.getpid()}_{index}"
                command = scenario_args("remote-ssh-min", repo, marker)
                command[0] = str(args.bash.resolve())
                sample = run_pty_sample(command, env, repo, marker, 10)
                if not sample.ok:
                    raise RuntimeError(sample)
                if index >= 0:
                    samples.append(asdict(sample))
            ready = [s["ready_ms"] for s in samples]
            results[case] = {"samples": samples, "median_ready_ms": statistics.median(ready)}
    args.output.write_text(
        json.dumps(
            {
                "platform": platform.platform(),
                "atuin_version": version,
                "atuin_sha256": hashlib.sha256(args.atuin.read_bytes()).hexdigest(),
                "bash_version": subprocess.check_output(
                    [str(args.bash), "--version"], text=True
                ).splitlines()[0],
                "iterations": args.iterations,
                "warmup": 2,
                "repo": str(repo),
                "bash": str(args.bash.resolve()),
                "atuin": str(args.atuin.resolve()),
                "source_sha256": fingerprints,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
