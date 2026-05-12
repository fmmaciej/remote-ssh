from __future__ import annotations

from pathlib import Path

from conftest import (
    ToolStateEnv,
    assert_failed,
    make_external_tool,
    make_managed_tool,
    run_remote_ssh,
    write_expected_tools,
)


def test_remote_ssh_doctor_reports_missing_tools(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    write_expected_tools(tool_env, ["rg"])

    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    output = result.stdout
    assert "remote-ssh doctor" in output
    assert "status: ok" in output
    assert "Repository" in output
    assert "branch:" in output
    assert "commit:" in output
    assert "dirty:" in output
    assert "Shell rc" in output
    assert "shell/rc.sh" in output
    assert "Optional helpers" in output
    assert "sshf python3:" in output
    assert "Tool check" in output
    assert "summary: failed" in output
    assert "Next steps" in output
    assert "run: remote-ssh install" in output
    assert "inspect: remote-ssh check --strict" in output


def test_remote_ssh_doctor_reports_path_shadow_hint(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["rg"])
    make_managed_tool(tool_env, "rg", "15.1.0", content="#!/usr/bin/env bash\nprintf managed-rg\n")
    make_external_tool(tool_env, "rg", content="#!/usr/bin/env bash\nprintf external-rg\n")
    env = tool_env.env | {"PATH": f"{tool_env.external_dir}:{tool_env.bin_dir}:/usr/bin:/bin"}

    result = run_remote_ssh(repo_dir, ["doctor"], env=env)

    assert_failed(result)
    assert "status:    path-shadowed" in result.stdout
    assert (
        f"check PATH order: {tool_env.bin_dir} should come before external tool directories"
        in result.stdout
    )
    assert "inspect: remote-ssh check --strict" in result.stdout


def test_remote_ssh_doctor_rejects_mismatched_remote_env_dir(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    other = tool_env.home / "other"
    other.mkdir()
    env = tool_env.env | {"REMOTE_ENV_DIR": str(other)}

    result = run_remote_ssh(repo_dir, ["doctor"], env=env)

    assert_failed(result)
    assert "env status: mismatch" in result.stdout


def test_remote_ssh_doctor_reports_missing_expected_tools_config(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    assert "No expected tools config found:" in result.stdout
    assert "choose tools: remote-ssh install fd rg fzf" in result.stdout
    assert "remote-ssh install --full --yes" in result.stdout


def test_remote_ssh_doctor_reports_missing_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["nu"])
    make_managed_tool(tool_env, "nu", "0.112.2")

    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    assert "alias:     nushell -> [missing] status=missing target=[missing]" in result.stdout
    assert "run: remote-ssh install" in result.stdout
    assert "inspect: remote-ssh check --strict" in result.stdout
