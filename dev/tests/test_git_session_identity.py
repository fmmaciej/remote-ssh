from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_ok,
    init_git_repo,
    require_git,
    run_cmd,
    write_git_user_local,
)


def _configure_repo_identity(repo: Path, env: dict[str, str]) -> None:
    for args in (
        ["--local", "user.name", "Repo User"],
        ["--local", "user.email", "repo@example.com"],
    ):
        result = run_cmd(["git", "config", *args], cwd=repo, env=env)
        assert_ok(result)


def _run_git_session_identity_probe(
    repo_dir: Path,
    repo: Path,
    env: dict[str, str],
    script: str,
) -> str:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(script).lstrip(),
            "_",
            repo_dir,
        ],
        cwd=repo,
        env=env,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def test_git_session_identity_overrides_repo_local_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    dots_dir = isolated_env.home / "dots"
    write_git_user_local(dots_dir)
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _configure_repo_identity(repo, isolated_env.env)
    env = isolated_env.env | {"REMOTE_DOTS_DIR": str(dots_dir)}
    env.pop("GIT_CONFIG_COUNT", None)
    env.pop("REMOTE_SSH_GIT_SESSION_IDENTITY", None)

    got = _run_git_session_identity_probe(
        repo_dir,
        repo,
        env,
        """
        set -euo pipefail
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        . "$1/shell/rc.d/07-git-session-identity.sh"

        printf 'name=%s\n' "$(git config user.name)"
        printf 'email=%s\n' "$(git config user.email)"
        printf 'useConfigOnly=%s\n' "$(git config user.useConfigOnly)"
        printf 'local_name=%s\n' "$(git config --local user.name)"
        printf 'local_email=%s\n' "$(git config --local user.email)"
        printf 'enabled=%s\n' "$REMOTE_SSH_GIT_SESSION_IDENTITY"
        printf 'count=%s\n' "$GIT_CONFIG_COUNT"
        """,
    )

    assert got == "\n".join(
        [
            "name=Session User",
            "email=session@example.com",
            "useConfigOnly=true",
            "local_name=Repo User",
            "local_email=repo@example.com",
            "enabled=1",
            "count=3",
        ]
    )


def test_git_session_identity_can_be_disabled(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    dots_dir = isolated_env.home / "dots"
    write_git_user_local(dots_dir)
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _configure_repo_identity(repo, isolated_env.env)
    env = isolated_env.env | {
        "REMOTE_DOTS_DIR": str(dots_dir),
        "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
    }
    env.pop("GIT_CONFIG_COUNT", None)
    env.pop("REMOTE_SSH_GIT_SESSION_IDENTITY", None)

    got = _run_git_session_identity_probe(
        repo_dir,
        repo,
        env,
        """
        set -euo pipefail
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        . "$1/shell/rc.d/07-git-session-identity.sh"

        printf 'name=%s\n' "$(git config user.name)"
        printf 'email=%s\n' "$(git config user.email)"
        printf 'enabled=%s\n' "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}"
        printf 'count=%s\n' "${GIT_CONFIG_COUNT:-0}"
        """,
    )

    assert got == "\n".join(
        [
            "name=Repo User",
            "email=repo@example.com",
            "enabled=0",
            "count=0",
        ]
    )
