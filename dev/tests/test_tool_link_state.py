from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_managed_tool,
    mark_managed_release,
    run_remote_ssh,
    write_executable,
)


@pytest.fixture
def link_env(tool_env: ToolStateEnv, runtime_bash: str) -> ToolStateEnv:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        tool_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Darwin;; -m) echo arm64;; esac\n",
    )
    write_executable(
        tool_env.bin_dir / "curl",
        '#!/bin/sh\nprintf called > "$HOME/network-called"\nexit 99\n',
    )
    tool_env.env["FORCE"] = "0"
    return tool_env


def point_link(env: ToolStateEnv, name: str, target: Path, relative: bool) -> Path:
    link = env.bin_dir / name
    if link.is_symlink():
        link.unlink()
    link.symlink_to(os.path.relpath(target, link.parent) if relative else target)
    return link


def assert_listed(repo: Path, env: ToolStateEnv, tool: str, installed: bool) -> None:
    result = run_remote_ssh(repo, ["tool", "list", "--installed"], env=env.env)
    assert_ok(result)
    rows = [line.split() for line in result.stdout.splitlines()]
    assert ([tool, "installed"] in rows) == installed


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
@pytest.mark.parametrize("tool,version", [("rg", "15.2.0"), ("nu", "0.117.0"), ("nvim", "0.12.6")])
def test_pinned_links_agree_across_list_check_and_install(
    repo_dir: Path, link_env: ToolStateEnv, relative: bool, tool: str, version: str
) -> None:
    binary = "bin/nvim" if tool == "nvim" else tool
    executable = make_managed_tool(link_env, tool, version, binary=binary, link_name=tool)
    if tool == "nvim":
        mark_managed_release(
            executable.parent.parent, tool, version, executable=binary, layout="bundle"
        )
    link = point_link(link_env, tool, executable, relative)
    if tool == "nu":
        point_link(link_env, "nushell", executable, relative)
    target = link.readlink()

    assert_listed(repo_dir, link_env, tool, installed=True)
    check = run_remote_ssh(repo_dir, ["check", "--strict", tool], env=link_env.env)
    assert_ok(check)
    assert "status:    ok" in check.stdout
    assert f"target:    {target}" in check.stdout
    if tool == "nu":
        assert f"status=ok target={target}" in check.stdout
    install = run_remote_ssh(repo_dir, ["tool", "install", tool], env=link_env.env)
    assert_ok(install)
    assert "SKIPPING" in install.stderr
    assert not (link_env.home / "network-called").exists()
    assert link.readlink() == target


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_old_links_remain_listed_but_require_pinned_install(
    repo_dir: Path, link_env: ToolStateEnv, relative: bool
) -> None:
    executable = make_managed_tool(link_env, "rg", "14.1.0")
    link = point_link(link_env, "rg", executable, relative)
    target = link.readlink()

    assert_listed(repo_dir, link_env, "rg", installed=True)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_failed(check)
    assert "status:    stale-local" in check.stdout
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_failed(install)  # Transport is blocked; the reinstall must be attempted.
    assert (link_env.home / "network-called").exists()
    assert link.readlink() == target


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_legacy_binary_links_keep_existing_policy(
    repo_dir: Path, link_env: ToolStateEnv, relative: bool
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    marker = executable.parent / ".remote-ssh-release"
    marker.unlink()
    point_link(link_env, "rg", executable, relative)

    assert_listed(repo_dir, link_env, "rg", installed=False)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_ok(check)
    assert "status:    ok" in check.stdout
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_ok(install)
    assert "SKIPPING" in install.stderr
    assert not (link_env.home / "network-called").exists()
    assert not marker.exists()


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
@pytest.mark.parametrize("state", ["broken", "outside", "traversal", "terminal-symlink"])
def test_invalid_links_are_not_treated_as_pinned_installations(
    repo_dir: Path, link_env: ToolStateEnv, relative: bool, state: str
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    if state == "broken":
        executable.unlink()
    else:
        outside = link_env.external_dir / "rg-15.2.0/rg"
        write_executable(outside, "#!/bin/sh\nexit 0\n")
        if state == "terminal-symlink":
            executable.unlink()
            executable.symlink_to(outside)
        elif state == "traversal":
            # Looks like a pinned release path before resolving the parent.
            executable = executable.parent / "../../external/rg-15.2.0/rg"
        else:
            executable = outside
    link = point_link(link_env, "rg", executable, relative)
    target = link.readlink()

    assert_listed(repo_dir, link_env, "rg", installed=False)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_failed(check)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_failed(install)
    assert (link_env.home / "network-called").exists()
    assert link.readlink() == target


def test_relative_link_under_symlinked_prefix_and_suffixed_release(
    repo_dir: Path, link_env: ToolStateEnv
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    release = executable.parent.with_name("rg-15.2.0.123-456")
    executable.parent.rename(release)
    prefix_alias = link_env.home / "opt alias"
    prefix_alias.symlink_to(link_env.opt_dir, target_is_directory=True)
    link_env.env["INSTALL_PREFIX"] = str(prefix_alias)
    point_link(link_env, "rg", release / "rg", relative=True)

    assert_listed(repo_dir, link_env, "rg", installed=True)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_ok(check)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_ok(install)
    assert not (link_env.home / "network-called").exists()


def test_relative_link_via_symlinked_bin_uses_physical_parent(
    repo_dir: Path, link_env: ToolStateEnv
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    link = point_link(link_env, "rg", executable, relative=True)
    alias = link_env.home / ".local/bin"
    alias.parent.mkdir(exist_ok=True)
    alias.symlink_to(link_env.bin_dir, target_is_directory=True)
    # Force logical cd to succeed at the wrong directory instead of falling back.
    shadow = Path(os.path.normpath(str(alias / link.readlink().parent)))
    shadow.mkdir(parents=True)
    link_env.bin_dir = alias
    link_env.env["INSTALL_BIN_DIR"] = str(alias)
    link_env.env["PATH"] = f"{alias}:{link_env.env['PATH']}"
    assert (alias / "rg").resolve() == executable

    assert_listed(repo_dir, link_env, "rg", installed=True)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_ok(check)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_ok(install)
    assert not (link_env.home / "network-called").exists()

    stale = link_env.opt_dir / "rg-14.1.0"
    stale.mkdir()
    mark_managed_release(stale, "rg", "14.1.0")
    prune = run_remote_ssh(repo_dir, ["prune", "--apply"], env=link_env.env)
    assert_ok(prune)
    assert executable.exists()
    assert not stale.exists()
    uninstall = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=link_env.env)
    assert_ok(uninstall)
    assert not (alias / "rg").is_symlink()
    assert not executable.parent.exists()
    assert shadow.is_dir()


def test_prefix_with_symlink_then_parent_uses_physical_directory(
    repo_dir: Path, link_env: ToolStateEnv
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    logical = link_env.home / "logical"
    logical.mkdir()
    child = link_env.home / "physical-child"
    child.mkdir()
    (logical / "jump").symlink_to(child, target_is_directory=True)
    shadow = logical / "opt/rg-15.2.0"
    shadow.mkdir(parents=True)
    prefix = logical / "jump/../opt"
    link_env.env["INSTALL_PREFIX"] = str(prefix)
    assert prefix.resolve() == link_env.opt_dir

    assert_listed(repo_dir, link_env, "rg", installed=True)
    assert_ok(run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env))
    assert_ok(run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env))
    assert not (link_env.home / "network-called").exists()
    stale = link_env.opt_dir / "rg-14.1.0"
    stale.mkdir()
    mark_managed_release(stale, "rg", "14.1.0")
    assert_ok(run_remote_ssh(repo_dir, ["prune", "--apply"], env=link_env.env))
    assert executable.exists()
    assert not stale.exists()
    assert_ok(run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=link_env.env))
    assert not executable.parent.exists()
    assert not (link_env.bin_dir / "rg").is_symlink()
    assert shadow.is_dir()


@pytest.mark.parametrize("removal", [["prune", "--apply"], ["uninstall", "--yes", "rg"]])
def test_symlink_then_parent_cannot_adopt_external_executable(
    repo_dir: Path, link_env: ToolStateEnv, removal: list[str]
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    outside = link_env.external_dir / "rg"
    write_executable(outside, "#!/bin/sh\nprintf outside\n")
    child = link_env.external_dir / "child"
    child.mkdir()
    (executable.parent / "jump").symlink_to(child, target_is_directory=True)
    link = point_link(link_env, "rg", executable.parent / "jump/../rg", relative=False)
    target = link.readlink()
    assert link.resolve() == outside

    assert_listed(repo_dir, link_env, "rg", installed=False)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_failed(check)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_failed(install)
    assert (link_env.home / "network-called").exists()
    result = run_remote_ssh(repo_dir, removal, env=link_env.env)
    assert_ok(result)
    assert outside.read_text() == "#!/bin/sh\nprintf outside\n"
    assert link.is_symlink() and link.readlink() == target
    assert not executable.parent.exists()  # The owned release is actually inactive.


@pytest.mark.parametrize(
    "version,marked", [("15.2.0.1", True), ("15.2.0.1", False), ("15.2.0.123-456", True)]
)
def test_version_prefix_does_not_count_as_exact_version(
    repo_dir: Path, link_env: ToolStateEnv, version: str, marked: bool
) -> None:
    executable = make_managed_tool(link_env, "rg", version)
    if not marked:
        (executable.parent / ".remote-ssh-release").unlink()

    assert_listed(repo_dir, link_env, "rg", installed=marked)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_failed(check)
    assert "status:    stale-local" in check.stdout
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_failed(install)
    assert (link_env.home / "network-called").exists()
    assert executable.exists()


@pytest.mark.parametrize("marked", [False, True], ids=["legacy", "marked"])
@pytest.mark.parametrize(
    "suffix,valid",
    [("123-456", True), ("123x-456", False), ("123-456x", False), ("123-456-7", False)],
)
def test_only_numeric_install_suffix_is_accepted(
    repo_dir: Path, link_env: ToolStateEnv, marked: bool, suffix: str, valid: bool
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    release = executable.parent.with_name(f"rg-15.2.0.{suffix}")
    executable.parent.rename(release)
    if not marked:
        (release / ".remote-ssh-release").unlink()
    point_link(link_env, "rg", release / "rg", relative=True)

    assert_listed(repo_dir, link_env, "rg", installed=marked and valid)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    if valid:
        assert_ok(check)
        assert_ok(install)
        assert not (link_env.home / "network-called").exists()
    else:
        assert_failed(check)
        assert_failed(install)
        assert (link_env.home / "network-called").exists()


@pytest.mark.parametrize("record", ["truncated", "dangling-link", "directory"])
def test_invalid_record_cannot_fall_back_to_legacy_matching(
    repo_dir: Path, link_env: ToolStateEnv, record: str
) -> None:
    executable = make_managed_tool(link_env, "rg", "15.2.0")
    marker = executable.parent / ".remote-ssh-release"
    if record == "truncated":
        marker.write_text("format=1\n")
    else:
        marker.unlink()
        if record == "dangling-link":
            marker.symlink_to("missing-marker")
        else:
            marker.mkdir()

    assert_listed(repo_dir, link_env, "rg", installed=False)
    check = run_remote_ssh(repo_dir, ["check", "--strict", "rg"], env=link_env.env)
    assert_failed(check)
    install = run_remote_ssh(repo_dir, ["tool", "install", "rg"], env=link_env.env)
    assert_failed(install)
    assert (link_env.home / "network-called").exists()
