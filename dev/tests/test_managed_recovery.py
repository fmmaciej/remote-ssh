from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from conftest import ToolStateEnv, assert_ok
from test_managed_state import prepare, release, run


@pytest.mark.parametrize("complete", [False, True])
def test_sigkill_install_recovers_actual_success_or_rolls_back_partial_aliases(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, complete: bool
) -> None:
    old = release(tool_env, "rg", "1.0")
    new = release(tool_env, "rg", "2.0")
    for name in ["rg", "rga"]:
        (tool_env.bin_dir / name).symlink_to(old / "bin/rg")
    after = 'ln -sfn "$new/bin/rg" "$MS_BIN/rga"\n' if complete else ""
    setup = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\n'
        "ms_migration_commit\nms_row_add alias rg rga\n"
        'ms_row_add selector rg "$MS_BIN/rga" "$MS_PREFIX/rg-1.0/bin/rg" "$MS_PREFIX/rg-1.0"\n'
        "ms_recovery_gate\nms_journal_begin install install rg\nms_journal_item rg running staging\n"
        'new="$MS_PREFIX/rg-2.0"\n'
        'ms_row_add publication "$MS_BATCH" rg "$MS_PREFIX/.stage-rg" "$new" 2.0 binary bin/rg intended\n'
        'for name in rg rga; do ms_row_add link-intent "$MS_BATCH" rg "$MS_BIN/$name" link "$MS_PREFIX/rg-1.0/bin/rg" "$new/bin/rg" "$new" intended; done\n'
        'ms_state_commit\nln -sfn "$new/bin/rg" "$MS_BIN/rg"\n'
        + after
        + "kill -KILL $$",
    )
    assert setup.returncode == -9
    recovered = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_recovery_gate\n'
        'ms_member_has rg\nms_row_find item "$MS_BATCH" rg\nprintf "%s\\n" "${MS_ROWS[MS_INDEX+3]}"\n'
        'previous="$MS_BATCH"\nif ms_journal_begin install install fd; then exit 92; fi\nms_journal_prepare\nms_journal_begin install install fd\nms_row_find result "$previous" rg\n',
    )
    assert_ok(recovered)
    assert recovered.stdout.strip() == ("completed" if complete else "failed")
    expected = new if complete else old
    assert (tool_env.bin_dir / "rg").readlink() == expected / "bin/rg"
    assert (tool_env.bin_dir / "rga").readlink() == expected / "bin/rg"
    assert old.exists() and new.exists()


@pytest.mark.parametrize(
    "replacement", ["foreign-link", "regular", "missing-member", "marker-link"]
)
def test_unresolved_journal_blocks_every_new_batch_and_retains_membership(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, replacement: str
) -> None:
    root = release(tool_env, "rg")
    selector = tool_env.bin_dir / "rg"
    selector.symlink_to(root / "bin/rg")
    setup = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_migration_commit\n'
        "ms_recovery_gate\nms_journal_begin uninstall uninstall rg\nms_journal_item rg running removing\n"
        'ms_row_add remove-intent "$MS_BATCH" rg link "$MS_BIN/rg" "$MS_PREFIX/rg-1.0/bin/rg" "$MS_PREFIX/rg-1.0" intended required\n'
        'ms_row_add remove-intent "$MS_BATCH" rg release "$MS_PREFIX/rg-1.0" "" "$MS_PREFIX/rg-1.0" intended required\nms_state_commit',
    )
    assert_ok(setup)
    if replacement in {"foreign-link", "regular"}:
        selector.unlink()
        if replacement == "foreign-link":
            selector.symlink_to(tool_env.external_dir / "foreign")
        else:
            selector.write_text("foreign")
    elif replacement == "missing-member":
        (root / "bin/rg").unlink()
    else:
        marker = root / ".remote-ssh-release"
        saved = tool_env.external_dir / "marker"
        marker.rename(saved)
        marker.symlink_to(saved)
    state = tool_env.opt_dir / ".remote-ssh-managed/locations/0/state"
    before = state.read_bytes()
    for command in ["install", "uninstall", "update", "wrapper"]:
        recovered = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\n'
            f"ms_recovery_gate\nms_journal_begin {command} install fd",
        )
        assert recovered.returncode != 0
        assert state.read_bytes() == before
    retained = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_member_has rg\nms_journal_active\nms_row_find item "$MS_BATCH" rg\n[[ "${MS_ROWS[MS_INDEX+3]}" == running ]]',
    )
    assert_ok(retained)
    assert root.exists()


