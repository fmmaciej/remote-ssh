from __future__ import annotations

import argparse
import json
import math
import os
import pty
import select
import shlex
import signal
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCENARIO_ORDER = (
    "bash-baseline",
    "remote-ssh-min",
    "remote-ssh-welcome",
    "remote-ssh-default",
)

SCENARIO_DESCRIPTIONS = {
    "bash-baseline": "bash --noprofile --norc",
    "remote-ssh-min": "remote-ssh rc.sh with welcome/update disabled",
    "remote-ssh-welcome": "remote-ssh welcome, update disabled, user modules disabled",
    "remote-ssh-default": "remote-ssh default with fresh local update cache",
}

REMOTE_SSH_ENV_PREFIX = "REMOTE_SSH_"
NO_COLOR_ENV = "NO_COLOR"


@dataclass(frozen=True)
class Sample:
    ready_ms: float | None
    total_ms: float
    returncode: int | None
    timed_out: bool
    output_tail: str

    @property
    def ok(self) -> bool:
        return self.ready_ms is not None and self.returncode == 0 and not self.timed_out


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    description: str
    samples: tuple[Sample, ...]


def repo_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def clean_parent_env(parent_env: Mapping[str, str]) -> dict[str, str]:
    env = {
        key: value
        for key, value in parent_env.items()
        if not key.startswith(REMOTE_SSH_ENV_PREFIX) and key != NO_COLOR_ENV
    }
    env.setdefault("TERM", "xterm-256color")
    return env


def scenario_environment(
    scenario_name: str,
    parent_env: Mapping[str, str],
    scenario_dir: Path,
    _repo: Path,
) -> dict[str, str]:
    env = clean_parent_env(parent_env)

    home = scenario_dir / "home"
    xdg_config_home = home / ".config"
    xdg_state_home = home / ".local" / "state"
    xdg_config_home.mkdir(parents=True, exist_ok=True)
    xdg_state_home.mkdir(parents=True, exist_ok=True)

    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(xdg_config_home),
            "XDG_STATE_HOME": str(xdg_state_home),
            "HISTFILE": os.devnull,
        }
    )

    if scenario_name == "remote-ssh-min":
        env["REMOTE_SSH_WELCOME"] = "0"
        env["REMOTE_SSH_UPDATE_CHECK"] = "0"
    elif scenario_name == "remote-ssh-welcome":
        env["REMOTE_SSH_UPDATE_CHECK"] = "0"
        env["REMOTE_SSH_WELCOME_USER"] = "0"
    elif scenario_name == "remote-ssh-default":
        write_fresh_update_cache(xdg_state_home)

    return env


def write_fresh_update_cache(xdg_state_home: Path) -> None:
    state_dir = xdg_state_home / "remote-ssh"
    state_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    (state_dir / "update-check").write_text(
        "\n".join(
            [
                f"checked_at={now}",
                "checked_at_text=benchmark",
                "status=current",
                "repo=",
                "branch=",
                "upstream=",
                "local_head=",
                "remote_head=",
                "message=benchmark cache",
                "",
            ]
        ),
        encoding="utf-8",
    )


def shell_command(marker: str) -> str:
    return f"printf '%s\\n' {shlex.quote(marker)}"


def scenario_args(scenario_name: str, current_repo: Path, marker: str) -> list[str]:
    command = shell_command(marker)
    if scenario_name == "bash-baseline":
        return ["bash", "--noprofile", "--norc", "-i", "-c", command]
    return ["bash", "--rcfile", str(current_repo / "shell" / "rc.sh"), "-i", "-c", command]


def wait_status_to_returncode(status: int) -> int:
    if hasattr(os, "waitstatus_to_exitcode"):
        return os.waitstatus_to_exitcode(status)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    return 1


