from __future__ import annotations

import os
import shlex
import shutil
import stat
from pathlib import Path

import pytest
from conftest import (
    IsolatedEnv,
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_managed_tool,
    mark_managed_release,
    run_cmd,
    run_remote_ssh,
    write_executable,
)


def prepare_prune_dirs(env: IsolatedEnv) -> tuple[Path, Path]:
    bin_dir = env.home / "managed-bin"
    opt_dir = env.home / "managed-opt"
    bin_dir.mkdir()
    opt_dir.mkdir()
    return bin_dir, opt_dir


def prepare_rg_install(bin_dir: Path, opt_dir: Path) -> None:
    active = opt_dir / "rg-15.1.0"
    stale = opt_dir / "rg-14.1.0"
    unknown = opt_dir / "not-a-tool-1.0.0"
    active.mkdir()
    stale.mkdir()
    unknown.mkdir()
    rg = active / "rg"
    rg.write_text("#!/usr/bin/env bash\nprintf rg\n", encoding="utf-8")
    rg.chmod(0o755)
    mark_managed_release(active, "rg", "15.1.0")
    mark_managed_release(stale, "rg", "14.1.0")
    (bin_dir / "rg").symlink_to(rg)


def prune_env(env: IsolatedEnv, bin_dir: Path, opt_dir: Path) -> dict[str, str]:
    return env.env | {
        "INSTALL_PREFIX": str(opt_dir),
        "INSTALL_BIN_DIR": str(bin_dir),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }


def test_prune_dry_run_keeps_candidates(
    repo_dir: Path, isolated_env: IsolatedEnv
) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    prepare_rg_install(bin_dir, opt_dir)

    result = run_remote_ssh(
        repo_dir, ["prune"], env=prune_env(isolated_env, bin_dir, opt_dir)
    )

    assert_ok(result)
    assert "remote-ssh prune (dry-run)" in result.stdout
    assert f"candidate: {opt_dir / 'rg-14.1.0'}" in result.stdout
    assert (opt_dir / "rg-14.1.0").is_dir()
    assert (opt_dir / "rg-15.1.0").is_dir()
    assert (opt_dir / "not-a-tool-1.0.0").is_dir()


