from __future__ import annotations

from pathlib import Path

from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_managed_tool,
    run_remote_ssh,
    write_expected_tools,
)


def test_remote_ssh_usage_and_unknown_command(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["--help"], env=tool_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh <command> [args]" in result.stdout
    assert "prune [--apply]" in result.stdout
    assert "guide [section]" in result.stdout
    assert "git <command>" in result.stdout
    assert "update [check]" in result.stdout
    assert "install --full [--yes]" in result.stdout
    assert "uninstall [--yes] [tool ...]" in result.stdout
    assert "tool list" in result.stdout

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


def test_remote_ssh_guide_renders_commands_section(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "commands"], env=tool_env.env)

    assert_ok(result)
    assert "Commands" in result.stdout
    assert "remote-ssh guide [section]  Show this configuration guide" in result.stdout
    assert "remote-ssh check --strict   Report pinned tools vs local bin and PATH" in result.stdout
    assert "remote-ssh tool list        Show tool selection and install state" in result.stdout
    assert "remote-ssh uninstall [tool ...]" in result.stdout
    assert "remote-ssh git setup        Add remote-ssh Git config via include.path" in result.stdout
    assert "remote-ssh update check     Check whether upstream has changed" in result.stdout


def test_remote_ssh_git_usage_and_unknown_command(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["git", "--help"], env=tool_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh git <command> [args]" in result.stdout
    assert "setup" in result.stdout
    assert "status [ssh-host]" in result.stdout

    result = run_remote_ssh(repo_dir, ["git", "wat"], env=tool_env.env)
    assert_failed(result)
    assert "Unknown remote-ssh git command: wat" in result.stderr


def test_remote_ssh_check_delegates_to_check_command(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["check", "rg"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh check" in result.stdout
    assert "status:    ok" in result.stdout


def test_remote_ssh_tool_list_reports_tool_sets(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    write_expected_tools(tool_env, ["rg", "fd"])
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["tool", "list"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh tool list" in result.stdout
    assert "Default tools:" in result.stdout
    assert "Expected tools:" in result.stdout
    assert "  rg" in result.stdout
    assert "Managed installed tools:" in result.stdout
    assert "Unsupported default tools on this platform:" in result.stdout
