from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_external_tool,
    make_managed_tool,
    mark_managed_release,
    run_remote_ssh,
    write_executable,
    write_expected_tools,
)


def set_platform(env: ToolStateEnv, system: str, arch: str, libc: str = "gnu") -> None:
    write_executable(
        env.bin_dir / "uname",
        f"""#!/usr/bin/env bash
case "$1" in
  -s) printf '%s\\n' '{system}' ;;
  -m) printf '%s\\n' '{arch}' ;;
  *) exit 1 ;;
esac
""",
    )
    write_executable(env.bin_dir / "ldd", f"#!/bin/sh\nprintf '%s\\n' '{libc}'\n")


@pytest.fixture
def list_env(tool_env: ToolStateEnv, runtime_bash: str) -> ToolStateEnv:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    set_platform(tool_env, "Darwin", "arm64")
    return tool_env


def list_tools(repo_dir: Path, env: ToolStateEnv, *options: str) -> dict[str, str]:
    result = run_remote_ssh(repo_dir, ["list", *options], env=env.env)
    assert_ok(result)
    assert result.stderr == ""
    lines = [line.split() for line in result.stdout.splitlines()]
    header = next(i for i, row in enumerate(lines) if row and row[0] == "TOOL")
    rows = [row for row in lines[header + 1 :] if row and row[0] != "No"]
    names = [row[0] for row in rows]
    assert names == sorted(set(names))
    return {
        row[0]: "installed"
        if "installed" in row[3:]
        else "unsupported"
        if row[2] == "unsupported"
        else "available"
        for row in rows
    }


