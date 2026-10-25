from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ToolStateEnv, assert_ok, mark_managed_release, run_remote_ssh


@pytest.mark.parametrize("command", [["prune", "--apply"], ["uninstall", "--yes", "rg"]])
def test_removal_preserves_unowned_or_invalid_releases(
    repo_dir: Path, tool_env: ToolStateEnv, command: list[str]
) -> None:
    names = ["rg-personal-notes", "rg-14.1.0", "rg-13.1.0", "rg-12.1.0", "rg-11.1.0"]
    for name in names:
        (tool_env.opt_dir / name).mkdir()
    (tool_env.opt_dir / names[2] / ".remote-ssh-release").write_text("format=1\n")
    mark_managed_release(tool_env.opt_dir / names[3], "fd", "12.1.0")
    mark_managed_release(tool_env.opt_dir / names[4], "rg", "11.1.0")
    (tool_env.opt_dir / names[4] / ".remote-ssh-release").write_text(
        "format=1\ntool=rg\nversion=11.1.0\nlayout=binary\nexecutable=../outside\n"
    )
    result = run_remote_ssh(repo_dir, command, env=tool_env.env)
    assert_ok(result)
    assert all((tool_env.opt_dir / name).is_dir() for name in names)


def test_prune_protects_entire_nested_release_via_alias(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    active = tool_env.opt_dir / "nu-0.112.2"
    active.mkdir()
    mark_managed_release(active, "nu", "0.112.2", executable="bin/nu", layout="bundle")
    (tool_env.bin_dir / "custom-nu-alias").symlink_to(active / "bin" / "nu")
    stale = tool_env.opt_dir / "nu-0.100.0"
    stale.mkdir()
    mark_managed_release(stale, "nu", "0.100.0", executable="bin/nu", layout="bundle")
    result = run_remote_ssh(repo_dir, ["prune", "--apply"], env=tool_env.env)
    assert_ok(result)
    assert active.is_dir()
    assert not stale.exists()


def test_uninstall_preserves_same_prefix_foreign_symlink(
    repo_dir: Path, tool_env: ToolStateEnv
) -> None:
    foreign = tool_env.opt_dir / "rg-personal-notes"
    foreign.mkdir()
    executable = foreign / "rg"
    executable.write_text("keep\n")
    link = tool_env.bin_dir / "rg"
    link.symlink_to(executable)
    result = run_remote_ssh(repo_dir, ["uninstall", "--yes", "rg"], env=tool_env.env)
    assert_ok(result)
    assert link.is_symlink()
    assert executable.read_text() == "keep\n"


@pytest.mark.parametrize("tamper", ["marker-link", "parent-link", "literal-code"])
def test_ownership_record_cannot_adopt_external_paths_or_execute_code(
    repo_dir: Path, tool_env: ToolStateEnv, tamper: str
) -> None:
    release = tool_env.opt_dir / "rg-15.1.0"
    release.mkdir()
    outside = tool_env.home / "outside"
    outside.mkdir()
    mark_managed_release(release, "rg", "15.1.0", executable="bin/rg")
    marker = release / ".remote-ssh-release"
    if tamper == "marker-link":
        external_marker = outside / "marker"
        marker.rename(external_marker)
        marker.symlink_to(external_marker)
    elif tamper == "parent-link":
        (release / "bin/rg").rename(outside / "rg")
        (release / "bin").rmdir()
        (release / "bin").symlink_to(outside, target_is_directory=True)
    else:
        marker.write_text(
            f'format=1\ntool=$(touch "{outside}/executed")\nversion=15.1.0\nlayout=binary\nexecutable=bin/rg\n'
        )
    result = run_remote_ssh(repo_dir, ["prune", "--apply"], env=tool_env.env)
    assert_ok(result)
    assert release.is_dir()
    assert outside.is_dir()
    assert not (outside / "executed").exists()