def test_prune_apply_removes_only_safe_candidates(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    prepare_rg_install(bin_dir, opt_dir)
    outside = isolated_env.home / "outside" / "rg-1.0.0"
    outside.mkdir(parents=True)

    result = run_remote_ssh(
        repo_dir,
        ["prune", "--apply"],
        env=prune_env(isolated_env, bin_dir, opt_dir),
    )

    assert_ok(result)
    assert "remote-ssh prune --apply" in result.stdout
    assert f"removed: {opt_dir / 'rg-14.1.0'}" in result.stdout
    assert not (opt_dir / "rg-14.1.0").exists()
    assert (opt_dir / "rg-15.1.0").is_dir()
    assert (opt_dir / "not-a-tool-1.0.0").is_dir()
    assert outside.is_dir()


def test_prune_preserves_relative_symlink_target(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    active = opt_dir / "rg-15.1.0"
    stale = opt_dir / "rg-14.1.0"
    active.mkdir()
    stale.mkdir()
    rg = active / "rg"
    rg.write_text("#!/usr/bin/env bash\nprintf rg\n", encoding="utf-8")
    rg.chmod(0o755)
    mark_managed_release(active, "rg", "15.1.0")
    mark_managed_release(stale, "rg", "14.1.0")
    (bin_dir / "rg").symlink_to(Path("../managed-opt/rg-15.1.0/rg"))

    result = run_remote_ssh(
        repo_dir,
        ["prune", "--apply"],
        env=prune_env(isolated_env, bin_dir, opt_dir),
    )

    assert_ok(result)
    assert f"removed: {stale}" in result.stdout
    assert not stale.exists()
    assert active.is_dir()


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
def test_prune_scans_symlinked_prefix_without_following_child_links(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    active = make_managed_tool(tool_env, "rg", "15.1.0")
    stale = tool_env.opt_dir / "rg-14.1.0"
    stale.mkdir()
    mark_managed_release(stale, "rg", "14.1.0")
    legacy = tool_env.opt_dir / "rg-13.1.0"
    legacy.mkdir()
    unknown = tool_env.opt_dir / "personal-notes"
    unknown.mkdir()
    outside = tool_env.external_dir / "rg-12.1.0"
    outside.mkdir()
    mark_managed_release(outside, "rg", "12.1.0")
    child_link = tool_env.opt_dir / outside.name
    child_link.symlink_to(outside, target_is_directory=True)
    prefix = tool_env.home / "opt alias"
    prefix.symlink_to(tool_env.opt_dir, target_is_directory=True)
    env = tool_env.env | {"INSTALL_PREFIX": str(prefix)}

    result = run_remote_ssh(
        repo_dir, ["prune", *(["--apply"] if apply else [])], env=env
    )

    assert_ok(result)
    assert f"{'removed' if apply else 'candidate'}: {stale}" in result.stdout
    assert stale.exists() != apply
    assert active.exists()
    assert legacy.is_dir() and unknown.is_dir() and outside.is_dir()
    assert child_link.is_symlink()


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("aliased_prefix", [False, True], ids=["physical", "alias"])
@pytest.mark.parametrize("mode", [0o111, 0o444], ids=["no-read", "no-search"])
def test_prune_aborts_when_bin_cannot_be_inspected(
    repo_dir: Path,
    tool_env: ToolStateEnv,
    runtime_bash: str,
    apply: bool,
    aliased_prefix: bool,
    mode: int,
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    executable = make_managed_tool(
        tool_env, "rg", "15.1.0", content="#!/bin/sh\nexit 0\n"
    )
    stale = tool_env.opt_dir / "rg-14.1.0"
    stale.mkdir()
    mark_managed_release(stale, "rg", "14.1.0")
    env = tool_env.env.copy()
    if aliased_prefix:
        alias = tool_env.home / "opt alias"
        alias.symlink_to(tool_env.opt_dir, target_is_directory=True)
        env["INSTALL_PREFIX"] = str(alias)
    original_mode = stat.S_IMODE(tool_env.bin_dir.stat().st_mode)
    tool_env.bin_dir.chmod(mode)
    try:
        denied_permission = os.R_OK if mode == 0o111 else os.X_OK
        if os.access(tool_env.bin_dir, denied_permission):
            pytest.skip("Current user bypasses the tested directory permissions")
        if mode == 0o111:
            assert_ok(run_cmd([tool_env.bin_dir / "rg"], env=env))
        result = run_cmd(
            [
                runtime_bash,
                repo_dir / "bin/remote-ssh",
                "prune",
                *(["--apply"] if apply else []),
            ],
            env=env,
        )
    finally:
        tool_env.bin_dir.chmod(original_mode)

    assert_failed(result)
    assert str(tool_env.bin_dir) in result.stderr
    assert "prune aborted" in result.stderr
    assert "candidate:" not in result.stdout and "removed:" not in result.stdout
    assert executable.exists() and stale.is_dir()
    assert (tool_env.bin_dir / "rg").is_symlink()
    assert_ok(run_cmd([tool_env.bin_dir / "rg"], env=env))


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("operation", ["find", "readlink"])
def test_prune_aborts_on_failed_active_link_inventory(
    repo_dir: Path,
    tool_env: ToolStateEnv,
    runtime_bash: str,
    apply: bool,
    operation: str,
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    active = make_managed_tool(tool_env, "rg", "15.1.0")
    other = tool_env.opt_dir / "rg-14.1.0"
    other.mkdir()
    mark_managed_release(other, "rg", "14.1.0")
    (tool_env.bin_dir / "custom-rg").symlink_to(other / "rg")
    alias = tool_env.home / "bin alias"
    alias.symlink_to(tool_env.bin_dir, target_is_directory=True)
    temporary = tool_env.home / "prune-tmp"
    temporary.mkdir()
    actual_command = shutil.which(operation)
    assert actual_command
    write_executable(
        tool_env.external_dir / operation,
        f"""#!/bin/sh
if [ "$1" = "$PRUNE_TEST_FAIL_PATH" ]; then
  # A partial listing must not be consumed after find returns failure.
  if [ "$PRUNE_TEST_OPERATION" = find ]; then
    printf '%s\\000' "$PRUNE_TEST_PARTIAL_LINK"
  fi
  exit 9
fi
exec {shlex.quote(actual_command)} "$@"
""",
    )
    env = tool_env.env | {
        "INSTALL_BIN_DIR": str(alias),
        "PATH": f"{tool_env.external_dir}:{tool_env.env['PATH']}",
        "TMPDIR": str(temporary),
        "PRUNE_TEST_OPERATION": operation,
        "PRUNE_TEST_FAIL_PATH": str(tool_env.bin_dir.resolve() / "rg")
        if operation == "readlink"
        else str(tool_env.bin_dir.resolve()),
        "PRUNE_TEST_PARTIAL_LINK": str(tool_env.bin_dir / "rg"),
    }

    result = run_remote_ssh(
        repo_dir, ["prune", *(["--apply"] if apply else [])], env=env
    )

    assert_failed(result)
    assert "prune aborted" in result.stderr
    assert "candidate:" not in result.stdout and "removed:" not in result.stdout
    assert active.exists() and (other / "rg").exists()
    assert list(temporary.iterdir()) == []


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
def test_prune_accepts_readonly_bin_and_unusual_custom_alias(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    active = make_managed_tool(tool_env, "rg", "15.1.0")
    custom = tool_env.opt_dir / "rg-14.1.0"
    custom.mkdir()
    mark_managed_release(custom, "rg", "14.1.0")
    (tool_env.bin_dir / "custom rg\nalias").symlink_to(custom / "rg")
    stale = tool_env.opt_dir / "rg-13.1.0"
    stale.mkdir()
    mark_managed_release(stale, "rg", "13.1.0")
    (tool_env.bin_dir / "notes").write_text("keep\n")
    outside = tool_env.external_dir / "foreign"
    outside.write_text("keep\n")
    (tool_env.bin_dir / "unmanaged-link").symlink_to(outside)
    prefix = tool_env.home / "opt alias"
    prefix.symlink_to(tool_env.opt_dir, target_is_directory=True)
    temporary = tool_env.home / "prune-tmp"
    temporary.mkdir()
    original_mode = stat.S_IMODE(tool_env.bin_dir.stat().st_mode)
    tool_env.bin_dir.chmod(0o555)
    try:
        result = run_remote_ssh(
            repo_dir,
            ["prune", *(["--apply"] if apply else [])],
            env=tool_env.env
            | {"INSTALL_PREFIX": str(prefix), "TMPDIR": str(temporary)},
        )
    finally:
        tool_env.bin_dir.chmod(original_mode)

    assert_ok(result)
    assert active.exists() and (custom / "rg").exists()
    assert stale.exists() != apply
    assert outside.read_text() == "keep\n"
    assert (tool_env.bin_dir / "notes").read_text() == "keep\n"
    assert list(temporary.iterdir()) == []


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("kind", ["missing", "file", "broken-link"])
def test_prune_rejects_invalid_bin_directory(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool, kind: str
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    active = make_managed_tool(tool_env, "rg", "15.1.0")
    invalid = tool_env.home / "invalid-bin"
    if kind == "file":
        invalid.write_text("keep\n")
    elif kind == "broken-link":
        invalid.symlink_to("absent")

    result = run_remote_ssh(
        repo_dir,
        ["prune", *(["--apply"] if apply else [])],
        env=tool_env.env | {"INSTALL_BIN_DIR": str(invalid)},
    )

    assert_failed(result)
    assert str(invalid) in result.stderr and "prune aborted" in result.stderr
    assert "candidate:" not in result.stdout and "removed:" not in result.stdout
    assert active.exists()
    assert not invalid.is_dir()


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
def test_prune_accepts_empty_readable_bin_directory(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    inactive = make_managed_tool(tool_env, "rg", "15.1.0")
    (tool_env.bin_dir / "rg").unlink()
    empty = tool_env.home / "empty-bin"
    empty.mkdir()

    result = run_remote_ssh(
        repo_dir,
        ["prune", *(["--apply"] if apply else [])],
        env=tool_env.env | {"INSTALL_BIN_DIR": str(empty)},
    )

    assert_ok(result)
    assert f"{'removed' if apply else 'candidate'}: {inactive.parent}" in result.stdout
    assert inactive.exists() != apply


def test_prune_inventory_failure_aborts_without_errexit_or_pipefail(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    active = make_managed_tool(tool_env, "rg", "15.1.0")
    inactive = tool_env.opt_dir / "rg-14.1.0"
    inactive.mkdir()
    mark_managed_release(inactive, "rg", "14.1.0")
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        set -eu
        . "$1/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        ms_prune_collect() { return 9; }
        set +e
        set +o pipefail
        remote_ssh_cmd_prune_main --apply
        exit "$?"
        """,
            "_",
            repo_dir,
        ],
        env=tool_env.env,
    )

    assert_failed(result)
    assert "prune aborted" in result.stderr
    assert "candidate:" not in result.stdout and "removed:" not in result.stdout
    assert active.exists() and inactive.is_dir()


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("payload", ["helper", "data"])
def test_prune_protects_bundle_referenced_only_through_additional_payload(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool, payload: str
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    active = tool_env.opt_dir / "nvim-0.11.5"
    active.mkdir()
    mark_managed_release(
        active, "nvim", "0.11.5", executable="bin/nvim", layout="bundle"
    )
    helper = active / "libexec/editor-helper"
    write_executable(helper, "#!/bin/sh\nprintf helper\n")
    data = active / "share/runtime-data"
    data.parent.mkdir()
    data.write_text("runtime data\n")
    referenced = helper if payload == "helper" else data
    alias = tool_env.bin_dir / "custom-payload"
    alias.symlink_to(referenced)
    stale = tool_env.opt_dir / "nvim-0.11.4"
    stale.mkdir()
    mark_managed_release(
        stale, "nvim", "0.11.4", executable="bin/nvim", layout="bundle"
    )
    legacy = tool_env.opt_dir / "nvim-0.11.3"
    legacy.mkdir()
    (legacy / "notes").write_text("keep\n")
    invalid = tool_env.opt_dir / "nvim-0.11.2"
    invalid.mkdir()
    (invalid / ".remote-ssh-release").write_text("format=1\n")
    (invalid / "notes").write_text("keep\n")
    (tool_env.bin_dir / "invalid-payload").symlink_to(invalid / "notes")
    assert not (tool_env.bin_dir / "nvim").exists()

    result = run_remote_ssh(
        repo_dir, ["prune", *(["--apply"] if apply else [])], env=tool_env.env
    )

    assert_ok(result)
    assert f"candidate: {active}\n" not in result.stdout
    assert f"removed: {active}\n" not in result.stdout
    assert f"{'removed' if apply else 'candidate'}: {stale}\n" in result.stdout
    assert active.is_dir() and referenced.exists() and alias.is_symlink()
    assert stale.exists() != apply
    assert legacy.is_dir() and invalid.is_dir()
    if payload == "helper":
        assert run_cmd([alias], env=tool_env.env).stdout == "helper"
    else:
        assert alias.read_text() == "runtime data\n"


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
def test_prune_does_not_protect_release_from_reference_outside_prefix(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, apply: bool
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    inactive = tool_env.opt_dir / "rg-15.1.0"
    inactive.mkdir()
    mark_managed_release(inactive, "rg", "15.1.0")
    outside = (
        tool_env.opt_dir.with_name(tool_env.opt_dir.name + "-outside")
        / "rg-15.1.0/helper"
    )
    write_executable(outside, "#!/bin/sh\nprintf outside\n")
    alias = tool_env.bin_dir / "outside-helper"
    alias.symlink_to(outside)

    result = run_remote_ssh(
        repo_dir, ["prune", *(["--apply"] if apply else [])], env=tool_env.env
    )

    assert_ok(result)
    assert f"{'removed' if apply else 'candidate'}: {inactive}\n" in result.stdout
    assert inactive.exists() != apply
    assert outside.exists() and alias.is_symlink()
    assert run_cmd([alias], env=tool_env.env).stdout == "outside"


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize(
    "protect_suffix", [False, True], ids=["base-active", "suffix-active"]
)
def test_prune_matches_literal_complete_paths_without_grep(
    repo_dir: Path,
    tool_env: ToolStateEnv,
    runtime_bash: str,
    apply: bool,
    protect_suffix: bool,
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    prefix = tool_env.home / "opt [x]*?+ space"
    prefix.mkdir()
    base = prefix / "rg-15.1.0"
    suffixed = prefix / "rg-15.1.0.123-456"
    for release in (base, suffixed):
        release.mkdir()
        mark_managed_release(release, "rg", "15.1.0")
    active, inactive = (suffixed, base) if protect_suffix else (base, suffixed)
    (tool_env.bin_dir / "rg").symlink_to(active / "rg")
    write_executable(
        tool_env.external_dir / "grep",
        '#!/bin/sh\nprintf called > "$HOME/grep-called"\nexit 2\n',
    )
    env = tool_env.env | {
        "INSTALL_PREFIX": str(prefix),
        "PATH": f"{tool_env.external_dir}:{tool_env.env['PATH']}",
    }

    result = run_remote_ssh(
        repo_dir, ["prune", *(["--apply"] if apply else [])], env=env
    )

    assert_ok(result)
    assert active.is_dir()
    assert inactive.exists() != apply
    assert f"{'removed' if apply else 'candidate'}: {inactive}\n" in result.stdout
    assert not (tool_env.home / "grep-called").exists()