def test_list_uses_full_catalogue_without_configuration(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    rows = list_tools(repo_dir, list_env)

    assert rows["tspin"] == "available"
    assert rows["vector"] == "available"
    assert set(rows.values()) == {"available"}
    assert not {"dust", "eza", "procs"} & rows.keys()
    assert not (list_env.config_dir / "remote-ssh").exists()


def test_all_lists_every_definition(repo_dir: Path, list_env: ToolStateEnv) -> None:
    rows = list_tools(repo_dir, list_env, "--all")

    assert rows.keys() == {path.stem for path in (repo_dir / "tools/defs").glob("*.sh")}
    for tool in ("dust", "eza", "procs"):
        assert rows[tool] == "unsupported"


@pytest.mark.parametrize(
    "system,arch,libc,vector",
    [
        ("Darwin", "arm64", "gnu", "available"),
        ("Darwin", "x86_64", "gnu", "unsupported"),
        ("Linux", "x86_64", "gnu", "available"),
        ("Linux", "aarch64", "musl", "available"),
    ],
)
def test_list_filters_for_detected_platform(
    repo_dir: Path,
    list_env: ToolStateEnv,
    system: str,
    arch: str,
    libc: str,
    vector: str,
) -> None:
    set_platform(list_env, system, arch, libc)

    rows = list_tools(repo_dir, list_env)
    assert rows["fd"] == "available"
    if system == "Linux" and arch == "aarch64" and libc == "musl":
        assert "rg" not in rows  # This definition only provides a glibc ARM asset.
    assert ("vector" in rows) == (vector == "available")
    assert list_tools(repo_dir, list_env, "--all")["vector"] == vector


@pytest.mark.parametrize("version", ["15.1.0", "14.1.0"])
def test_list_installed_includes_older_managed_versions(
    repo_dir: Path, list_env: ToolStateEnv, version: str
) -> None:
    make_managed_tool(list_env, "rg", version)
    make_external_tool(list_env, "fd")
    list_env.env["PATH"] = f"{list_env.external_dir}:{list_env.env['PATH']}"

    assert list_tools(repo_dir, list_env)["rg"] == "installed"
    assert list_tools(repo_dir, list_env)["fd"] == "available"
    assert list_tools(repo_dir, list_env, "--installed") == {"rg": "installed"}


def test_relative_bundle_link_is_installed_without_alias_rows(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    executable = make_managed_tool(
        list_env, "nu", "0.112.2", binary="bin/nu", link_name="nu"
    )
    mark_managed_release(
        executable.parent.parent, "nu", "0.112.2", executable="bin/nu", layout="bundle"
    )
    link = list_env.bin_dir / "nu"
    link.unlink()
    link.symlink_to(os.path.relpath(executable, list_env.bin_dir))
    (list_env.bin_dir / "nushell").symlink_to(executable)

    assert list_tools(repo_dir, list_env, "--installed") == {"nu": "installed"}


def test_installed_is_visible_on_unsupported_platform(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    make_managed_tool(list_env, "procs", "0.14.11")

    for options in ((), ("--all",), ("--installed",)):
        assert list_tools(repo_dir, list_env, *options)["procs"] == "installed"


@pytest.mark.parametrize(
    "state",
    ["broken", "not-executable", "unowned", "invalid-record", "foreign", "plain-file"],
)
def test_invalid_or_unmanaged_installation_is_not_installed(
    repo_dir: Path, list_env: ToolStateEnv, state: str
) -> None:
    executable = make_managed_tool(list_env, "rg", "15.1.0")
    marker = executable.parent / ".remote-ssh-release"
    link = list_env.bin_dir / "rg"
    if state == "broken":
        executable.unlink()
    elif state == "not-executable":
        executable.chmod(0o644)
    elif state == "unowned":
        marker.unlink()
    elif state == "invalid-record":
        marker.write_text("format=1\n")
    elif state == "foreign":
        link.unlink()
        link.symlink_to(make_external_tool(list_env, "rg"))
    elif state == "plain-file":
        link.unlink()
        write_executable(link, "#!/bin/sh\nexit 0\n")

    assert list_tools(repo_dir, list_env)["rg"] == "available"
    assert list_tools(repo_dir, list_env, "--installed") == (
        {"rg": "available"} if state == "not-executable" else {}
    )


def test_expected_selection_does_not_affect_list_or_change(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    before = list_tools(repo_dir, list_env)
    config = write_expected_tools(
        list_env, ["# custom selection", "rg", "unknown-tool"]
    )
    original = config.read_bytes()
    config.chmod(0o444)

    assert list_tools(repo_dir, list_env) == before
    list_tools(repo_dir, list_env, "--all")
    list_tools(repo_dir, list_env, "--installed")
    assert config.read_bytes() == original
    assert config.stat().st_mode & 0o777 == 0o444


def test_listing_does_not_execute_installed_binary(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    sentinel = list_env.home / "executed"
    make_managed_tool(
        list_env, "rg", "15.1.0", content=f'#!/bin/sh\ntouch "{sentinel}"\n'
    )

    assert list_tools(repo_dir, list_env)["rg"] == "installed"
    assert not sentinel.exists()


def test_empty_results_do_not_create_install_directories(
    repo_dir: Path, list_env: ToolStateEnv
) -> None:
    list_env.env["INSTALL_PREFIX"] = str(list_env.home / "missing-opt")
    list_env.env["INSTALL_BIN_DIR"] = str(list_env.home / "missing-bin")

    assert list_tools(repo_dir, list_env, "--installed") == {}
    set_platform(list_env, "Unknown", "unknown")
    assert list_tools(repo_dir, list_env) == {}
    assert not Path(list_env.env["INSTALL_PREFIX"]).exists()
    assert not Path(list_env.env["INSTALL_BIN_DIR"]).exists()


@pytest.mark.parametrize(
    "options",
    [["-h"], ["--help"], ["--help", "--all"], ["--installed", "--help"]],
)
def test_list_help(repo_dir: Path, list_env: ToolStateEnv, options: list[str]) -> None:
    sentinel = list_env.home / "platform-detected"
    write_executable(
        list_env.bin_dir / "uname", f'#!/bin/sh\ntouch "{sentinel}"\nexit 1\n'
    )
    result = run_remote_ssh(repo_dir, ["list", *options], env=list_env.env)

    assert_ok(result)
    assert result.stderr == ""
    assert "Usage: remote-ssh list [--installed | --all]" in result.stdout
    assert not sentinel.exists()


@pytest.mark.parametrize(
    "options",
    [
        ["--installed", "--all"],
        ["--all", "--installed"],
        ["--unknown"],
        ["rg"],
        ["--help", "--all", "--installed"],
        ["--all", "--help", "--installed"],
        ["--all", "--installed", "--help"],
        ["--help", "--installed", "--all"],
        ["--installed", "--help", "--all"],
        ["--installed", "--all", "--help"],
        ["--help", "--unknown"],
        ["--unknown", "--help"],
        ["-h", "rg"],
        ["rg", "-h"],
    ],
)
def test_list_rejects_invalid_arguments(
    repo_dir: Path, list_env: ToolStateEnv, options: list[str]
) -> None:
    result = run_remote_ssh(repo_dir, ["list", *options], env=list_env.env)

    assert_failed(result)
    assert result.stdout == ""
    assert result.stderr
