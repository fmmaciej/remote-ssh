from __future__ import annotations

from pathlib import Path

from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_external_tool,
    make_managed_tool,
    run_remote_ssh,
    write_expected_tools,
)


def test_remote_ssh_check_reports_local_tool(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["check", "rg"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh check" in result.stdout
    assert "VERSION=15.1.0 BurntSushi/ripgrep@15.1.0" in result.stdout
    assert f"local:     {tool_env.bin_dir / 'rg'}" in result.stdout
    assert f"target:    {tool_env.opt_dir / 'rg-15.1.0' / 'rg'}" in result.stdout
    assert f"path:      {tool_env.bin_dir / 'rg'}" in result.stdout
    assert "status:    ok" in result.stdout


def test_remote_ssh_check_uses_expected_tools_by_default(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["# comment", "", "rg"])
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["check"], env=tool_env.env)

    assert_ok(result)
    assert "rg" in result.stdout
    assert "status:    ok" in result.stdout


def test_remote_ssh_check_reports_missing_expected_config(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["check"], env=tool_env.env)

    assert_failed(result)
    assert "No expected tools config found:" in result.stderr
    assert "remote-ssh install --full --yes" in result.stderr


def test_remote_ssh_check_warns_about_unknown_expected_tool(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["rg", "oldtool"])
    make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["check"], env=tool_env.env)

    assert_ok(result)
    assert "unknown expected tool: oldtool" in result.stdout
    assert "status:    ok" in result.stdout


def test_remote_ssh_check_strict_rejects_external_only_tool(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_external_tool(tool_env, "rg")
    env = tool_env.env | {"PATH": f"{tool_env.external_dir}:/usr/bin:/bin"}

    result = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=env)

    assert_failed(result)
    assert "status:    external-only" in result.stdout
    assert f"path:      {tool_env.external_dir / 'rg'}" in result.stdout


def test_remote_ssh_check_strict_rejects_stale_local_tool(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "rg", "14.1.0")

    result = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=tool_env.env)

    assert_failed(result)
    assert "status:    stale-local" in result.stdout
    assert f"target:    {tool_env.opt_dir / 'rg-14.1.0' / 'rg'}" in result.stdout


def test_remote_ssh_check_strict_accepts_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    target = make_managed_tool(tool_env, "nu", "0.112.2")
    (tool_env.bin_dir / "nushell").symlink_to(target)

    result = run_remote_ssh(repo_dir, ["check", "--strict", "nu"], env=tool_env.env)

    assert_ok(result)
    assert (
        f"alias:     nushell -> {tool_env.bin_dir / 'nushell'} "
        f"status=ok target={tool_env.opt_dir / 'nu-0.112.2' / 'nu'}"
    ) in result.stdout


def test_remote_ssh_check_strict_rejects_missing_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "nu", "0.112.2")

    result = run_remote_ssh(repo_dir, ["check", "--strict", "nu"], env=tool_env.env)

    assert_failed(result)
    assert "alias:     nushell -> [missing] status=missing target=[missing]" in result.stdout


def test_remote_ssh_check_strict_rejects_stale_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "nu", "0.112.2")
    stale = make_managed_tool(tool_env, "nu", "0.111.0", link_name="nushell", content=None)

    result = run_remote_ssh(repo_dir, ["check", "--strict", "nu"], env=tool_env.env)

    assert_failed(result)
    assert (
        f"alias:     nushell -> {tool_env.bin_dir / 'nushell'} "
        f"status=stale-local target={stale}"
    ) in result.stdout


def test_remote_ssh_check_strict_rejects_external_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "nu", "0.112.2")
    make_external_tool(tool_env, "nushell", content="#!/usr/bin/env bash\nprintf external\n")
    env = tool_env.env | {"PATH": f"{tool_env.bin_dir}:{tool_env.external_dir}:/usr/bin:/bin"}

    result = run_remote_ssh(repo_dir, ["check", "--strict", "nu"], env=env)

    assert_failed(result)
    assert (
        f"alias:     nushell -> {tool_env.external_dir / 'nushell'} "
        "status=external-only target=[missing]"
    ) in result.stdout
