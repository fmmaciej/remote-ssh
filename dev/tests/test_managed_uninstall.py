from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command, snapshot


@pytest.mark.parametrize(
    "args", [[], ["--yes"], ["--help", "--unknown"], ["rg", "unknown", "--yes"], ["rg"]]
)
def test_uninstall_invalid_or_unconfirmed_preserves_everything(
    engine: EngineEnv, args: list[str]
) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    before = snapshot(engine)
    result = command(engine, "uninstall", *args)
    assert result.returncode == 1
    assert snapshot(engine) == before


def test_uninstall_known_absent_is_readonly_noop(engine: EngineEnv) -> None:
    engine.asset("rg")
    result = command(engine, "uninstall", "rg", "--yes")
    assert_ok(result)
    assert not engine.opt.exists() and not engine.bin.exists()


def test_uninstall_removes_all_own_releases_aliases_and_keeps_protected_other_tools(
    engine: EngineEnv,
) -> None:
    engine.asset("nu", aliases=("nushell",))
    engine.asset("rg")
    assert_ok(command(engine, "install", "nu", "rg", "--yes"))
    inactive = engine.opt / "nu-0.1"
    inactive.mkdir()
    write_executable(inactive / "nu", "#!/bin/sh\nexit 0\n")
    (inactive / ".remote-ssh-release").write_text(
        "format=1\ntool=nu\nversion=0.1\nlayout=binary\nexecutable=nu\n"
    )
    protected = engine.opt / "nu-personal-notes"
    protected.mkdir()
    (protected / "notes").write_text("keep")
    custom = engine.bin / "old alias\nwith newline"
    custom.symlink_to(engine.opt / "nu-1.0/nu")
    result = command(engine, "uninstall", "nu", "--yes")
    assert_ok(result)
    assert "Protected remains" in result.stdout
    assert not (engine.bin / "nu").exists() and not (engine.bin / "nushell").exists()
    assert not custom.is_symlink()
    assert not (engine.opt / "nu-1.0").exists() and not inactive.exists()
    assert (protected / "notes").read_text() == "keep"
    assert (engine.bin / "rg").is_symlink()
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nif ms_member_has nu; then exit 91; fi\n"
        )
    )
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert_ok(engine.private("ms_state_load\nif ms_member_has nu; then exit 91; fi\n"))


def test_foreign_required_alias_aborts_entire_uninstall_selection(
    engine: EngineEnv,
) -> None:
    engine.asset("nu", aliases=("nushell",))
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "nu", "--yes"))
    (engine.bin / "nushell").unlink()
    (engine.bin / "nushell").symlink_to(Path(engine.env["HOME"]) / "foreign")
    before = snapshot(engine)
    result = command(engine, "uninstall", "rg", "nu", "--yes")
    assert result.returncode == 1
    assert snapshot(engine) == before
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has nu\n"))


def test_retired_tool_uninstall_uses_saved_live_proof(engine: EngineEnv) -> None:
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    (engine.repo / "tools/defs/nu.sh").unlink()
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    assert not (engine.opt / "nu-1.0").exists()
    assert_ok(engine.private("ms_state_load\nif ms_member_has nu; then exit 91; fi\n"))


