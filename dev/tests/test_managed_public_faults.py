from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command, snapshot
from test_managed_update import bump, commit, git, upstream


def utility_stub(engine: EngineEnv, name: str, body: str) -> Path:
    path = Path(engine.env["PATH"].split(":")[1]) / name
    actual = shutil.which(name)
    assert actual
    write_executable(
        path,
        f'#!{engine.bash}\nactual={shlex.quote(actual)}\nfor target in "$@"; do :; done\n'
        + ('operation=""\nfor argument in "$@"; do case "$argument" in fetch|reset) operation="$argument"; break;; esac; done\n' if name == "git" else "")
        + body
        + '\nexec "$actual" "$@"\n',
    )
    return path


@pytest.mark.parametrize("last_alias", [False, True])
@pytest.mark.parametrize("owner_signal", ["KILL", "TERM"])
def test_public_alias_crash_records_only_actual_completed_members(
    engine: EngineEnv, last_alias: bool, owner_signal: str
) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    engine.asset("fd")
    upstream(engine)
    assert_ok(command(engine, "install", "rg", "--yes"))
    chosen = "nushell" if last_alias else "nu"
    stub = utility_stub(
        engine,
        "ln",
        f'if [[ "$target" == "$INSTALL_BIN_DIR/{chosen}" && ! -e "$HOME/crashed" ]]; then\n'
        ' "$actual" "$@" || exit $?\n printf once >"$HOME/crashed"\n'
        f' kill -{owner_signal} "$PPID"\n exit 0\nfi\n',
    )
    crashed = command(engine, "install", "nu", "--yes")
    assert crashed.returncode != 0
    stub.unlink()
    assert_ok(command(engine, "install", "fd", "--yes"))
    state = engine.private(
        "ms_state_load\nms_member_has rg\nms_member_has fd\nif ms_member_has nu; then echo member; else echo absent; fi\n"
    )
    assert_ok(state)
    assert state.stdout.strip() == ("member" if last_alias else "absent")
    assert_ok(command(engine, "update"))
    assert (engine.bin / "nu").is_symlink() == last_alias
    assert (engine.bin / "nushell").is_symlink() == last_alias
    if last_alias:
        # Recovered completion must save exact B receipts too; later payload
        # loss stays repairable instead of becoming an unproved new selector.
        payload = (engine.bin / "nu").resolve()
        payload.unlink()
        assert_ok(command(engine, "install", "nu", "--yes"))


@pytest.mark.parametrize("partial", [False, True])
def test_public_sigkill_recursive_remove_then_unrelated_install_and_update(
    engine: EngineEnv, partial: bool
) -> None:
    engine.asset("nu", aliases=("nushell",))
    engine.asset("rg")
    engine.asset("fd")
    upstream(engine)
    assert_ok(command(engine, "install", "rg", "nu", "--yes"))
    removal = '"$actual" -- "$target/nu"' if partial else '"$actual" "$@"'
    stub = utility_stub(
        engine,
        "rm",
        'if [[ "$1" == -rf && "$target" == "$INSTALL_PREFIX/nu-1.0" && ! -e "$HOME/crashed" ]]; then\n'
        f' {removal} || exit $?\n printf once >"$HOME/crashed"\n kill -KILL "$PPID"\n exit 0\nfi\n',
    )
    crashed = command(engine, "uninstall", "nu", "--yes")
    assert crashed.returncode != 0
    stub.unlink()
    assert_ok(command(engine, "install", "fd", "--yes"))
    state = engine.private(
        "ms_state_load\nms_member_has rg\nms_member_has fd\nif ms_member_has nu; then echo member; else echo absent; fi\n"
    )
    assert_ok(state)
    assert state.stdout.strip() == ("member" if partial else "absent")
    assert_ok(command(engine, "update"))
    assert (engine.bin / "nu").is_symlink() == partial
    if partial:
        assert (engine.opt / "nu-1.0/.remote-ssh-release").is_file()
        assert not (engine.opt / "nu-1.0/nu").exists()
        assert (engine.bin / "nu").readlink() != engine.opt / "nu-1.0/nu"
    else:
        assert not (engine.opt / "nu-1.0").exists()


