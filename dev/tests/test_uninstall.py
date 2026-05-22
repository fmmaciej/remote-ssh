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


def test_uninstall_help(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    result = run_remote_ssh(repo_dir, ["uninstall", "--help"], env=tool_env.env)

    assert_ok(result)
    assert "Usage:" in result.stdout
    assert "remote-ssh uninstall [--yes] [tool ...]" in result.stdout


def test_uninstall_without_managed_tools_is_noop(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["uninstall"], env=tool_env.env)

    assert_ok(result)
    assert "remote-ssh uninstall" in result.stdout
    assert "No managed tools selected for uninstall." in result.stdout
    assert "requires confirmation" not in result.stderr


def test_uninstall_requires_confirmation_before_changes(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    executable = make_managed_tool(tool_env, "rg", "15.1.0")
    expected_file = write_expected_tools(tool_env, ["rg"])

    result = run_remote_ssh(repo_dir, ["uninstall", "rg"], env=tool_env.env)

    assert_failed(result)
    assert "Use --yes for non-interactive uninstall." in result.stderr
    assert (tool_env.bin_dir / "rg").is_symlink()
    assert executable.exists()
    assert expected_file.exists()


def test_uninstall_yes_without_args_removes_all_managed_tools(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    rg = make_managed_tool(tool_env, "rg", "15.1.0")
    rg_stale = tool_env.opt_dir / "rg-14.1.0"
    fd = make_managed_tool(tool_env, "fd", "10.3.0")
    unknown = tool_env.opt_dir / "not-a-tool-1.0.0"
    rg_stale.mkdir()
    unknown.mkdir()
    expected_file = write_expected_tools(tool_env, ["rg", "fd", "fzf"])

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes"], env=tool_env.env)

    assert_ok(result)
    assert "Selected tools:" in result.stdout
    assert "  rg" in result.stdout
    assert "  fd" in result.stdout
    assert not (tool_env.bin_dir / "rg").exists()
    assert not (tool_env.bin_dir / "fd").exists()
    assert not rg.parent.exists()
    assert not rg_stale.exists()
    assert not fd.parent.exists()
    assert unknown.is_dir()
    assert expected_file.read_text(encoding="utf-8").splitlines()[-1] == "fzf"


def test_uninstall_explicit_tool_removes_only_that_tool(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    rg = make_managed_tool(tool_env, "rg", "15.1.0")
    fd = make_managed_tool(tool_env, "fd", "10.3.0")
    expected_file = write_expected_tools(tool_env, ["rg", "fd"])

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=tool_env.env)

    assert_ok(result)
    assert not (tool_env.bin_dir / "rg").exists()
    assert not rg.parent.exists()
    assert (tool_env.bin_dir / "fd").is_symlink()
    assert fd.exists()
    assert expected_file.read_text(encoding="utf-8").splitlines()[-1] == "fd"


def test_uninstall_removes_managed_aliases(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    nu = make_managed_tool(tool_env, "nu", "0.112.2", binary="nu", link_name="nu")
    (tool_env.bin_dir / "nushell").symlink_to(nu)

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "nu"], env=tool_env.env)

    assert_ok(result)
    assert not (tool_env.bin_dir / "nu").exists()
    assert not (tool_env.bin_dir / "nushell").exists()
    assert not nu.parent.exists()


def test_uninstall_protects_unmanaged_paths(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    unmanaged = tool_env.bin_dir / "rg"
    unmanaged.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    unmanaged.chmod(0o755)
    release_dir = tool_env.opt_dir / "rg-15.1.0"
    release_dir.mkdir()

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=tool_env.env)

    assert_ok(result)
    assert "Protected/skipped paths:" in result.stdout
    assert f"{unmanaged} (not a symlink)" in result.stdout
    assert unmanaged.exists()
    assert not release_dir.exists()


def test_uninstall_protects_symlink_outside_install_prefix(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    external = tool_env.external_dir / "rg"
    external.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    external.chmod(0o755)
    (tool_env.bin_dir / "rg").symlink_to(external)

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=tool_env.env)

    assert_ok(result)
    assert "Protected/skipped paths:" in result.stdout
    assert f"{tool_env.bin_dir / 'rg'} -> {external}" in result.stdout
    assert (tool_env.bin_dir / "rg").is_symlink()
    assert external.exists()


def test_uninstall_unknown_tool_fails_without_changes(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    executable = make_managed_tool(tool_env, "rg", "15.1.0")

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "nope"], env=tool_env.env)

    assert_failed(result)
    assert "Unknown tool: nope" in result.stderr
    assert (tool_env.bin_dir / "rg").is_symlink()
    assert executable.exists()


def test_uninstall_removes_expected_tools_file_when_empty(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    make_managed_tool(tool_env, "rg", "15.1.0")
    expected_file = write_expected_tools(tool_env, ["rg"])

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=tool_env.env)

    assert_ok(result)
    assert not expected_file.exists()


def test_uninstall_without_args_detects_relative_managed_symlink(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    release_dir = tool_env.opt_dir / "rg-15.1.0"
    executable = release_dir / "rg"
    release_dir.mkdir()
    executable.write_text("#!/usr/bin/env bash\nprintf rg\n", encoding="utf-8")
    executable.chmod(0o755)
    (tool_env.bin_dir / "rg").symlink_to(Path("../home/opt/rg-15.1.0/rg"))

    result = run_remote_ssh(repo_dir, ["uninstall", "--yes"], env=tool_env.env)

    assert_ok(result)
    assert not (tool_env.bin_dir / "rg").exists()
    assert not release_dir.exists()
