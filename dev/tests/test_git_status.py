from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    init_git_repo,
    require_git,
    run_cmd,
    run_remote_ssh,
    write_executable,
)


def _configure_git_identity(repo: Path, env: dict[str, str]) -> None:
    for args in (
        ["user.name", "Test User"],
        ["user.email", "test@example.com"],
        ["user.useConfigOnly", "true"],
    ):
        result = run_cmd(["git", "config", *args], cwd=repo, env=env)
        assert_ok(result)


def _add_origin(repo: Path, env: dict[str, str]) -> None:
    result = run_cmd(
        ["git", "remote", "add", "origin", "git@github.com-myuser:fmmaciej/remote-ssh.git"],
        cwd=repo,
        env=env,
    )
    assert_ok(result)


def test_remote_ssh_git_status_reports_git_state_without_ssh_probes(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _configure_git_identity(repo, isolated_env.env)
    _add_origin(repo, isolated_env.env)
    ssh_called = isolated_env.home / "ssh-called"
    ssh_add_called = isolated_env.home / "ssh-add-called"
    write_executable(
        isolated_env.bin_dir / "ssh",
        f"#!/usr/bin/env bash\ntouch {ssh_called}\nexit 99\n",
    )
    write_executable(
        isolated_env.bin_dir / "ssh-add",
        f"#!/usr/bin/env bash\ntouch {ssh_add_called}\nexit 99\n",
    )
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock")}

    result = run_remote_ssh(repo_dir, ["git", "status"], cwd=repo, env=env)

    assert_ok(result)
    output = result.stdout
    assert "remote-ssh git status" in output
    assert "Git config" in output
    assert "  user.name:         Test User " in output
    assert "  user.email:        test@example.com " in output
    assert "  user.useConfigOnly: true " in output
    assert "Git session override" in output
    assert "  enabled:           0" in output
    assert "Git remote" in output
    assert "  origin:            git@github.com-myuser:fmmaciej/remote-ssh.git" in output
    assert "Next steps" in output
    assert "  [none]" in output
    assert "SSH agent" not in output
    assert "SSH auth" not in output
    assert "Diagnosis" not in output
    assert "ssh host:" not in output
    assert "ssh agent:" not in output
    assert "ssh auth:" not in output
    assert not ssh_called.exists()
    assert not ssh_add_called.exists()


def test_remote_ssh_git_status_rejects_host_argument(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert "Usage: remote-ssh git status" in result.stderr


def test_remote_ssh_git_status_reports_missing_git_config_next_step(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _add_origin(repo, isolated_env.env)

    result = run_remote_ssh(repo_dir, ["git", "status"], cwd=repo, env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "  user.name:         [missing]" in output
    assert "  user.email:        [missing]" in output
    assert "  user.useConfigOnly: [missing]" in output
    assert "Next steps" in output
    assert "  - Run remote-ssh git setup to configure bundled Git defaults." in output
    assert "  - Add an origin remote" not in output


def test_remote_ssh_git_status_reports_missing_origin_next_step(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _configure_git_identity(repo, isolated_env.env)

    result = run_remote_ssh(repo_dir, ["git", "status"], cwd=repo, env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "  origin:            [missing]" in output
    assert "Next steps" in output
    assert "  - Add an origin remote, or run this from a repository that has one." in output
    assert "  - Run remote-ssh git setup" not in output


def test_remote_ssh_git_status_reports_outside_worktree_next_step(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()

    result = run_remote_ssh(
        repo_dir,
        ["git", "status"],
        cwd=isolated_env.home,
        env=isolated_env.env,
    )

    assert_ok(result)
    output = result.stdout
    assert "  work tree:         [not inside a Git work tree]" in output
    assert "Next steps" in output
    assert "  - Run remote-ssh git status from inside a Git work tree." in output
    assert "  - Run remote-ssh git setup to configure bundled Git defaults." in output
    assert "  - Add an origin remote, or run this from a repository that has one." in output


def test_remote_ssh_git_status_reports_session_override(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    _add_origin(repo, isolated_env.env)
    for args in (
        ["--local", "user.name", "Repo User"],
        ["--local", "user.email", "repo@example.com"],
    ):
        result = run_cmd(["git", "config", *args], cwd=repo, env=isolated_env.env)
        assert_ok(result)
    env = isolated_env.env | {
        "REMOTE_SSH_GIT_SESSION_IDENTITY": "1",
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "user.name",
        "GIT_CONFIG_VALUE_0": "Session User",
        "GIT_CONFIG_KEY_1": "user.email",
        "GIT_CONFIG_VALUE_1": "session@example.com",
        "GIT_CONFIG_KEY_2": "user.useConfigOnly",
        "GIT_CONFIG_VALUE_2": "true",
    }

    result = run_remote_ssh(repo_dir, ["git", "status"], cwd=repo, env=env)

    assert_ok(result)
    output = result.stdout
    assert "  user.name:         Session User " in output
    assert "  user.email:        session@example.com " in output
    assert "Git session override" in output
    assert "  enabled:           1" in output
    assert "  GIT_CONFIG_COUNT:  3" in output
    assert "  session name:      Session User" in output
    assert "  session email:     session@example.com" in output
    assert "  session useConfigOnly: true" in output
    assert "Next steps" in output
    assert "  [none]" in output
