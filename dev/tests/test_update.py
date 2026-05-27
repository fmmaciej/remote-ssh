from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    run_cmd,
    run_remote_ssh,
    write_fake_update_git,
)


def test_remote_ssh_update_check_reports_current(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    env = isolated_env.env | {
        "FAKE_LOCAL_HEAD": "aaaaaaaa",
        "FAKE_REMOTE_HEAD": "aaaaaaaa",
    }

    result = run_remote_ssh(repo_dir, ["update", "check"], env=env)

    assert_ok(result)
    assert "remote-ssh update check" in result.stdout
    assert "upstream: origin/main" in result.stdout
    assert "status:   current" in result.stdout


def test_remote_ssh_update_check_reports_update_available(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    env = isolated_env.env | {
        "FAKE_LOCAL_HEAD": "aaaaaaaa",
        "FAKE_REMOTE_HEAD": "bbbbbbbb",
    }

    result = run_remote_ssh(repo_dir, ["update", "check"], env=env)

    assert_ok(result)
    assert "status:   update-available" in result.stdout
    assert "next:     remote-ssh update" in result.stdout


def test_remote_ssh_update_check_reports_missing_upstream(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    env = isolated_env.env | {"FAKE_NO_UPSTREAM": "1"}

    result = run_remote_ssh(repo_dir, ["update", "check"], env=env)

    assert_failed(result)
    assert "status:   error" in result.stdout
    assert "No upstream branch is configured" in result.stdout


def test_remote_ssh_update_check_writes_cached_message(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    state_dir = isolated_env.home / "state"
    env = isolated_env.env | {
        "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
        "FAKE_LOCAL_HEAD": "aaaaaaaa",
        "FAKE_REMOTE_HEAD": "bbbbbbbb",
    }

    result = run_remote_ssh(repo_dir, ["update", "check", "--quiet", "--write-cache"], env=env)

    assert_ok(result)
    cache = state_dir / "update-check"
    cache_text = cache.read_text(encoding="utf-8")
    assert "status=update-available" in cache_text
    assert "checked_at_text=" in cache_text
    login_status = (state_dir / "login-status").read_text(encoding="utf-8").rstrip("\n")
    assert login_status.startswith("remote-ssh: update available. Run: remote-ssh update")
    assert " (checked: " in login_status

    result = run_remote_ssh(
        repo_dir,
        ["update", "check", "--cached-message"],
        env=isolated_env.env | {"REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir)},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "remote-ssh: update available. Run: remote-ssh update"


def test_remote_ssh_update_marks_cached_status_current(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    repo_copy = isolated_env.home / "repo"
    repo_copy.joinpath(".git").mkdir(parents=True)
    state_dir = isolated_env.home / "state"
    state_dir.mkdir()
    (state_dir / "update-check").write_text(
        "checked_at=1\nstatus=update-available\n",
        encoding="utf-8",
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            source "$1/tools/lib/env.sh"
            source "$TOOLS_LIB_DIR/commands.lib.sh"
            remote_ssh_cmd_install_main() {
              :
            }
            remote_ssh_cmd_update_run "$2"
            """,
            "_",
            repo_dir,
            repo_copy,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "FAKE_LOCAL_HEAD": "bbbbbbbb",
            "FAKE_REMOTE_HEAD": "bbbbbbbb",
        },
    )

    assert_ok(result)
    cache_text = (state_dir / "update-check").read_text(encoding="utf-8")
    assert "status=current" in cache_text
    assert "checked_at_text=" in cache_text
    assert "local_head=bbbbbbbb" in cache_text
    assert "remote_head=bbbbbbbb" in cache_text
    login_status = (state_dir / "login-status").read_text(encoding="utf-8").rstrip("\n")
    assert login_status.startswith("remote-ssh: current")
    assert " (checked: " in login_status


def test_remote_ssh_update_runs_install_without_tool_arguments(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    repo_copy = isolated_env.home / "repo"
    repo_copy.joinpath(".git").mkdir(parents=True)

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            source "$1/tools/lib/env.sh"
            source "$TOOLS_LIB_DIR/commands.lib.sh"
            remote_ssh_cmd_install_main() {
              printf "argc=%s\n" "$#"
              printf "repo=%s\n" "${1:-}"
            }
            remote_ssh_cmd_update_run "$2"
            """,
            "_",
            repo_dir,
            repo_copy,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "argc=1" in result.stdout
    assert f"repo={repo_copy}" in result.stdout