@pytest.mark.parametrize("complete", [False, True])
def test_sigkill_uninstall_finishes_tombstone_before_unrelated_new_install(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, complete: bool
) -> None:
    root = release(tool_env, "rg")
    (tool_env.bin_dir / "rg").symlink_to(root / "bin/rg")
    remove_root = (
        'remote_ssh_release_delete_valid "$MS_PREFIX/rg-1.0" rg\nrm -rf "$MS_PREFIX/rg-1.0"\n'
        if complete
        else ""
    )
    setup = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_migration_commit\n'
        "ms_recovery_gate\nms_journal_begin uninstall uninstall rg\nms_journal_item rg running removing\n"
        'ms_row_add remove-intent "$MS_BATCH" rg link "$MS_BIN/rg" "$MS_PREFIX/rg-1.0/bin/rg" "$MS_PREFIX/rg-1.0" intended required\n'
        'ms_row_add remove-intent "$MS_BATCH" rg release "$MS_PREFIX/rg-1.0" "" "$MS_PREFIX/rg-1.0" intended required\n'
        'ms_state_commit\nrm "$MS_BIN/rg"\n' + remove_root + "kill -KILL $$",
    )
    assert setup.returncode == -9
    recovered = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_recovery_gate\n'
        "if ms_member_has rg; then echo member; else echo removed; fi\n"
        "ms_journal_prepare\nms_journal_begin install install fd\nms_state_load\n"
        "if ms_member_has rg; then echo member; else echo removed; fi\n",
    )
    assert_ok(recovered)
    assert recovered.stdout.splitlines() == (
        ["removed", "removed"] if complete else ["member", "member"]
    )
    assert root.exists() != complete


def test_member_and_each_completed_tool_survive_later_failure(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    prepare(repo_dir, tool_env, runtime_bash)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\nms_recovery_gate\n'
        "ms_journal_begin install install rg fd sk\nms_journal_item rg running staging\nms_journal_complete rg\n"
        "ms_journal_item fd running staging\nms_journal_fail_tail fd\nms_state_load\nms_member_has rg\n"
        "if ms_member_has fd || ms_member_has sk; then exit 91; fi\n"
        'ms_journal_active\nms_row_find item "$MS_BATCH" rg\n[[ "${MS_ROWS[MS_INDEX+3]}" == completed ]]\n'
        'ms_row_find item "$MS_BATCH" fd\n[[ "${MS_ROWS[MS_INDEX+3]}" == failed ]]\n'
        'ms_row_find item "$MS_BATCH" sk\n[[ "${MS_ROWS[MS_INDEX+3]}" == not-run ]]\n',
    )
    assert_ok(result)


def test_failed_atomic_state_rename_preserves_previous_generation(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    state = prepare(repo_dir, tool_env, runtime_bash)
    before = state.read_bytes()
    stub = tool_env.bin_dir / "mv"
    stub.write_text(
        f'#!{runtime_bash}\nfor target in "$@"; do :; done\ncase "$target" in */state) exit 75 ;; esac\nexec /bin/mv "$@"\n'
    )
    stub.chmod(0o755)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\nms_member_set rg 0\nms_state_commit',
    )
    assert result.returncode != 0
    assert state.read_bytes() == before
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_member_has rg\n[[ "$MS_GENERATION" == 1 ]]',
        )
    )


def test_retired_saved_metadata_allows_live_proof_but_missing_payload_never_delete(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    root = release(tool_env, "retired")
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        f"root={shlex.quote(str(root))}\n"
        'if remote_ssh_release_validate "$root" retired; then exit 91; fi\n'
        'remote_ssh_release_delete_valid "$root" retired saved\n'
        'rm "$root/bin/retired"\nremote_ssh_release_identify "$root" retired saved\n'
        'if remote_ssh_release_delete_valid "$root" retired saved; then exit 92; fi\n',
    )
    assert_ok(result)
    assert root.exists()


@pytest.mark.parametrize("complete", [False, True])
def test_new_tool_membership_requires_all_published_aliases_after_crash(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, complete: bool
) -> None:
    root = release(tool_env, "nu")
    alias = 'ln -s "$new/bin/nu" "$MS_BIN/nushell"\n' if complete else ""
    setup = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_migration_commit\n'
        "ms_row_add tool nu binary bin/nu\nms_row_add alias nu nushell\n"
        "ms_recovery_gate\nms_journal_begin install install nu\nms_journal_item nu running staging\n"
        'new="$MS_PREFIX/nu-1.0"\n'
        'ms_row_add publication "$MS_BATCH" nu "$MS_PREFIX/.stage-nu" "$new" 1.0 binary bin/nu intended\n'
        'for name in nu nushell; do ms_row_add link-intent "$MS_BATCH" nu "$MS_BIN/$name" absent "" "$new/bin/nu" "$new" intended; done\n'
        'ms_state_commit\nln -s "$new/bin/nu" "$MS_BIN/nu"\n' + alias + "kill -KILL $$",
    )
    assert setup.returncode == -9
    recovered = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_recovery_gate\n'
        "if ms_member_has nu; then echo member; else echo absent; fi",
    )
    assert_ok(recovered)
    assert recovered.stdout.strip() == ("member" if complete else "absent")
    assert (tool_env.bin_dir / "nu").is_symlink() == complete
    assert root.exists()
