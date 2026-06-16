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
    assert not (state_dir / "login-status").exists()

    result = run_remote_ssh(
        repo_dir,
        ["update", "check", "--cached-message"],
        env=isolated_env.env | {"REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir)},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "remote-ssh: update available. Run: remote-ssh update"


def test_update_check_helper_stale_decisions(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    cache = tmp_path / "update-check"

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/update-check.lib.sh"

            unset REMOTE_SSH_UPDATE_CHECK_INTERVAL
            printf 'default-interval=%s\n' "$(remote_ssh_update_check_interval)"

            if remote_ssh_update_check_is_stale "$2"; then
              printf 'missing=stale\n'
            else
              printf 'missing=fresh\n'
            fi

            printf 'checked_at=not-a-number\n' >"$2"
            if remote_ssh_update_check_is_stale "$2"; then
              printf 'invalid=stale\n'
            else
              printf 'invalid=fresh\n'
            fi

            REMOTE_SSH_UPDATE_CHECK_INTERVAL=86400
            printf 'checked_at=%s\n' "$(date +%s)" >"$2"
            if remote_ssh_update_check_is_stale "$2"; then
              printf 'fresh=stale\n'
            else
              printf 'fresh=fresh\n'
            fi

            printf 'checked_at=%s\n' "$(($(date +%s) + 3600))" >"$2"
            if remote_ssh_update_check_is_stale "$2"; then
              printf 'future=stale\n'
            else
              printf 'future=fresh\n'
            fi

            printf 'checked_at=1\n' >"$2"
            REMOTE_SSH_UPDATE_CHECK_INTERVAL=1
            if remote_ssh_update_check_is_stale "$2"; then
              printf 'expired=stale\n'
            else
              printf 'expired=fresh\n'
            fi
            """,
            "_",
            repo_dir,
            cache,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "default-interval=86400",
        "missing=stale",
        "invalid=stale",
        "fresh=fresh",
        "future=stale",
        "expired=stale",
    ]


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
    assert not (state_dir / "login-status").exists()


def test_remote_ssh_update_refreshes_tracked_files_from_upstream(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    repo_copy = isolated_env.home / "repo"
    repo_copy.joinpath(".git").mkdir(parents=True)
    git_log = isolated_env.home / "git.log"

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            source "$1/tools/lib/env.sh"
            source "$TOOLS_LIB_DIR/commands.lib.sh"
            remote_ssh_cmd_install_main() { :; }
            remote_ssh_cmd_update_run "$2"
            """,
            "_",
            repo_dir,
            repo_copy,
        ],
        env=isolated_env.env | {"FAKE_GIT_LOG": str(git_log)},
    )

    assert_ok(result)
    output = git_log.read_text(encoding="utf-8")
    assert "git fetch origin main" in output
    assert "git reset --hard origin/main" in output
    assert "git ls-files --others --exclude-standard" in output
    assert "pull" not in output
    assert "clean" not in output


def test_remote_ssh_update_reports_untracked_files_without_removing_them(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    repo_copy = isolated_env.home / "repo"
    repo_copy.joinpath(".git").mkdir(parents=True)
    git_log = isolated_env.home / "git.log"

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            source "$1/tools/lib/env.sh"
            source "$TOOLS_LIB_DIR/commands.lib.sh"
            remote_ssh_cmd_install_main() { :; }
            remote_ssh_cmd_update_run "$2"
            """,
            "_",
            repo_dir,
            repo_copy,
        ],
        env=isolated_env.env
        | {
            "FAKE_GIT_LOG": str(git_log),
            "FAKE_UNTRACKED": "local-note.md",
        },
    )

    assert_ok(result)
    assert "[WARN] Untracked files were left in place:" in result.stdout
    assert "  local-note.md" in result.stdout
    assert "clean" not in git_log.read_text(encoding="utf-8")


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
