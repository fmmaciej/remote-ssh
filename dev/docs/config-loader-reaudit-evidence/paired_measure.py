"""Independent paired config-loader check; retained audit evidence only."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "dev"))
from bench.pty_runner import run_pty_sample  # noqa: E402
from bench.scenarios import scenario_environment  # noqa: E402

BASHES = ("/bin/bash", "/opt/homebrew/bin/bash")
CHANGED = ("shell/config/parse.sh", "shell/config/load.sh", "shell/config/markers.sh")
FIXTURE = (REPO / "dev/docs/config-loader-measurements/ninekeys.conf").read_bytes()
EXPECTED = dict(line.split("=", 1) for line in FIXTURE.decode().splitlines())


def check_script(expected: dict[str, str], config_owned: set[str], check_absent: bool) -> str:
    commands = []
    for key in EXPECTED:
        suffix = key.removeprefix("REMOTE_SSH_")
        source = f"REMOTE_SSH_CONFIG_SOURCE_{suffix}"
        loaded = f"REMOTE_SSH_CONFIG_LOADED_VALUE_{suffix}"
        if key in expected:
            commands.append(
                f'[[ "${{{key}+present}}" == present && "${{{key}}}" == {shlex.quote(expected[key])} ]]'
                f" || {{ printf '%s\\n' 'wrong setting: {key}' >&2; exit 41; }}"
            )
        elif check_absent:
            commands.append(
                f'[[ -z "${{{key}+present}}" ]]'
                f" || {{ printf '%s\\n' 'unexpected setting: {key}' >&2; exit 42; }}"
            )
        if key in config_owned:
            commands.append(
                f'[[ "${{{source}-}}" == config && "${{{loaded}+present}}" == present'
                f' && "${{{loaded}}}" == {shlex.quote(expected[key])} ]]'
                f" || {{ printf '%s\\n' 'wrong provenance: {key}' >&2; exit 43; }}"
            )
        else:
            commands.append(
                f'[[ -z "${{{source}+present}}" && -z "${{{loaded}+present}}" ]]'
                f" || {{ printf '%s\\n' 'unexpected provenance: {key}' >&2; exit 44; }}"
            )
    return "\n".join(commands)


def environment(root: Path, bash: str, fixture: bytes | None) -> dict[str, str]:
    home = root / "home"
    config = home / ".config"
    state = home / ".local/state"
    shim = root / "bin"
    for directory in (home, config, state, shim):
        directory.mkdir(parents=True, exist_ok=True)
    (shim / "bash").symlink_to(bash)
    env = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "XDG_STATE_HOME": str(state),
        "PATH": f"{shim}:/usr/bin:/bin",
        "LC_ALL": "C",
        "TERM": "xterm-256color",
        "BASH_ENV": "/dev/null",
        "HISTFILE": os.devnull,
    }
    if fixture is not None:
        destination = config / "remote-ssh/config"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(fixture)
    return env


def stats(values: list[float]) -> dict:
    return {
        "samples_ms": values,
        "median_ms": statistics.median(values),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def main() -> None:
    result = {
        "method": "alternating before/after pairs; each sample asserts configuration/provenance",
        "fixture_utf8": FIXTURE.decode(),
        "fixture_sha256": hashlib.sha256(FIXTURE).hexdigest(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "loader_sampling": {"warmup": 2, "measured": 7},
        "pty_sampling": {"warmup": 2, "measured": 5},
        "loader": {},
        "pty": {},
        "trace": {},
    }
    archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD"], cwd=REPO)
    with tempfile.TemporaryDirectory(prefix="config-independent-pairs-") as temporary:
        root = Path(temporary)
        trees = {}
        for variant in ("before", "after"):
            tree = root / variant
            tree.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                bundle.extractall(tree, filter="data")
            if variant == "after":
                for relative in CHANGED:
                    (tree / relative).write_bytes((REPO / relative).read_bytes())
            trees[variant] = tree
        result["runtime_sha256"] = {
            variant: {
                relative: hashlib.sha256((tree / relative).read_bytes()).hexdigest()
                for relative in CHANGED
            }
            for variant, tree in trees.items()
        }
        for bash in BASHES:
            bash_id = "bash32" if bash == BASHES[0] else "bash53"
            result["loader"][bash] = {}
            result["pty"][bash] = {}
            for case in ("control", "disabled", "missing", "empty", "ninekeys"):
                samples = {variant: [] for variant in trees}
                for index in range(9):
                    order = ("before", "after") if index % 2 == 0 else ("after", "before")
                    for variant in order:
                        fixture = (
                            FIXTURE
                            if case in {"disabled", "ninekeys"}
                            else b""
                            if case == "empty"
                            else None
                        )
                        env = environment(
                            root / "loader" / bash_id / case / str(index) / variant, bash, fixture
                        )
                        if case == "disabled":
                            env["REMOTE_SSH_CONFIG"] = "0"
                        if case == "control":
                            command = ":"
                        else:
                            expected = EXPECTED if case == "ninekeys" else {}
                            command = (
                                '. "$1/shell/config.lib.sh"; remote_ssh_config_load\n'
                                + check_script(expected, set(expected), True)
                            )
                        command += "\nprintf '%s\\n' OK"
                        start = time.perf_counter_ns()
                        completed = subprocess.run(
                            [
                                bash,
                                "--noprofile",
                                "--norc",
                                "-c",
                                command,
                                "_",
                                str(trees[variant]),
                            ],
                            env=env,
                            cwd=trees[variant],
                            capture_output=True,
                            check=True,
                            timeout=20,
                        )
                        elapsed = (time.perf_counter_ns() - start) / 1_000_000
                        if completed.stdout != b"OK\n" or completed.stderr:
                            raise RuntimeError(f"Unexpected loader output: {completed!r}")
                        if index >= 2:
                            samples[variant].append(elapsed)
                result["loader"][bash][case] = {
                    variant: stats(values) for variant, values in samples.items()
                }
                print(
                    "loader",
                    bash,
                    case,
                    {
                        variant: round(statistics.median(values), 2)
                        for variant, values in samples.items()
                    },
                    flush=True,
                )
            for scenario in ("remote-ssh-min", "remote-ssh-welcome"):
                for config in ("missing", "ninekeys"):
                    samples = {variant: [] for variant in trees}
                    for index in range(7):
                        order = ("before", "after") if index % 2 == 0 else ("after", "before")
                        for variant in order:
                            sample_root = (
                                root / "pty" / bash_id / scenario / config / str(index) / variant
                            )
                            parent = environment(sample_root / "parent", bash, None)
                            env = scenario_environment(
                                scenario, parent, sample_root / "session", trees[variant]
                            )
                            if config == "ninekeys":
                                destination = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh/config"
                                destination.parent.mkdir(parents=True)
                                destination.write_bytes(FIXTURE)
                            expected = dict(EXPECTED) if config == "ninekeys" else {}
                            owned = set(expected)
                            for key in EXPECTED:
                                if key in env:
                                    expected[key] = env[key]
                                    owned.discard(key)
                            marker = f"__PAIRED_READY_{index}_{variant}__"
                            command = (
                                check_script(expected, owned, False)
                                + f"\nprintf '%s\\n' {shlex.quote(marker)}"
                            )
                            args = [
                                bash,
                                "--rcfile",
                                str(trees[variant] / "shell/rc.sh"),
                                "-i",
                                "-c",
                                command,
                            ]
                            sample = run_pty_sample(args, env, trees[variant], marker, 20)
                            if not sample.ok:
                                raise RuntimeError(
                                    f"Invalid PTY sample {bash}/{scenario}/{config}/{variant}: {sample!r}"
                                )
                            if index >= 2:
                                samples[variant].append(sample.ready_ms)
                    label = f"{scenario}/{config}"
                    result["pty"][bash][label] = {
                        variant: stats(values) for variant, values in samples.items()
                    }
                    print(
                        "pty",
                        bash,
                        label,
                        {
                            variant: round(statistics.median(values), 2)
                            for variant, values in samples.items()
                        },
                        flush=True,
                    )
        # Instrumentation is separate from timed samples: count Bash process
        # contexts in xtrace, not all kernel processes or system calls.
        bash = BASHES[1]
        for variant, tree in trees.items():
            env = environment(root / "trace" / variant, bash, FIXTURE)
            command = "PS4='+pid=${BASHPID} sub=${BASH_SUBSHELL} '; set -x\n"
            command += '. "$1/shell/config.lib.sh"; remote_ssh_config_load\n'
            command += check_script(EXPECTED, set(EXPECTED), True)
            traced = subprocess.run(
                [bash, "--noprofile", "--norc", "-c", command, "_", str(tree)],
                env=env,
                cwd=tree,
                capture_output=True,
                check=True,
                timeout=20,
            )
            (OUTPUT / f"trace-{variant}.txt").write_bytes(traced.stderr)
            contexts = re.findall(rb"^\++pid=(\d+) sub=(\d+) ", traced.stderr, flags=re.M)
            result["trace"][variant] = {
                "distinct_bash_pids": len({pid for pid, _ in contexts}),
                "max_bash_subshell_depth": max(int(depth) for _, depth in contexts),
                "traced_commands": len(contexts),
            }
    (OUTPUT / "paired-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print("trace", result["trace"], flush=True)


if __name__ == "__main__":
    main()
