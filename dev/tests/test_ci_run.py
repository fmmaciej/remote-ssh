from __future__ import annotations

import shlex
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable

JobRow = tuple[str, str, str, str, str]


def run_ci_run(
    repo_dir: Path,
    args: Sequence[str],
    *,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["bash", repo_dir / "bin" / "ci-run", *args], env=env)


def run_ci_run_script(
    repo_dir: Path,
    args: Sequence[str],
    *,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["/bin/bash", repo_dir / "scripts" / "ci_run.sh", *args], env=env)


def write_fake_gh(bin_dir: Path, rows: Sequence[JobRow], *, exit_code: int = 0) -> None:
    payload = "\n".join("\t".join(row) for row in rows)
    write_executable(
        bin_dir / "gh",
        f"""
        #!/usr/bin/env bash

        if [[ -n "${{FAKE_GH_LOG:-}}" ]]; then
          printf '%s\\n' "$*" >>"${{FAKE_GH_LOG}}"
        fi

        if [[ {exit_code} -ne 0 ]]; then
          printf 'gh failed\\n' >&2
          exit {exit_code}
        fi

        if [[ "${{1:-}}" == "api" ]]; then
          printf '%s\\n' {shlex.quote(payload)}
          exit 0
        fi

        printf 'unexpected gh args: %s\\n' "$*" >&2
        exit 99
        """,
    )


def test_ci_run_help(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_ci_run(repo_dir, ["--help"], env=isolated_env.env)

    assert_ok(result)
    assert "Usage:" in result.stdout
    assert "ci-run status <run-id> <app-filter>" in result.stdout


def test_ci_run_status_requires_repo_outside_github_checkout(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(isolated_env.bin_dir, [])

    result = run_ci_run(repo_dir, ["status", "1234567890", "app"], env=isolated_env.env)

    assert_failed(result)
    assert result.returncode == 64
    assert "--repo owner/repo is required" in result.stderr


def test_ci_run_status_passes_when_all_matches_succeed(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [
            ("success", "completed", "success", "app | docker", "101"),
            ("success", "completed", "success", "APP | helm", "102"),
            ("success", "completed", "success", "APP | asdf", "103"),
            ("failure", "completed", "failure", "other | docker", "201"),
        ],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "ci-run status" in result.stdout
    assert "matched: 3" in result.stdout
    assert "passed:  3" in result.stdout
    assert "failed:  0" in result.stdout
    assert "pending: 0" in result.stdout
    assert "app | docker" in result.stdout
    assert "APP | helm" in result.stdout
    assert "APP | asdf" in result.stdout
    assert "All matched jobs passed." in result.stdout


def test_ci_run_status_reports_failure_and_suggests_failed_job_logs(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [
            ("success", "completed", "success", "app | docker", "101"),
            ("failure", "completed", "failure", "app | helm", "102"),
        ],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 1
    assert "failed:  1" in result.stdout
    assert "app | helm" in result.stdout
    assert "gh run view 1234567890 --repo owner/repo --job 102 --log-failed" in result.stdout
    assert "gh run view 1234567890 --repo owner/repo --job 102 --log" in result.stdout
    assert "--job 101 --log" not in result.stdout


def test_ci_run_status_reports_pending_for_running_or_unknown_jobs(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [("in_progress", "in_progress", "unknown", "app | smoke", "301")],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 2
    assert "pending: 1" in result.stdout
    assert "gh run view 1234567890 --repo owner/repo --job 301 --log-failed" in result.stdout


def test_ci_run_status_reports_no_matches(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [("success", "completed", "success", "api | docker", "401")],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 2
    assert "Jobs\n  [none]" in result.stdout
    assert "matched: 0" in result.stdout
    assert "No matching jobs; no log commands to show." in result.stdout


def test_ci_run_filter_is_case_insensitive_literal_substring(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [("success", "completed", "success", "APP | docker", "501")],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )
    assert_ok(result)
    assert "APP | docker" in result.stdout

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app.", "--repo", "owner/repo"],
        env=isolated_env.env,
    )
    assert_failed(result)
    assert result.returncode == 2
    assert "matched: 0" in result.stdout


def test_ci_run_status_passes_repo_and_attempt_to_gh_and_log_commands(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    log_file = isolated_env.home / "gh-args.log"
    write_fake_gh(
        isolated_env.bin_dir,
        [("failure", "completed", "failure", "app | docker", "601")],
    )
    env = isolated_env.env | {"FAKE_GH_LOG": str(log_file)}

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo", "--attempt", "2"],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 1
    gh_args = log_file.read_text(encoding="utf-8")
    assert "/repos/owner/repo/actions/runs/1234567890/attempts/2/jobs?per_page=30" in gh_args
    assert "--paginate --jq" in gh_args
    assert "gh run view 1234567890 --repo owner/repo --attempt 2 --job 601 --log-failed" in (
        result.stdout
    )


def test_ci_run_status_accepts_github_host_repo_prefix(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    log_file = isolated_env.home / "gh-args.log"
    write_fake_gh(
        isolated_env.bin_dir,
        [("success", "completed", "success", "app | docker", "801")],
    )
    env = isolated_env.env | {"FAKE_GH_LOG": str(log_file)}

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "github.com/owner/repo"],
        env=env,
    )

    assert_ok(result)
    assert "/repos/owner/repo/actions/runs/1234567890/jobs?per_page=30" in log_file.read_text(
        encoding="utf-8"
    )


def test_ci_run_all_includes_successful_job_log_commands(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_gh(
        isolated_env.bin_dir,
        [("success", "completed", "success", "app | docker", "701")],
    )

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo", "--all"],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "gh run view 1234567890 --repo owner/repo --job 701 --log-failed" in result.stdout
    assert "gh run view 1234567890 --repo owner/repo --job 701 --log" in result.stdout


def test_ci_run_missing_gh_returns_127(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    env = isolated_env.env | {"PATH": str(isolated_env.bin_dir)}

    result = run_ci_run_script(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 127
    assert "gh is required" in result.stderr


def test_ci_run_gh_failure_returns_3(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    write_fake_gh(isolated_env.bin_dir, [], exit_code=1)

    result = run_ci_run(
        repo_dir,
        ["status", "1234567890", "app", "--repo", "owner/repo"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 3
    assert "gh api failed" in result.stderr
    assert "gh failed" in result.stderr
