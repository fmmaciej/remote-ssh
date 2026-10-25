from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    copy_repo_for_git_setup,
    run_cmd,
    run_remote_ssh,
    write_executable,
    write_fake_update_git,
)


def prepare_update_checkout(repo: Path) -> None:
    repo.joinpath(".git").mkdir(parents=True)
    write_executable(
        repo / "bin" / "remote-ssh",
        """
        #!/usr/bin/env bash
        [[ "$*" == install ]] || exit 99
        printf 'argc=1\\nrepo=%s\\n' "$REMOTE_ENV_DIR"
        exit "${FAKE_INSTALL_EXIT:-0}"
    """,
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
    prepare_update_checkout(repo_copy)
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
    prepare_update_checkout(repo_copy)
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
    prepare_update_checkout(repo_copy)
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
    prepare_update_checkout(repo_copy)

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


@pytest.mark.parametrize("step", ["FETCH", "RESET"])
def test_failed_update_does_not_install_or_mark_current(
    repo_dir: Path, isolated_env: IsolatedEnv, step: str
) -> None:
    write_fake_update_git(isolated_env.bin_dir)
    log = isolated_env.home / "git.log"
    cache = Path(isolated_env.env["XDG_STATE_HOME"]) / "remote-ssh" / "update-check"
    cache.parent.mkdir(parents=True)
    cache.write_text("status=update-available\n")
    result = run_remote_ssh(
        repo_dir,
        ["update"],
        env=isolated_env.env
        | {
            f"FAKE_{step}_EXIT": "17",
            "FAKE_GIT_LOG": str(log),
        },
    )
    assert result.returncode == 17
    if step == "FETCH":
        assert "reset" not in log.read_text()
    assert "Begin." not in result.stderr
    assert cache.read_text() == "status=update-available\n"


def test_update_runs_new_checkout_installer_and_propagates_failure(
    repo_dir: Path, isolated_env: IsolatedEnv, tmp_path: Path
) -> None:
    real_git = shutil.which("git")
    assert real_git
    checkout = copy_repo_for_git_setup(repo_dir, tmp_path)
    upstream = tmp_path / "upstream"
    env = isolated_env.env | {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args: str | Path) -> None:
        assert_ok(
            run_cmd(
                [
                    real_git,
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "-c",
                    "commit.gpgsign=false",
                    *args,
                ],
                env=env,
            )
        )

    git("-C", checkout, "init", "-b", "main")
    git("-C", checkout, "add", ".")
    git("-C", checkout, "commit", "-qm", "base")
    # Use Git's transfer protocol so background packing cannot race with a
    # local filesystem copy of the source object directory.
    git("clone", "--no-local", "--bare", checkout, upstream)
    git("-C", checkout, "remote", "add", "origin", upstream)
    git("-C", checkout, "fetch", "origin")
    git("-C", checkout, "branch", "--set-upstream-to=origin/main")
    writer = tmp_path / "writer"
    git("clone", upstream, writer)
    write_executable(
        writer / "bin" / "remote-ssh", "#!/bin/sh\necho refreshed-installer:$1\nexit 23\n"
    )
    git("-C", writer, "add", ".")
    git("-C", writer, "commit", "-qm", "new installer")
    git("-C", writer, "push")
    result = run_cmd(["bash", checkout / "bin" / "remote-ssh", "update"], env=env)
    assert result.returncode == 23
    assert "refreshed-installer:install" in result.stdout
