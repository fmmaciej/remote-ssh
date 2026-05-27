from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from bench.model import Sample
from bench.references import reference_file_paths
from bench.report import sample_to_json
from bench.scenarios import SCENARIO_ORDER, scenario_environment
from bench.stats import series_stats
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd


def test_series_stats_are_deterministic() -> None:
    assert series_stats([4.0, 1.0, 3.0, 2.0]) == {
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

    env = scenario_environment(
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


def run_bench_json(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    scenario: str | None = None,
) -> dict[str, object]:
    args: list[str | Path] = [
        sys.executable,
        repo_dir / "dev" / "bench_shell_startup.py",
        "--iterations",
        "1",
        "--warmup",
        "0",
        "--format",
        "json",
    ]
    if scenario is not None:
        args.extend(["--scenario", scenario])

    result = run_cmd(
        args,
        env=isolated_env.env,
    )

    assert_ok(result)
    return json.loads(result.stdout)


def make_reference_repo(tmp_path: Path, default_references: str, local_references: str = "") -> Path:
    repo = tmp_path / "repo"
    (repo / "dev" / "config").mkdir(parents=True)
    (repo / "shell").mkdir()
    (repo / "shell" / "rc.sh").write_text("# test rc\n", encoding="utf-8")
    (repo / "dev" / "config" / "shell_startup_references.json").write_text(
        default_references,
        encoding="utf-8",
    )
    if local_references:
        (repo / "dev" / "config" / "shell_startup_references.local.json").write_text(
            local_references,
            encoding="utf-8",
        )
    return repo


def test_reference_paths_use_dev_config(repo_dir: Path) -> None:
    default_path, local_path = reference_file_paths(repo_dir)

    assert default_path == repo_dir / "dev" / "config" / "shell_startup_references.json"
    assert local_path == repo_dir / "dev" / "config" / "shell_startup_references.local.json"


@pytest.mark.parametrize(
    "scenario",
    ("bash-baseline", "zsh-reference", *SCENARIO_ORDER[1:]),
)
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


def test_cli_json_default_includes_references(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env)

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "zsh-reference",
        "remote-ssh-min",
        "remote-ssh-welcome",
        "remote-ssh-default",
    ]


def test_cli_json_adds_baseline_for_single_remote_scenario(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "remote-ssh-default")

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "zsh-reference",
        "remote-ssh-default",
    ]
    summary = data["scenarios"][2]["summary"]
    assert summary["ratio_ready_vs_baseline"] is not None
    assert summary["delta_ready_ms_vs_baseline"] is not None


def test_cli_json_reference_scenario_adds_baseline(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "zsh-reference")

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "zsh-reference",
    ]
    reference = data["scenarios"][1]
    assert reference["source"] == "reference"
    assert reference["samples"][0]["ready_ms"] == 200.0
    assert reference["samples"][0]["total_ms"] == 200.0
    assert reference["summary"]["slower_ready_percent_vs_baseline"] is not None
    assert "output_tail" not in reference["samples"][0]


def test_cli_json_does_not_duplicate_requested_baseline(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "bash-baseline")

    assert [item["name"] for item in data["scenarios"]] == ["bash-baseline"]


def test_sample_json_includes_output_tail_only_for_failures() -> None:
    ok_sample = Sample(
        ready_ms=1.0,
        total_ms=2.0,
        returncode=0,
        timed_out=False,
        output_tail="successful output",
    )
    failed_sample = Sample(
        ready_ms=None,
        total_ms=2.0,
        returncode=1,
        timed_out=False,
        output_tail="failure output",
    )

    assert "output_tail" not in sample_to_json(ok_sample)
    assert sample_to_json(failed_sample)["output_tail"] == "failure output"


def test_cli_json_remote_ssh_min_does_not_require_ssh(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    data = run_bench_json(repo_dir, isolated_env, "remote-ssh-min")

    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "zsh-reference",
        "remote-ssh-min",
    ]
    assert data["scenarios"][2]["summary"]["failed"] == 0


def test_reference_local_override_changes_existing_reference(
    tmp_path: Path,
    isolated_env: IsolatedEnv,
    repo_dir: Path,
) -> None:
    repo = make_reference_repo(
        tmp_path,
        (repo_dir / "dev" / "config" / "shell_startup_references.json").read_text(
            encoding="utf-8"
        ),
        """
        {
          "references": [
            {
              "name": "zsh-reference",
              "description": "Local zsh override",
              "ready_ms": 123.0,
              "total_ms": 124.0
            }
          ]
        }
        """,
    )
    result = run_cmd(
        [
            sys.executable,
            repo_dir / "dev" / "bench_shell_startup.py",
            "--repo",
            repo,
            "--iterations",
            "1",
            "--warmup",
            "0",
            "--scenario",
            "zsh-reference",
            "--format",
            "json",
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    data = json.loads(result.stdout)
    reference = data["scenarios"][1]
    assert reference["description"] == "Local zsh override"
    assert reference["samples"][0]["ready_ms"] == 123.0
    assert reference["samples"][0]["total_ms"] == 124.0


def test_reference_local_file_adds_reference(
    tmp_path: Path,
    isolated_env: IsolatedEnv,
    repo_dir: Path,
) -> None:
    repo = make_reference_repo(
        tmp_path,
        (repo_dir / "dev" / "config" / "shell_startup_references.json").read_text(
            encoding="utf-8"
        ),
        """
        {
          "references": [
            {
              "name": "zsh-dotfiles",
              "description": "Local zsh dotfiles",
              "ready_ms": 196.0,
              "total_ms": 196.5
            }
          ]
        }
        """,
    )
    result = run_cmd(
        [
            sys.executable,
            repo_dir / "dev" / "bench_shell_startup.py",
            "--repo",
            repo,
            "--iterations",
            "1",
            "--warmup",
            "0",
            "--scenario",
            "zsh-dotfiles",
            "--format",
            "json",
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    data = json.loads(result.stdout)
    assert [item["name"] for item in data["scenarios"]] == [
        "bash-baseline",
        "zsh-dotfiles",
    ]
    assert data["scenarios"][1]["source"] == "reference"
    assert data["scenarios"][1]["samples"][0]["ready_ms"] == 196.0


def test_reference_invalid_json_fails(
    tmp_path: Path,
    isolated_env: IsolatedEnv,
    repo_dir: Path,
) -> None:
    repo = make_reference_repo(tmp_path, "{")
    result = run_cmd(
        [
            sys.executable,
            repo_dir / "dev" / "bench_shell_startup.py",
            "--repo",
            repo,
            "--scenario",
            "zsh-reference",
            "--format",
            "json",
        ],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert "invalid JSON" in result.stderr


def test_reference_invalid_numeric_value_fails(
    tmp_path: Path,
    isolated_env: IsolatedEnv,
    repo_dir: Path,
) -> None:
    repo = make_reference_repo(
        tmp_path,
        """
        {
          "references": [
            {
              "name": "zsh-reference",
              "description": "Broken reference",
              "ready_ms": -1,
              "total_ms": 1
            }
          ]
        }
        """,
    )
    result = run_cmd(
        [
            sys.executable,
            repo_dir / "dev" / "bench_shell_startup.py",
            "--repo",
            repo,
            "--scenario",
            "zsh-reference",
            "--format",
            "json",
        ],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert "expected >= 0" in result.stderr
