from __future__ import annotations

from pathlib import Path

from conftest import ToolStateEnv, assert_failed, assert_ok, run_remote_ssh


def test_remote_ssh_scripts_list_public_helpers(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "--list"], env=tool_env.env)

    assert_ok(result)
    output = result.stdout
    assert "remote-ssh scripts" in output
    assert "bssh" in output
    assert "bssh-ip" in output
    assert "ssh-find" in output
    assert "ssh-pick" in output
    assert "command" in output
    assert "shell function" in output
    assert "ssh_hosts.py" not in output
    assert "ssh_find.py" not in output


def test_remote_ssh_scripts_list_alias(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "list"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh scripts" in result.stdout
    assert "ssh-find" in result.stdout


def test_remote_ssh_scripts_guide_points_to_guide_section(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "guide"], env=tool_env.env)

    assert_failed(result)
    assert "remote-ssh scripts guide moved to remote-ssh guide scripts." in result.stderr
    assert "Use: remote-ssh guide scripts [helper]" in result.stderr