def terminate_child(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    time.sleep(0.05)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def run_pty_sample(
    args: Sequence[str],
    env: Mapping[str, str],
    cwd: Path,
    marker: str,
    timeout_seconds: float,
) -> Sample:
    marker_bytes = marker.encode()
    search_buffer = b""
    output_limit = 128 * 1024
    output_tail = bytearray()

    start_ns = time.perf_counter_ns()
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(cwd)
        os.execvpe(args[0], list(args), dict(env))

    ready_ns: int | None = None
    returncode: int | None = None
    timed_out = False
    deadline = time.monotonic() + timeout_seconds

    try:
        while True:
            waited_pid, status = os.waitpid(pid, os.WNOHANG)
            if waited_pid == pid:
                returncode = wait_status_to_returncode(status)

            remaining = max(0.0, deadline - time.monotonic())
            if returncode is None and remaining <= 0:
                timed_out = True
                terminate_child(pid)
                waited_pid, status = os.waitpid(pid, 0)
                if waited_pid == pid:
                    returncode = wait_status_to_returncode(status)
                break

            read_timeout = 0.0 if returncode is not None else min(0.05, remaining)
            readable, _, _ = select.select([fd], [], [], read_timeout)
            if readable:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    chunk = b""
                if not chunk:
                    if returncode is not None:
                        break
                    continue

                output_tail.extend(chunk)
                if len(output_tail) > output_limit:
                    del output_tail[: len(output_tail) - output_limit]

                search_buffer = (search_buffer + chunk)[-4096:]
                if ready_ns is None and marker_bytes in search_buffer:
                    ready_ns = time.perf_counter_ns()
                continue

            if returncode is not None:
                break
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    total_ns = time.perf_counter_ns()
    ready_ms = None if ready_ns is None else (ready_ns - start_ns) / 1_000_000
    total_ms = (total_ns - start_ns) / 1_000_000
    return Sample(
        ready_ms=ready_ms,
        total_ms=total_ms,
        returncode=returncode,
        timed_out=timed_out,
        output_tail=output_tail.decode(errors="replace"),
    )


def run_sample(
    scenario_name: str,
    current_repo: Path,
    bench_root: Path,
    sample_index: int,
    timeout_seconds: float,
) -> Sample:
    marker = f"__REMOTE_SSH_BENCH_READY_{os.getpid()}_{sample_index}__"
    sample_dir = bench_root / scenario_name / str(sample_index)
    env = scenario_environment(scenario_name, os.environ, sample_dir, current_repo)
    args = scenario_args(scenario_name, current_repo, marker)
    return run_pty_sample(args, env, current_repo, marker, timeout_seconds)


def run_scenario(
    scenario_name: str,
    current_repo: Path,
    bench_root: Path,
    iterations: int,
    warmup: int,
    timeout_seconds: float,
) -> ScenarioResult:
    for index in range(warmup):
        run_sample(scenario_name, current_repo, bench_root, -index - 1, timeout_seconds)

    samples = tuple(
        run_sample(scenario_name, current_repo, bench_root, index, timeout_seconds)
        for index in range(iterations)
    )
    return ScenarioResult(
        name=scenario_name,
        description=SCENARIO_DESCRIPTIONS[scenario_name],
        samples=samples,
    )


def percentile_nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    rank = math.ceil((percentile / 100) * len(ordered))
    index = min(max(rank - 1, 0), len(ordered) - 1)
    return ordered[index]


def series_stats(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[midpoint]
    else:
        median = (ordered[midpoint - 1] + ordered[midpoint]) / 2
    return {
        "median": median,
        "p95": percentile_nearest_rank(ordered, 95),
        "min": ordered[0],
        "max": ordered[-1],
    }


def summarize_result(
    result: ScenarioResult,
    baseline_ready_median: float | None,
) -> dict[str, Any]:
    ok_samples = [sample for sample in result.samples if sample.ok]
    ready_values = [sample.ready_ms for sample in ok_samples if sample.ready_ms is not None]
    total_values = [sample.total_ms for sample in ok_samples]
    ready_stats = series_stats(ready_values)
    total_stats = series_stats(total_values)
    ready_median = None if ready_stats is None else ready_stats["median"]
    ratio = None
    delta = None
    if baseline_ready_median and ready_median is not None:
        ratio = ready_median / baseline_ready_median
        delta = ready_median - baseline_ready_median

    return {
        "iterations": len(result.samples),
        "failed": len(result.samples) - len(ok_samples),
        "ready_ms": ready_stats,
        "total_ms": total_stats,
        "ratio_ready_vs_baseline": ratio,
        "delta_ready_ms_vs_baseline": delta,
    }


def sample_to_json(sample: Sample) -> dict[str, Any]:
    data: dict[str, Any] = {
        "ready_ms": sample.ready_ms,
        "total_ms": sample.total_ms,
        "returncode": sample.returncode,
        "timed_out": sample.timed_out,
    }
    if not sample.ok:
        data["output_tail"] = sample.output_tail
    return data


def result_to_json(result: ScenarioResult, baseline_ready_median: float | None) -> dict[str, Any]:
    return {
        "name": result.name,
        "description": result.description,
        "samples": [sample_to_json(sample) for sample in result.samples],
        "summary": summarize_result(result, baseline_ready_median),
    }


def baseline_ready_median(results: Sequence[ScenarioResult]) -> float | None:
    for result in results:
        if result.name != "bash-baseline":
            continue
        summary = summarize_result(result, None)
        ready_stats = summary["ready_ms"]
        if ready_stats is None:
            return None
        return ready_stats["median"]
    return None


def fmt_ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def fmt_ratio(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}x"


def print_table(results: Sequence[ScenarioResult], baseline_median: float | None) -> None:
    print("Shell startup benchmark (local PTY)")
    print()
    print(
        "Scenario              n  fail  ready med  ready p95  ready min  "
        "ready max  delta   ratio  total med"
    )
    print(
        "-------------------- -- ----- ---------- ---------- ---------- "
        "---------- ------- ------ ---------"
    )
    for result in results:
        summary = summarize_result(result, baseline_median)
        ready_stats = summary["ready_ms"] or {}
        total_stats = summary["total_ms"] or {}
        print(
            f"{result.name:<20} "
            f"{summary['iterations']:>2} "
            f"{summary['failed']:>5} "
            f"{fmt_ms(ready_stats.get('median')):>10} "
            f"{fmt_ms(ready_stats.get('p95')):>10} "
            f"{fmt_ms(ready_stats.get('min')):>10} "
            f"{fmt_ms(ready_stats.get('max')):>10} "
            f"{fmt_ms(summary['delta_ready_ms_vs_baseline']):>7} "
            f"{fmt_ratio(summary['ratio_ready_vs_baseline']):>6} "
            f"{fmt_ms(total_stats.get('median')):>9}"
        )


def report_json(
    results: Sequence[ScenarioResult],
    current_repo: Path,
    iterations: int,
    warmup: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    baseline_median = baseline_ready_median(results)
    return {
        "repo": str(current_repo),
        "iterations": iterations,
        "warmup": warmup,
        "timeout_seconds": timeout_seconds,
        "scenarios": [result_to_json(result, baseline_median) for result in results],
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark remote-ssh shell startup locally.")
    parser.add_argument("--repo", type=Path, default=repo_dir(), help="remote-ssh repository path")
    parser.add_argument("--iterations", type=int, default=20, help="measured samples per scenario")
    parser.add_argument("--warmup", type=int, default=3, help="discarded warmup samples per scenario")
    parser.add_argument("--timeout", type=float, default=10.0, help="timeout per sample in seconds")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=SCENARIO_ORDER,
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


def selected_scenario_names(requested: Sequence[str] | None) -> tuple[str, ...]:
    if not requested:
        return SCENARIO_ORDER
    if "bash-baseline" in requested:
        return tuple(requested)
    return ("bash-baseline", *requested)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validate_args(args)

    current_repo = args.repo.resolve()
    scenario_names = selected_scenario_names(args.scenario)

    with tempfile.TemporaryDirectory(prefix="remote-ssh-shell-bench.") as tmp:
        bench_root = Path(tmp)
        results = [
            run_scenario(
                name,
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


if __name__ == "__main__":
    raise SystemExit(main())
