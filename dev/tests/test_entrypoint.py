from __future__ import annotations

from pathlib import Path

import pytest
from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_managed_tool,
    run_cmd,
    run_remote_ssh,
)


@pytest.mark.parametrize(
    "args,code",
    [
        (["install", "--help"], 0),
        ([], 0),
        (["-h"], 0),
        (["--help"], 0),
        (["help"], 0),
        (["shell", "-h"], 0),
        (["shell", "--help"], 0),
        (["list"], 0),
        (["list", "--installed"], 0),
        (["list", "--all"], 0),
        (["check", "rg"], 1),
        (["check", "--strict", "rg"], 1),
        (["uninstall", "--yes"], 1),
        (["prune"], 0),
    ],
)
def test_public_commands_with_empty_state_on_supported_bash(
    repo_dir: Path,
    tool_env: ToolStateEnv,
    runtime_bash: str,
    args: list[str],
    code: int,
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    result = run_cmd(
        [runtime_bash, repo_dir / "bin/remote-ssh", *args], env=tool_env.env
    )
    assert result.returncode == code, result.stdout + result.stderr
    assert "unbound variable" not in result.stderr


def test_remote_ssh_usage_and_unknown_command(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    result = run_remote_ssh(repo_dir, ["--help"], env=tool_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh <command> [args]" in result.stdout
    assert "prune [--apply]" in result.stdout
    assert "guide [section]" in result.stdout
    assert "setup" in result.stdout
    assert "ssh <command>" in result.stdout
    assert "git <command>" in result.stdout
    assert "update [check]" in result.stdout
    assert "install --profile <name>" in result.stdout
    assert "install --full" not in result.stdout
    assert "uninstall [--yes] TOOL ..." in result.stdout
    assert "list [--installed | --all]" in result.stdout
    assert "scripts --list" in result.stdout
    assert (
        "shell                     Start an interactive remote-ssh Bash"
        in result.stdout
    )

    result = run_remote_ssh(repo_dir, ["help"], env=tool_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh <command> [args]" in result.stdout
    assert "guide [section]" in result.stdout

    result = run_remote_ssh(repo_dir, ["help", "aliases"], env=tool_env.env)
    assert_failed(result)
    assert "remote-ssh help does not accept sections." in result.stderr
    assert "Use: remote-ssh guide aliases" in result.stderr

    result = run_remote_ssh(repo_dir, ["wat"], env=tool_env.env)
    assert_failed(result)
    assert "Unknown remote-ssh command: wat" in result.stderr


def test_remote_ssh_guide_renders_commands_section(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "commands"], env=tool_env.env)

    assert_ok(result)
    assert "Commands" in result.stdout
    assert "remote-ssh guide [section]  Show this configuration guide" in result.stdout
    assert "remote-ssh install --profile <name>" in result.stdout
    assert "remote-ssh check" in result.stdout
    assert "remote-ssh list [--installed | --all]" in result.stdout
    assert "List available tools and managed installations" in result.stdout
    assert "remote-ssh uninstall TOOL ..." in result.stdout
    assert (
        "remote-ssh setup            Configure bundled SSH and Git defaults"
        in result.stdout
    )
    assert (
        "remote-ssh git setup        Add remote-ssh Git config via include.path"
        in result.stdout
    )
    assert (
        "remote-ssh ssh setup        Add remote-ssh SSH config include" in result.stdout
    )
    assert (
        "remote-ssh ssh status       Check SSH config, host, agent, and auth"
        in result.stdout
    )
    assert (
        "remote-ssh update check     Check whether upstream has changed"
        in result.stdout
    )
    assert "remote-ssh scripts --list   List bundled helper scripts" in result.stdout
    assert (
        "remote-ssh shell            Start an interactive remote-ssh Bash"
        in result.stdout
    )


def test_remote_ssh_git_usage_and_unknown_command(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    result = run_remote_ssh(repo_dir, ["git", "--help"], env=tool_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh git <command> [args]" in result.stdout
    assert "setup" in result.stdout
    assert (
        "status             Report Git identity, session override, and origin"
        in result.stdout
    )
    assert "status [ssh-host]" not in result.stdout

    result = run_remote_ssh(repo_dir, ["git", "wat"], env=tool_env.env)
    assert_failed(result)
    assert "Unknown remote-ssh git command: wat" in result.stderr


def test_remote_ssh_check_delegates_to_check_command(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "rg", "15.2.0")

    result = run_remote_ssh(repo_dir, ["check", "rg"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh check" in result.stdout
    assert "installed ok" in result.stdout


def test_remote_ssh_tool_list_reports_install_state(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["list"], env=tool_env.env)

    assert_ok(result)
    assert result.stdout.splitlines()[0].split() == [
        "TOOL",
        "MEMBERSHIP",
        "SUPPORT",
        "STATUS",
    ]
    assert any(
        row and row[0] == "rg" and "installed" in row
        for row in (line.split() for line in result.stdout.splitlines()[1:])
    )
