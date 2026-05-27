from __future__ import annotations

import json
import sys
from pathlib import Path

import bench_shell_startup
import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd


def test_series_stats_are_deterministic() -> None:
    assert bench_shell_startup.series_stats([4.0, 1.0, 3.0, 2.0]) == {
        "median": 2.5,
        "p95": 4.0,
        "min": 1.0,
        "max": 4.0,
    }


def test_scenario_environment_is_isolated(repo_dir: Path, tmp_path: Path) -> None:
    parent_env = {
        "HOME": "/real-home",
        "PATH": "/usr/bin:/bin",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "NO_COLOR": "1",
    }

    env = bench_shell_startup.scenario_environment(
        "remote-ssh-default",
        parent_env,
        tmp_path / "scenario",
        repo_dir,
    )

    assert env["HOME"] == str(tmp_path / "scenario" / "home")
    assert env["XDG_CONFIG_HOME"] == str(tmp_path / "scenario" / "home" / ".config")
    assert env["XDG_STATE_HOME"] == str(tmp_path / "scenario" / "home" / ".local" / "state")
    assert env["PATH"] == "/usr/bin:/bin"
    assert "REMOTE_SSH_WELCOME" not in env
    assert "REMOTE_SSH_UPDATE_CHECK" not in env
    assert "NO_COLOR" not in env
    assert (
        tmp_path / "scenario" / "home" / ".local" / "state" / "remote-ssh" / "update-check"
    ).exists()


def run_bench_json(repo_dir: Path, isolated_env: IsolatedEnv, scenario: str) -> dict[str, object]:
    result = run_cmd(
        [
            sys.executable,
            repo_dir / "dev" / "bench_shell_startup.py",
            "--iterations",
            "1",
            "--warmup",
            "0",
            "--scenario",
            scenario,
            "--format",
            "json",
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    return json.loads(result.stdout)


@pytest.mark.parametrize("scenario", bench_shell_startup.SCENARIO_ORDER)
def test_cli_json_scenarios_run(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    scenario: str,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, scenario)
    scenario_names = [item["name"] for item in data["scenarios"]]

    assert data["iterations"] == 1
    assert data["warmup"] == 0
    assert scenario in scenario_names
    for item in data["scenarios"]:
        assert item["summary"]["failed"] == 0
        assert len(item["samples"]) == 1
        assert item["samples"][0]["ready_ms"] >= 0
        assert "output_tail" not in item["samples"][0]


def test_cli_json_adds_baseline_for_single_remote_scenario(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "remote-ssh-default")

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "remote-ssh-default",
    ]
    summary = data["scenarios"][1]["summary"]
    assert summary["ratio_ready_vs_baseline"] is not None
    assert summary["delta_ready_ms_vs_baseline"] is not None


def test_cli_json_does_not_duplicate_requested_baseline(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "bash-baseline")

    assert [item["name"] for item in data["scenarios"]] == ["bash-baseline"]


def test_sample_json_includes_output_tail_only_for_failures() -> None:
    ok_sample = bench_shell_startup.Sample(
        ready_ms=1.0,
        total_ms=2.0,
        returncode=0,
        timed_out=False,
        output_tail="successful output",
    )
    failed_sample = bench_shell_startup.Sample(
        ready_ms=None,
        total_ms=2.0,
        returncode=1,
        timed_out=False,
        output_tail="failure output",
    )

    assert "output_tail" not in bench_shell_startup.sample_to_json(ok_sample)
    assert bench_shell_startup.sample_to_json(failed_sample)["output_tail"] == "failure output"


def test_cli_json_remote_ssh_min_does_not_require_ssh(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "remote-ssh-min")

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "remote-ssh-min",
    ]
    assert data["scenarios"][1]["summary"]["failed"] == 0