def test_unlink_failure_retains_member_and_update_repairs_it(engine: EngineEnv) -> None:
    engine.asset("nu", aliases=("nushell",))
    upstream(engine)
    assert_ok(command(engine, "install", "nu", "--yes"))
    stub = utility_stub(
        engine,
        "rm",
        'if [[ "$target" == "$INSTALL_BIN_DIR/nushell" ]]; then exit 77; fi\n',
    )
    result = command(engine, "uninstall", "nu", "--yes")
    assert result.returncode == 1
    stub.unlink()
    assert_ok(engine.private("ms_state_load\nms_member_has nu\n"))
    assert_ok(command(engine, "update"))
    assert (engine.bin / "nu").is_symlink() and (engine.bin / "nushell").is_symlink()


def test_final_state_rename_failure_recovers_completed_install(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "rg", "--yes"))
    stub = utility_stub(
        engine,
        "mv",
        'if [[ "$target" == */state && -L "$INSTALL_BIN_DIR/nu" && -L "$INSTALL_BIN_DIR/nushell" && ! -e "$HOME/failed-state" ]]; then printf once >"$HOME/failed-state"; exit 74; fi\n',
    )
    result = command(engine, "install", "nu", "--yes")
    assert result.returncode == 1
    stub.unlink()
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has nu\n"))
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert_ok(engine.private("ms_state_load\nms_member_has nu\n"))


@pytest.mark.parametrize("failure", ["fetch", "reset"])
def test_git_failure_preserves_exit_code_and_managed_set(
    engine: EngineEnv, failure: str
) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    origin = upstream(engine)
    (origin / "revision.txt").write_text("new checkout")
    commit(engine, origin)
    old_head = git(engine, engine.repo, "rev-parse", "HEAD")
    calls = (Path(engine.env["HOME"]) / "curl.calls").read_bytes()
    stub = utility_stub(
        engine, "git", f'if [[ "$operation" == {failure} ]]; then printf "%s" "$operation" >"$HOME/failed-git-operation"; exit 17; fi\n'
    )
    result = command(engine, "update")
    assert result.returncode == 17
    assert (Path(engine.env["HOME"]) / "failed-git-operation").read_text() == failure
    assert git(engine, engine.repo, "rev-parse", "HEAD") == old_head
    assert (Path(engine.env["HOME"]) / "curl.calls").read_bytes() == calls
    assert_ok(engine.private("ms_state_load\nms_member_has rg\n"))
    stub.unlink()
    assert_ok(command(engine, "update"))
    assert (engine.repo / "revision.txt").read_text() == "new checkout"


def test_sigkill_after_real_reset_is_recovered_before_unrelated_install(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("fd")
    assert_ok(command(engine, "install", "rg", "--yes"))
    origin = upstream(engine)
    bump(engine, origin, "rg")
    commit(engine, origin)
    stub = utility_stub(
        engine,
        "git",
        'if [[ "$operation" == reset && ! -e "$HOME/reset-crashed" ]]; then\n'
        ' "$actual" "$@" || exit $?\n printf once >"$HOME/reset-crashed"\n kill -KILL "$PPID"\n exit 0\nfi\n',
    )
    result = command(engine, "update")
    assert result.returncode != 0
    stub.unlink()
    assert git(engine, engine.repo, "rev-parse", "HEAD") == git(
        engine, origin, "rev-parse", "HEAD"
    )
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(command(engine, "update"))
    assert (engine.bin / "rg").readlink() == engine.opt / "rg-2.0/rg"
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has fd\n"))


def test_pair_and_xdg_isolation_across_update_and_uninstall(engine: EngineEnv) -> None:
    engine.asset("rg")
    engine.asset("fd")
    upstream(engine)
    first_bin = engine.bin
    assert_ok(command(engine, "install", "rg", "--yes"))
    second_bin = Path(engine.env["HOME"]) / "other-bin"
    engine.bin = second_bin
    engine.env["INSTALL_BIN_DIR"] = str(second_bin)
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has fd\nif ms_member_has rg; then exit 91; fi\n"
        )
    )
    assert_ok(command(engine, "update"))
    engine.bin = first_bin
    engine.env["INSTALL_BIN_DIR"] = str(first_bin)
    engine.env["XDG_CONFIG_HOME"] = str(Path(engine.env["HOME"]) / "other-config")
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nif ms_member_has fd; then exit 91; fi\n"
        )
    )
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    assert_ok(command(engine, "update"))
    assert not (first_bin / "rg").is_symlink()
    assert (second_bin / "fd").is_symlink()


