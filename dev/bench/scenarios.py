from __future__ import annotations

import os
import shlex
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from bench.model import BenchConfigError, ReferenceScenario, Sample, ScenarioResult
from bench.pty_runner import run_pty_sample

MEASURED_SCENARIO_ORDER = (
    "bash-baseline",
    "remote-ssh-min",
    "remote-ssh-welcome",
    "remote-ssh-default",
    "remote-ssh-default-preseed",
    "remote-ssh-default-warm-home",
)
SCENARIO_ORDER = MEASURED_SCENARIO_ORDER
SCENARIO_SUITES = {
    "login": (
        "remote-ssh-min",
        "remote-ssh-default",
        "remote-ssh-default-warm-home",
    ),
}

MEASURED_SCENARIO_DESCRIPTIONS = {
    "bash-baseline": "bash --noprofile --norc",
    "remote-ssh-min": "remote-ssh rc.sh with welcome/update disabled",
    "remote-ssh-welcome": "remote-ssh welcome, update disabled, user modules disabled",
    "remote-ssh-default": "remote-ssh default with fresh local update cache",
    "remote-ssh-default-preseed": (
        "remote-ssh default with fresh HOME and once-per-HOME state preseeded"
    ),
    "remote-ssh-default-warm-home": "remote-ssh default with one warmed isolated HOME",
}

REMOTE_SSH_ENV_PREFIX = "REMOTE_SSH_"
NO_COLOR_ENV = "NO_COLOR"
ATUIN_IMPORT_MARKER = "atuin-import-auto.done"
WARM_HOME_SCENARIOS = frozenset({"remote-ssh-default-warm-home"})


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
    elif scenario_name in {
        "remote-ssh-default",
        "remote-ssh-default-preseed",
        "remote-ssh-default-warm-home",
    }:
        write_fresh_update_cache(xdg_state_home)
        if scenario_name == "remote-ssh-default-preseed":
            write_atuin_import_marker(xdg_state_home)

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


def write_atuin_import_marker(xdg_state_home: Path) -> None:
    state_dir = xdg_state_home / "remote-ssh"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / ATUIN_IMPORT_MARKER).write_text("", encoding="utf-8")


def shell_command(marker: str) -> str:
    return f"printf '%s\\n' {shlex.quote(marker)}"


def scenario_args(scenario_name: str, current_repo: Path, marker: str) -> list[str]:
    command = shell_command(marker)
    if scenario_name == "bash-baseline":
        return ["bash", "--noprofile", "--norc", "-i", "-c", command]
    return ["bash", "--rcfile", str(current_repo / "shell" / "rc.sh"), "-i", "-c", command]


def run_sample(
    scenario_name: str,
    current_repo: Path,
    bench_root: Path,
    sample_index: int,
    timeout_seconds: float,
    sample_dir: Path | None = None,
) -> Sample:
    marker = f"__REMOTE_SSH_BENCH_READY_{os.getpid()}_{sample_index}__"
    if sample_dir is None:
        sample_dir = bench_root / scenario_name / str(sample_index)
    env = scenario_environment(scenario_name, os.environ, sample_dir, current_repo)
    args = scenario_args(scenario_name, current_repo, marker)
    return run_pty_sample(args, env, current_repo, marker, timeout_seconds)


def warm_home_sample_dir(bench_root: Path, scenario_name: str) -> Path:
    return bench_root / scenario_name / "shared-home"


def run_scenario(
    scenario_name: str,
    current_repo: Path,
    bench_root: Path,
    iterations: int,
    warmup: int,
    timeout_seconds: float,
) -> ScenarioResult:
    sample_dir = None
    if scenario_name in WARM_HOME_SCENARIOS:
        sample_dir = warm_home_sample_dir(bench_root, scenario_name)
        run_sample(
            scenario_name,
            current_repo,
            bench_root,
            -warmup - 2,
            timeout_seconds,
            sample_dir=sample_dir,
        )

    for index in range(warmup):
        run_sample(
            scenario_name,
            current_repo,
            bench_root,
            -index - 1,
            timeout_seconds,
            sample_dir=sample_dir,
        )

    samples = tuple(
        run_sample(
            scenario_name,
            current_repo,
            bench_root,
            index,
            timeout_seconds,
            sample_dir=sample_dir,
        )
        for index in range(iterations)
    )
    return ScenarioResult(
        name=scenario_name,
        description=MEASURED_SCENARIO_DESCRIPTIONS[scenario_name],
        samples=samples,
    )


def run_reference_scenario(reference: ReferenceScenario) -> ScenarioResult:
    sample = Sample(
        ready_ms=reference.ready_ms,
        total_ms=reference.total_ms,
        returncode=0,
        timed_out=False,
        output_tail="",
    )
    return ScenarioResult(
        name=reference.name,
        description=reference.description,
        samples=(sample,),
        source="reference",
    )


def run_named_scenario(
    scenario_name: str,
    reference_map: Mapping[str, ReferenceScenario],
    current_repo: Path,
    bench_root: Path,
    iterations: int,
    warmup: int,
    timeout_seconds: float,
) -> ScenarioResult:
    reference = reference_map.get(scenario_name)
    if reference is not None:
        return run_reference_scenario(reference)
    return run_scenario(scenario_name, current_repo, bench_root, iterations, warmup, timeout_seconds)


def default_scenario_names(reference_names: Sequence[str]) -> tuple[str, ...]:
    return (
        "bash-baseline",
        *reference_names,
        *(name for name in MEASURED_SCENARIO_ORDER if name != "bash-baseline"),
    )


def dedupe_names(names: Sequence[str]) -> tuple[str, ...]:
    selected: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        selected.append(name)
    return tuple(selected)


def expand_scenario_suites(requested_suites: Sequence[str] | None) -> tuple[str, ...]:
    if not requested_suites:
        return ()

    names: list[str] = []
    unknown: list[str] = []
    for suite in requested_suites:
        suite_names = SCENARIO_SUITES.get(suite)
        if suite_names is None:
            unknown.append(suite)
            continue
        names.extend(suite_names)

    if unknown:
        available_text = ", ".join(sorted(SCENARIO_SUITES))
        unknown_text = ", ".join(unknown)
        raise BenchConfigError(f"unknown suite: {unknown_text}; available: {available_text}")

    return dedupe_names(names)


def selected_scenario_names(
    requested: Sequence[str] | None,
    reference_names: Sequence[str],
) -> tuple[str, ...]:
    if not requested:
        return default_scenario_names(reference_names)
    if "bash-baseline" in requested:
        return dedupe_names(tuple(requested))

    names = ["bash-baseline"]
    if any(name in MEASURED_SCENARIO_DESCRIPTIONS for name in requested):
        names.extend(reference_names)
    names.extend(requested)
    return dedupe_names(names)


def validate_scenario_names(
    scenario_names: Sequence[str],
    reference_map: Mapping[str, ReferenceScenario],
) -> None:
    available = {*MEASURED_SCENARIO_DESCRIPTIONS, *reference_map}
    unknown = [name for name in scenario_names if name not in available]
    if unknown:
        available_text = ", ".join(sorted(available))
        unknown_text = ", ".join(unknown)
        raise BenchConfigError(f"unknown scenario: {unknown_text}; available: {available_text}")
