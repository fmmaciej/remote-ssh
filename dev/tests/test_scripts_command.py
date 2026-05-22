from __future__ import annotations

from pathlib import Path

from conftest import ToolStateEnv, assert_failed, assert_ok, run_remote_ssh


def test_remote_ssh_scripts_list_public_helpers(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "--list"], env=tool_env.env)

    assert_ok(result)
    output = result.stdout
    assert "remote-ssh scripts" in output
    assert "ci-run" in output
    assert "helm-chart-diff" in output
    assert "ssh-pick" in output
    assert "command" in output
    assert "shell function" in output
    assert "ssh_hosts.py" not in output


def test_remote_ssh_scripts_list_alias(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "list"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh scripts" in result.stdout
    assert "helm-chart-diff" in result.stdout


def test_remote_ssh_scripts_guide_lists_all_helpers(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "guide"], env=tool_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "ci-run" in output
    assert "ci-run status <run-id> <app-filter>" in output
    assert "Requires: gh" in output
    assert "Docs: docs/ci-run.md" in output
    assert "helm-chart-diff" in output
    assert "ssh-pick" in output
    assert "Backend: scripts/ssh_hosts.py" in output


def test_remote_ssh_scripts_guide_supports_single_helper(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "guide", "ci-run"], env=tool_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "ci-run" in output
    assert "ci-run status <run-id> <app-filter>" in output
    assert "helm-chart-diff" not in output
    assert "ssh-pick" not in output


def test_remote_ssh_scripts_guide_rejects_unknown_helper(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "guide", "sshf"], env=tool_env.env)

    assert_failed(result)
    assert "Unknown remote-ssh script helper: sshf" in result.stderr
    assert "Usage:" in result.stderr


def test_remote_ssh_scripts_guide_supports_ssh_pick(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["scripts", "guide", "ssh-pick"], env=tool_env.env)

    assert_ok(result)
    output = result.stdout
    assert "ssh-pick" in output
    assert "ssh-pick [ssh-args...]" in output
    assert "Entry point: shell/rc.d/30-ssh-pick.sh" in output
    assert "sshf" not in output