def test_sigkill_after_reuse_goal_preserves_actual_new_member(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    engine.asset("fd")
    assert_ok(command(engine, "install", "rg", "--yes"))
    # This owned install appeared after one-time adoption. Explicit install
    # reuses it, but mere presence must not make it an automatic member.
    root = engine.opt / "nu-1.0"
    write_executable(root / "nu", "#!/bin/sh\nexit 0\n")
    (root / ".remote-ssh-release").write_text(
        "format=1\ntool=nu\nversion=1.0\nlayout=binary\nexecutable=nu\n"
    )
    for name in ["nu", "nushell"]:
        (engine.bin / name).symlink_to(root / "nu")
    stub = utility_stub(
        engine,
        "mv",
        'source="$1"\nif [[ "$source" == -f ]]; then source="$3"; elif [[ "$source" == -- ]]; then source="$2"; fi\n'
        'if [[ "$target" == */state && ! -e "$HOME/reuse-crashed" ]] && /usr/bin/grep -a -q reuse-intent "$source"; then\n'
        ' "$actual" "$@" || exit $?\n printf once >"$HOME/reuse-crashed"\n kill -KILL "$PPID"\n exit 0\nfi\n',
    )
    result = command(engine, "install", "nu", "--yes")
    assert result.returncode != 0
    stub.unlink()
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nms_member_has nu\nms_member_has fd\n"
        )
    )


def test_two_public_installers_keep_both_members_without_shared_publication(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("fd")
    processes = [
        subprocess.Popen(
            [engine.bash, engine.repo / "bin/remote-ssh", "install", tool, "--yes"],
            env=engine.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for tool in ["rg", "fd"]
    ]
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=60)
            assert process.returncode == 0, (stdout, stderr)
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has fd\n"))
    assert (engine.bin / "rg").is_symlink() and (engine.bin / "fd").is_symlink()


@pytest.mark.parametrize("substitution", ["member", "parent", "marker", "selector"])
def test_repair01_pending_install_overrides_terminal_history_and_protects_foreign_scope(engine: EngineEnv, substitution: str) -> None:
    engine.asset("nu", layout="bundle", aliases=("nushell",))
    engine.asset("fd")
    upstream(engine)
    assert_ok(command(engine, "install", "nu", "--yes"))
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    stub = utility_stub(engine, "ln", 'if [[ "$target" == "$INSTALL_BIN_DIR/nu" && ! -e "$HOME/crashed" ]]; then\n "$actual" "$@" || exit $?\n printf once >"$HOME/crashed"\n kill -KILL "$PPID"\n exit 0\nfi\n')
    assert command(engine, "install", "nu", "--yes").returncode != 0
    stub.unlink()
    assert_ok(engine.private('ms_state_load\nms_journal_active\n[[ "$MS_BATCH_COMMAND" == install && "$MS_BATCH_PHASE" == tools ]]\nms_row_find item "$MS_BATCH" nu\n[[ "${MS_ROWS[MS_INDEX+3]}" == running ]]\nif ms_member_has nu; then exit 91; fi\n'))
    root = (engine.bin / "nu").readlink().parent.parent
    outside = Path(engine.env["HOME"]) / "foreign"
    outside.mkdir()
    (outside / "nu").write_text("foreign payload")
    if substitution == "member":
        (root / "bin/nu").unlink()
        (root / "bin/nu").symlink_to(outside / "nu")
    elif substitution == "parent":
        (root / "bin/nu").unlink()
        (root / "bin").rmdir()
        (root / "bin").symlink_to(outside, target_is_directory=True)
    elif substitution == "marker":
        marker = root / ".remote-ssh-release"
        marker.rename(outside / "marker")
        marker.symlink_to(outside / "marker")
    else:
        (engine.bin / "nu").unlink()
        (engine.bin / "nu").symlink_to(outside / "nu")
    # A rejected mutator still acquires/releases command locks. Protect actual
    # journal/payload bytes and paths, rather than lock-directory mtimes.
    before = snapshot(engine)
    foreign_info = (outside / "nu").stat()
    for args in [("install", "fd", "--yes"), ("update",)]:
        result = command(engine, *args)
        assert result.returncode == 1
        assert snapshot(engine) == before
    assert (outside / "nu").read_text() == "foreign payload"
    assert (outside / "nu").stat().st_mode == foreign_info.st_mode
    assert (outside / "nu").stat().st_mtime_ns == foreign_info.st_mtime_ns
    assert_ok(engine.private('ms_state_load\nms_journal_active\n[[ "$MS_BATCH_COMMAND" == install && "$MS_BATCH_PHASE" == tools ]]\nms_row_find item "$MS_BATCH" nu\n[[ "${MS_ROWS[MS_INDEX+3]}" == running ]]\nif ms_member_has nu; then exit 91; fi\n'))