def test_partial_recursive_removal_keeps_member_and_allows_safe_repair_without_deleting_remainder(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    fake_bin = Path(engine.env["PATH"].split(":")[1])
    write_executable(
        fake_bin / "rm",
        f'#!{engine.bash}\nfor target in "$@"; do :; done\n'
        'if [[ "$1" == -rf && "$target" == "$INSTALL_PREFIX/rg-1.0" ]]; then\n'
        ' /bin/rm -- "$target/rg"\n exit 71\nfi\nexec /bin/rm "$@"\n',
    )
    result = command(engine, "uninstall", "rg", "--yes")
    assert result.returncode == 1
    old = engine.opt / "rg-1.0"
    assert old.exists() and (old / ".remote-ssh-release").is_file()
    assert not (old / "rg").exists()
    assert_ok(
        engine.private(
            'ms_state_load\nms_member_has rg\nms_journal_active\n[[ "$MS_BATCH_PHASE" == settled ]]\nms_row_find protected rg "$MS_PREFIX/rg-1.0"\n'
        )
    )
    (fake_bin / "rm").unlink()
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert (engine.bin / "rg").readlink() != old / "rg"
    assert old.exists()  # no receipt was used as recursive deletion authority
    assert_ok(engine.private("ms_state_load\nms_member_has rg\n"))


def test_wrapper_rejects_unpinned_and_requires_same_confirmation(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    for args in [("latest",), ("0.1",), ("1.0",), ()]:
        result = subprocess.run(
            [engine.bash, engine.repo / "tools/install-tool.sh", "rg", *args],
            env=engine.env,
            text=True,
            input="",
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 1
        assert not engine.opt.exists()


def test_library_state_only_commands_work_with_readonly_bin_and_do_not_adopt_other_pair(
    engine: EngineEnv,
) -> None:
    import shlex

    engine.asset("rg")
    engine.asset("fd")
    engine.asset("flyline", layout="bash-builtin")
    assert_ok(command(engine, "install", "rg", "--yes"))
    fake_bin = Path(engine.env["PATH"].split(":")[1])
    (fake_bin / "bash").unlink()
    write_executable(
        fake_bin / "bash",
        f'#!{engine.bash}\nif [[ "$*" == *remote-ssh-library-probe* ]]; then exit 0; fi\nexec {shlex.quote(engine.bash)} "$@"\n',
    )
    engine.bin.chmod(0o555)
    try:
        assert_ok(command(engine, "install", "flyline", "--yes"))
        assert_ok(command(engine, "uninstall", "flyline", "--yes"))
        assert_ok(command(engine, "install", "flyline", "--yes"))
    finally:
        engine.bin.chmod(0o755)
    active = (engine.opt / ".active/flyline").readlink()
    engine.env["INSTALL_BIN_DIR"] = str(Path(engine.env["HOME"]) / "other-bin")
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has fd\nif ms_member_has flyline || ms_member_has rg; then exit 91; fi\n"
        )
    )
    assert (engine.opt / ".active/flyline").readlink() == active


def test_first_uninstall_preserves_legacy_fzf_hint_without_membership(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    root = engine.opt / "rg-1.0"
    write_executable(root / "rg", "#!/bin/sh\nexit 0\n")
    (root / ".remote-ssh-release").write_text(
        "format=1\ntool=rg\nversion=1.0\nlayout=binary\nexecutable=rg\n"
    )
    engine.bin.mkdir()
    (engine.bin / "rg").symlink_to(root / "rg")
    legacy = Path(engine.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    legacy.parent.mkdir()
    legacy.write_text("fzf\n")
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    assert legacy.read_text() == "fzf\n"
    assert_ok(
        engine.private(
            'ms_state_load\n[[ "$MS_FZF_HINT" == 1 ]]\nif ms_member_has fzf || ms_member_has rg; then exit 91; fi\n'
        )
    )


def test_uninstall_previews_complete_owned_scope_and_membership_before_confirmation(
    engine: EngineEnv,
) -> None:
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    before = snapshot(engine)
    result = command(engine, "uninstall", "nu")
    assert result.returncode == 1
    for text in [
        "Owned selectors to remove",
        "Owned release scope to remove",
        "Managed membership to remove",
        str(engine.bin / "nu"),
        str(engine.bin / "nushell"),
        str(engine.opt / "nu-1.0"),
    ]:
        assert text in result.stdout
    assert snapshot(engine) == before


def repair_snapshot(engine: EngineEnv) -> dict[str, tuple[int, int, bytes | str]]:
    """Complete synthetic HOME bytes/targets, modes and mtimes; excludes atime."""
    rows = {}
    for path in sorted(Path(engine.env["HOME"]).rglob("*")):
        info = path.lstat()
        value = str(path.readlink()) if path.is_symlink() else path.read_bytes() if path.is_file() else b""
        rows[str(path)] = (info.st_mode, info.st_mtime_ns, value)
    return rows


def test_repair01_repeat_completed_uninstall_is_readonly_then_unrelated_update(engine: EngineEnv) -> None:
    from test_managed_update import upstream

    engine.asset("rg")
    engine.asset("fd")
    upstream(engine)
    (Path(engine.env["HOME"]) / ".bashrc").write_text("# synthetic startup; keep\n")
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    before = repair_snapshot(engine)
    again = command(engine, "uninstall", "rg", "--yes")
    assert_ok(again)
    assert "No managed paths" in again.stdout
    assert repair_snapshot(engine) == before
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(command(engine, "update"))
    assert (engine.bin / "fd").is_symlink()
    assert not (engine.bin / "rg").is_symlink() and not (engine.opt / "rg-1.0").exists()
    assert_ok(engine.private('ms_state_load\nms_member_has fd\nif ms_member_has rg; then exit 91; fi\nms_journal_active\n[[ "$MS_BATCH_PHASE" == settled ]]\n'))


@pytest.mark.parametrize("foreign", [False, True])
def test_repair01_mixed_terminal_and_managed_uninstall_keeps_full_preflight(engine: EngineEnv, foreign: bool) -> None:
    engine.asset("nu", aliases=("nushell",))
    engine.asset("rg")
    assert_ok(command(engine, "install", "nu", "rg", "--yes"))
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    if foreign:
        (engine.bin / "rg").unlink()
        (engine.bin / "rg").write_text("foreign required selector")
    before = repair_snapshot(engine)
    result = command(engine, "uninstall", "nu", "rg", "--yes")
    if foreign:
        assert result.returncode == 1
        assert repair_snapshot(engine) == before
        assert_ok(engine.private('ms_state_load\nms_member_has rg\n'))
    else:
        assert_ok(result)
        assert not (engine.opt / "rg-1.0").exists()
        assert_ok(engine.private('ms_state_load\nms_journal_active\nif ms_member_has nu || ms_member_has rg || ms_row_find item "$MS_BATCH" nu; then exit 91; fi\nms_row_find item "$MS_BATCH" rg\n[[ "${MS_ROWS[MS_INDEX+3]}" == completed ]]\n'))


def test_repair01_live_inactive_release_after_terminal_uninstall_is_removed(engine: EngineEnv) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    root = engine.opt / "rg-0.1"
    write_executable(root / "rg", "#!/bin/sh\nexit 0\n")
    (root / ".remote-ssh-release").write_text("format=1\ntool=rg\nversion=0.1\nlayout=binary\nexecutable=rg\n")
    protected = engine.opt / "rg-personal"
    protected.mkdir()
    (protected / "notes").write_text("foreign remainder")
    result = command(engine, "uninstall", "rg", "--yes")
    assert_ok(result)
    assert not root.exists() and (protected / "notes").read_text() == "foreign remainder"
    before = repair_snapshot(engine)
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    assert repair_snapshot(engine) == before


def test_repair01_terminal_custom_selector_history_does_not_block_explicit_install(engine: EngineEnv) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    custom = engine.bin / "old custom alias"
    custom.symlink_to(engine.opt / "rg-1.0/rg")
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    custom.write_text("foreign custom file")
    before = repair_snapshot(engine)
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    assert repair_snapshot(engine) == before
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert custom.read_text() == "foreign custom file"
    assert (engine.bin / "rg").is_symlink()
