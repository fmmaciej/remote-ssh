"""Frozen, local welcome comparison; no runtime code is supplied by this harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import select
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "frozen_bench"))
from bench.model import Sample  # noqa: E402
from bench.pty_runner import run_pty_sample  # noqa: E402
from bench.scenarios import scenario_args, scenario_environment  # noqa: E402

BASE_SHA = "39226a2d9074acf08279e7c3edde6a51cc2a629c"
BASHES = {"3.2": "/bin/bash", "5.3": "/opt/homebrew/bin/bash"}
MARKER = "__WELCOME_FIRST_COMMAND_READY__"
SCRATCH = Path("/private/tmp/remote-ssh-welcome-measurements")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(repo: Path) -> dict:
    records = []
    for dirname in ("shell", "lib", "tools", "bin", "dots", "scripts"):
        for path in sorted((repo / dirname).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                records.append(
                    {
                        "path": str(path.relative_to(repo)),
                        "mode": oct(path.stat().st_mode & 0o777),
                        "sha256": digest(path.read_bytes()),
                    }
                )
    return {"aggregate": digest(json.dumps(records, sort_keys=True).encode()), "files": records}


def executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755)


def manifest() -> dict:
    return json.loads((HERE / "fixtures.json").read_text())


def environment(
    repo: Path, bash: str, fixture: str, scenario: str, sample_dir: Path
) -> dict[str, str]:
    parent = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("REMOTE_SSH_", "BASH_FUNC_", "GIT_CONFIG_"))
        and k
        not in {
            "BASH_ENV",
            "ENV",
            "SHELLOPTS",
            "BASHOPTS",
            "NO_COLOR",
            "SSH_AUTH_SOCK",
            "REMOTE_ENV_DIR",
            "REMOTE_SHELL_DIR",
            "INSTALL_PREFIX",
            "INSTALL_BIN_DIR",
        }
    }
    parent.update(
        {
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "LANG": "C",
            "TERM": "xterm-256color",
            "COLUMNS": "100",
            "LINES": "40",
        }
    )
    env = scenario_environment(scenario, parent, sample_dir, repo)
    m = manifest()
    home = Path(env["HOME"])
    shim = home / "probes"
    shim.mkdir(parents=True)
    (shim / "bash").symlink_to(bash)
    for name, text in m["probes"].items():
        executable(shim / name, text)
    if fixture == "healthy":
        executable(shim / "bssh", "#!/bin/sh\nexit 0\n")
    config_dir = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config").write_text(m["config"])
    (config_dir / "expected-tools").write_text(m["expected_tools"])
    managed_bin = home / ".local" / "bin"
    managed_bin.mkdir(parents=True)
    opt = home / ".local" / "opt"
    for name, version in m["tools"].items():
        if fixture == "actionable" and name == "fd":
            continue
        target = opt / f"{name}-{version}" / name
        executable(target, "#!/bin/sh\nexit 0\n")
        (target.parent / ".remote-ssh-release").write_text(
            f"format=1\ntool={name}\nversion={version}\nlayout=binary\nexecutable={name}\n"
        )
        (managed_bin / name).symlink_to(target)
    cache = Path(env["XDG_STATE_HOME"]) / "remote-ssh" / "update-check"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(m["cache"][fixture])
    assert time.time() - m["cache_timestamp"] < 86400, (
        "cache expired; freeze a new fixture set before measuring"
    )
    env.update(
        {
            "PATH": f"{managed_bin}:{shim}:/usr/bin:/bin",
            "REMOTE_ENV_DIR": str(repo),
            "REMOTE_SHELL_DIR": str(repo / "shell"),
            "INSTALL_PREFIX": str(opt),
            "INSTALL_BIN_DIR": str(managed_bin),
            "SSH_AUTH_SOCK": str(home / "agent.sock"),
            "REMOTE_SSH_WELCOME_COLOR": "0",
            "REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "ok" if fixture == "healthy" else "missing",
        }
    )
    if fixture == "healthy":
        env["REMOTE_SSH_GIT_SESSION_IDENTITY"] = "1"
    assert "BASH_ENV" not in env and "SHELLOPTS" not in env and "BASHOPTS" not in env
    return env


def detached(args: list[str], env: dict[str, str], cwd: Path) -> tuple[Sample, str]:
    start = time.perf_counter_ns()
    proc = subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert proc.stdout is not None and proc.stderr is not None
    streams = [proc.stdout, proc.stderr]
    output = bytearray()
    errors = bytearray()
    ready = None
    deadline = time.monotonic() + 15
    timeout = False
    while streams:
        if time.monotonic() >= deadline:
            proc.kill()
            timeout = True
        readable, _, _ = select.select(streams, [], [], 0.05)
        for stream in readable:
            chunk = os.read(stream.fileno(), 4096)
            if not chunk:
                streams.remove(stream)
                continue
            (output if stream is proc.stdout else errors).extend(chunk)
            if ready is None and MARKER.encode() in output:
                ready = (time.perf_counter_ns() - start) / 1e6
    rc = proc.wait()
    return Sample(
        ready, (time.perf_counter_ns() - start) / 1e6, rc, timeout, output.decode()
    ), errors.decode()


def sample(
    repo: Path, version: str, fixture: str, workload: str, sample_id: str, *, freeze: bool = False
) -> dict:
    sample_dir = SCRATCH / sample_id
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
    scenario = "remote-ssh-default-preseed" if workload in {"isolated", "pty"} else workload
    env = environment(repo, BASHES[version], fixture, scenario, sample_dir)
    cwd = SCRATCH / "cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    if workload == "isolated":
        args = [
            BASHES[version],
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_run; printf "%s\\n" "$2"',
            "_",
            str(repo),
            MARKER,
        ]
        result, stderr = detached(args, env, cwd)
    else:
        args = scenario_args(scenario, repo, MARKER)
        # Existing PTY runner, with the same terminal dimensions for each child.
        args = ["/bin/sh", "-c", 'stty cols 100 rows 40; exec "$@"', "_", *args]
        result = run_pty_sample(args, env, cwd, MARKER, 15)
        stderr = ""  # PTY intentionally combines the child's streams.
    output = result.output_tail
    screen_path = HERE / "screens" / f"{version}-{fixture}-{workload}.txt"
    assert result.returncode == 0 and not result.timed_out and result.ready_ms is not None, asdict(
        result
    )
    assert len(output.encode()) < 128 * 1024 and output.count(MARKER) == 1
    assert stderr == "", stderr
    if workload in {"pty", "isolated"}:
        normalized = output.replace("\r\n", "\n")
        for expected in (
            "host:    fixture-host / 192.0.2.4",
            "hw:      8 cpu / 16 GiB ram",
            "tools:   2 checked / " + ("2" if fixture == "healthy" else "1") + " ok",
            "scripts: 4 checked / " + ("4" if fixture == "healthy" else "3") + " ok",
            "sw:      ssh-agent ok / git config " + ("ok" if fixture == "healthy" else "missing"),
        ):
            assert expected in normalized, (expected, output)
        assert ("next:    remote-ssh doctor" in normalized) == (fixture == "actionable")
        assert ("update:  current" if fixture == "healthy" else "update:  available") in normalized
    if freeze:
        screen_path.parent.mkdir(exist_ok=True)
        screen_path.write_bytes(output.encode())
    else:
        assert output.encode() == screen_path.read_bytes(), (screen_path, output)
    cache = Path(env["XDG_STATE_HOME"]) / "remote-ssh" / "update-check"
    assert cache.read_text() == manifest()["cache"][fixture], "update cache mutated"
    record = asdict(result) | {
        "stderr": stderr,
        "output_sha256": digest(output.encode()),
        "output_bytes": len(output.encode()),
        "complete_output_asserted": True,
        "workload": workload,
        "bash": version,
        "fixture": fixture,
        "sample_id": sample_id,
    }
    shutil.rmtree(sample_dir)
    return record


def cells(controls: bool = False) -> list[tuple[str, str, str]]:
    return (
        [
            (v, f, w)
            for v in BASHES
            for f in ("healthy",)
            if controls
            for w in ("bash-baseline", "remote-ssh-min")
        ]
        if controls
        else [
            (v, f, w)
            for v in BASHES
            for f in ("healthy", "actionable")
            for w in ("isolated", "pty")
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("freeze", "baseline", "paired", "fingerprint", "summarize")
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == "fingerprint":
        args.out.write_text(json.dumps(fingerprint(args.baseline), indent=2) + "\n")
        return
    if args.mode == "summarize":
        records = [json.loads(line) for line in args.baseline.read_text().splitlines()]
        groups = {}
        for r in records:
            if r["warmup"]:
                continue
            key = (r["batch"], r["bash"], r["fixture"], r["workload"], r["version"])
            groups.setdefault(key, []).append(r)
        summary = []
        for key, rows in groups.items():
            item = {
                "batch": key[0],
                "bash": key[1],
                "fixture": key[2],
                "workload": key[3],
                "version": key[4],
                "n": len(rows),
            }
            for measure in ("ready_ms", "total_ms"):
                values = sorted(r[measure] for r in rows)
                item[measure] = {
                    "median": statistics.median(values),
                    "p95": values[int(len(values) * 0.95) - 1],
                    "min": min(values),
                    "max": max(values),
                }
            summary.append(item)
        for item in summary:
            if item["version"] == "candidate":
                before = next(
                    r
                    for r in summary
                    if all(r[k] == item[k] for k in ("batch", "bash", "fixture", "workload"))
                    and r["version"] == "baseline"
                )
                for measure in ("ready_ms", "total_ms"):
                    delta = item[measure]["median"] - before[measure]["median"]
                    item[measure]["delta_ms"] = delta
                    item[measure]["delta_percent"] = delta / before[measure]["median"] * 100
        args.out.write_text(json.dumps(summary, indent=2) + "\n")
        return
    metadata = {
        "baseline_sha": BASE_SHA,
        "baseline": fingerprint(args.baseline),
        "candidate": fingerprint(args.candidate) if args.candidate else None,
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python": sys.version,
        "bash": {
            k: subprocess.check_output([v, "--version"], text=True).splitlines()[0]
            for k, v in BASHES.items()
        },
        "harness_sha256": digest(Path(__file__).read_bytes()),
        "fixtures_sha256": digest((HERE / "fixtures.json").read_bytes()),
        "frozen_bench": {
            str(p.relative_to(HERE)): digest(p.read_bytes())
            for p in sorted((HERE / "frozen_bench").rglob("*.py"))
        },
        "sampling": {
            "warmups": 3,
            "samples": 20,
            "order": "alternating pairs",
            "home": "fresh per sample",
            "cwd": str(SCRATCH / "cwd"),
            "BASH_ENV": "unset",
            "SHELLOPTS_BASHOPTS": "unexported",
            "terminal": "100 columns x 40 rows",
            "network": "fresh fixed cache; git shim refuses fetch/ls-remote",
        },
    }
    args.out.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with args.out.open("w") as output:
        for batch in range(1, 3 if args.mode == "paired" else 2):
            for version, fixture, workload in cells() + (cells(True) if batch == 1 else []):
                print(
                    f"batch={batch} bash={version} fixture={fixture} workload={workload}",
                    flush=True,
                )
                for index in range(1 if args.mode == "freeze" else 23):
                    order = [("baseline", args.baseline)]
                    if args.mode == "paired":
                        assert args.candidate is not None
                        order.append(("candidate", args.candidate))
                        if index % 2:
                            order.reverse()
                    for name, repo in order:
                        record = sample(
                            repo,
                            version,
                            fixture,
                            workload,
                            f"{args.mode}-{batch}-{version}-{fixture}-{workload}-{index}-{name}",
                            freeze=args.mode == "freeze",
                        )
                        record.update(
                            {
                                "batch": batch,
                                "version": name,
                                "warmup": index < 3,
                                "index": index - 3,
                            }
                        )
                        output.write(json.dumps(record) + "\n")
                        output.flush()


if __name__ == "__main__":
    main()
