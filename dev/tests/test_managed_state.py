from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest
from conftest import ToolStateEnv, assert_ok


def release(
    env: ToolStateEnv, tool: str, version: str = "1.0", layout: str = "binary"
) -> Path:
    root = env.opt_dir / f"{tool}-{version}"
    member = f"lib/{tool}.so" if layout == "bash-builtin" else f"bin/{tool}"
    payload = root / member
    payload.parent.mkdir(parents=True)
    payload.write_text(
        "#!/bin/sh\nexit 91\n"
    )  # must never be executed by reports/migration
    payload.chmod(0o755 if layout != "bash-builtin" else 0o644)
    fmt, key = (2, "library") if layout == "bash-builtin" else (1, "executable")
    (root / ".remote-ssh-release").write_text(
        f"format={fmt}\ntool={tool}\nversion={version}\nlayout={layout}\n{key}={member}\n"
    )
    return root


def script(repo: Path, body: str) -> str:
    return (
        f"set -eu\n. {shlex.quote(str(repo / 'tools/lib/env.sh'))}\n"
        '. "$TOOLS_LIB_DIR/managed.lib.sh"\n' + body + "\n"
    )


def run(
    repo: Path, env: ToolStateEnv, bash: str, body: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [bash, "-c", script(repo, body)], env=env.env, text=True, capture_output=True
    )


def prepare(repo: Path, env: ToolStateEnv, bash: str) -> Path:
    result = run(
        repo,
        env,
        bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\n'
        "ms_row_add tool rg binary bin/rg\nms_member_set rg 1\nMS_ADOPTED=1\nms_state_commit\n",
    )
    assert_ok(result)
    return env.opt_dir / ".remote-ssh-managed/locations/0/state"


@pytest.mark.parametrize(
    "layout,tool", [("binary", "rg"), ("bundle", "nvim"), ("bash-builtin", "flyline")]
)
@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "leaf-link",
        "dangling",
        "leaf-dir",
        "parent-link",
        "missing-parent",
        "marker-link",
    ],
)
def test_separate_identity_repair_and_deletion_proofs(
    repo_dir: Path,
    tool_env: ToolStateEnv,
    runtime_bash: str,
    layout: str,
    tool: str,
    damage: str,
) -> None:
    root = release(tool_env, tool, layout=layout)
    member = f"lib/{tool}.so" if layout == "bash-builtin" else f"bin/{tool}"
    payload = root / member
    selector_dir = (
        tool_env.opt_dir / ".active" if layout == "bash-builtin" else tool_env.bin_dir
    )
    selector_dir.mkdir(exist_ok=True)
    link = selector_dir / tool
    link.symlink_to(payload)
    if damage == "marker-link":
        marker = root / ".remote-ssh-release"
        external = tool_env.external_dir / "marker"
        marker.rename(external)
        marker.symlink_to(external)
    elif damage in {"parent-link", "missing-parent"}:
        payload.unlink()
        payload.parent.rmdir()
        if damage == "parent-link":
            # Even a symlink resolving inside the same release is forbidden.
            (root / "real").mkdir()
            payload.parent.symlink_to(root / "real")
    else:
        payload.unlink()
        if damage in {"leaf-link", "dangling"}:
            external = tool_env.external_dir / "file"
            if damage == "leaf-link":
                external.write_text("foreign")
            payload.symlink_to(external)
        elif damage == "leaf-dir":
            payload.mkdir()
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        f"root={shlex.quote(str(root))}\nlink={shlex.quote(str(link))}\n"
        f'if remote_ssh_release_identify "$root" {tool}; then echo A; fi\n'
        f'if remote_ssh_selector_repair_valid "$link" "$root" {tool} 1.0 {layout} {member} {shlex.quote(str(payload))}; then echo B; fi\n'
        f'if remote_ssh_release_delete_valid "$root" {tool}; then echo C; fi\ntrue',
    )
    assert_ok(result)
    assert result.stdout.splitlines() == (
        [] if damage == "marker-link" else ["A", "B"] if damage == "missing" else ["A"]
    )
    assert root.exists()


def test_adoption_covers_alias_only_old_binary_bundle_and_library(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    old = release(tool_env, "rg", "0.1")
    nu = release(tool_env, "nu")
    bundle = release(tool_env, "nvim", layout="bundle")
    library = release(tool_env, "flyline", layout="bash-builtin")
    release(tool_env, "fd", "0.1")  # inactive must not become a member
    (tool_env.bin_dir / "rg").symlink_to(old / "bin/rg")
    (tool_env.bin_dir / "nushell").symlink_to(nu / "bin/nu")
    (tool_env.bin_dir / "nvim").symlink_to(bundle / "bin/nvim")
    (tool_env.opt_dir / ".active").mkdir()
    (tool_env.opt_dir / ".active/flyline").symlink_to(library / "lib/flyline.so")
    expected = tool_env.config_dir / "remote-ssh/expected-tools"
    expected.parent.mkdir()
    expected.write_text("navi\nfzf\n")
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        "ms_state_load\nms_migration_preview\n"
        'for t in rg nu nvim flyline; do ms_member_has "$t"; done\n'
        "if ms_member_has fd || ms_member_has navi || ms_member_has fzf; then exit 92; fi\n"
        '[[ ! -e "$MS_ROOT" ]]\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\n'
        'ms_migration_commit\nms_state_load\n[[ "$MS_ADOPTED" == 1 ]]\n'
        'for t in rg nu nvim flyline; do ms_member_has "$t"; done\n'
        # Missing payload remains a member after an independent reload.
        f"rm {shlex.quote(str(old / 'bin/rg'))}\nms_state_load\nms_member_has rg\n"
        "ms_row_find required nvim share/nvim/runtime || ms_row_add required nvim share/nvim/runtime dir\n"
        'if ms_tool_health nvim "$MS_PREFIX/nvim-1.0"; then exit 93; fi\n',
    )
    assert_ok(result)
    assert expected.read_text() == "navi\nfzf\n"


@pytest.mark.parametrize(
    "corrupt",
    [
        "truncated",
        "extra",
        "duplicate",
        "foreign-pair",
        "symlink",
        "mode",
        "missing",
        "unknown-record",
    ],
)
def test_corrupt_state_never_becomes_an_empty_set(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, corrupt: str
) -> None:
    state = prepare(repo_dir, tool_env, runtime_bash)
    data = state.read_bytes()
    if corrupt == "truncated":
        state.write_bytes(data[:-1])
    elif corrupt == "extra":
        state.write_bytes(data + b"x")
    elif corrupt == "duplicate":
        fields = data.split(b"\0")
        fields[7] = b"3"
        state.write_bytes(b"\0".join(fields[:-1] + [b"member", b"1", b"rg", b""]))
    elif corrupt == "foreign-pair":
        fields = data.split(b"\0")
        fields[2] = str(tool_env.external_dir).encode()
        state.write_bytes(b"\0".join(fields))
    elif corrupt == "symlink":
        outside = tool_env.external_dir / "record"
        state.rename(outside)
        state.symlink_to(outside)
    elif corrupt == "mode":
        state.chmod(0o644)
    elif corrupt == "missing":
        state.unlink()
    elif corrupt == "unknown-record":
        state.write_bytes(data.replace(b"member\0", b"invoke\0"))
    before = state.read_bytes() if state.exists() else None
    result = run(repo_dir, tool_env, runtime_bash, "ms_state_load")
    assert result.returncode != 0
    assert (state.read_bytes() if state.exists() else None) == before


def test_physical_pair_and_newline_paths_survive_strict_nul_roundtrip(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    prefix = tool_env.home / "prefix | with\nnewline"
    prefix.mkdir()
    alias = tool_env.home / "prefix-alias"
    alias.symlink_to(prefix)
    tool_env.env["INSTALL_PREFIX"] = str(alias)
    first = run(
        repo_dir,
        tool_env,
        runtime_bash,
        "ms_state_load\nms_lock_acquire \"$MS_PREFIX\"\nms_row_add tool nu binary nu\nms_row_add alias nu $'line\\nname|x'\nms_member_set nu 1\nMS_ADOPTED=1\nms_state_commit",
    )
    assert_ok(first)
    tool_env.env["INSTALL_PREFIX"] = str(prefix)
    tool_env.env["XDG_CONFIG_HOME"] = str(tool_env.external_dir)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        "ms_state_load\nms_member_has nu\nms_row_find alias nu $'line\\nname|x'\n[[ \"$MS_GENERATION\" == 1 ]]",
    )
    assert_ok(result)


def test_two_bin_pairs_have_separate_membership_and_complete_cross_slot_claims(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    root = release(tool_env, "rg")
    first = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\nms_row_add tool rg binary bin/rg\nms_member_set rg 1\nremote_ssh_release_validate "$MS_PREFIX/rg-1.0"\nms_release_save\nms_state_commit',
    )
    assert_ok(first)
    second_bin = tool_env.home / "second bin"
    second_bin.mkdir()
    tool_env.env["INSTALL_BIN_DIR"] = str(second_bin)
    second = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\n[[ -z "$MS_SLOT" ]]\nif ms_member_has rg; then exit 91; fi\nms_lock_acquire "$MS_PREFIX"\nms_row_add tool fd binary fd\nms_member_set fd 1\nms_state_commit\nms_claims_collect\nms_claimed_path "$MS_PREFIX/rg-1.0"\nms_member_has fd\nif ms_member_has rg; then exit 92; fi',
    )
    assert_ok(second)
    assert root.exists()


@pytest.mark.parametrize("producer", ["partial", "readlink"])
def test_inventory_io_failure_aborts_adoption_without_writes(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, producer: str
) -> None:
    root = release(tool_env, "rg")
    (tool_env.bin_dir / "rg").symlink_to(root / "bin/rg")
    stub = (
        'find() { command find "$@"; return 72; }\n'
        if producer == "partial"
        else "readlink() { return 73; }\n"
    )
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        "ms_state_load\n" + stub + "ms_migration_preview",
    )
    assert result.returncode != 0
    assert not (tool_env.opt_dir / ".remote-ssh-managed").exists()


def test_pending_final_release_claim_survives_dead_writer_and_other_slot(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    prepare(repo_dir, tool_env, runtime_bash)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\nms_recovery_gate\nms_journal_begin install install rg\nms_row_add publication "$MS_BATCH" rg "$MS_PREFIX/.stage-rg" "$MS_PREFIX/rg-2.0" 2.0 binary bin/rg intended\nms_state_commit',
    )
    assert_ok(result)
    other = tool_env.home / "other-bin"
    other.mkdir()
    tool_env.env["INSTALL_BIN_DIR"] = str(other)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nms_claims_collect\nms_claimed_path "$MS_PREFIX/rg-2.0"\nms_claimed_path "$MS_PREFIX/.stage-rg"\n'
        '[[ "${#MS_FOREIGN_CLAIM_PATHS[@]}" == 2 ]]',
    )
    assert_ok(result)


def test_readonly_report_has_no_initialization_and_detects_writer(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            "ms_report_begin\nms_inventory_live\nms_report_end",
        )
    )
    assert list(tool_env.opt_dir.iterdir()) == []
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX"\nif ms_report_begin; then exit 91; fi',
        )
    )


def test_prefix_state_does_not_require_writable_parent_and_readonly_bin(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    parent = tool_env.home / "readonly-parent"
    prefix = parent / "prefix"
    prefix.mkdir(parents=True)
    tool_env.env["INSTALL_PREFIX"] = str(prefix)
    parent.chmod(0o555)
    tool_env.bin_dir.chmod(0o555)
    try:
        result = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX"\n'
            "ms_row_add tool rg binary rg\nms_member_set rg 1\nms_state_commit\n"
            "ms_lock_release_all\nms_state_load\nms_member_has rg\n",
        )
        assert_ok(result)
        assert not (parent / ".remote-ssh-lock").exists()
        assert not (tool_env.bin_dir / ".remote-ssh-lock").exists()
    finally:
        parent.chmod(0o755)
        tool_env.bin_dir.chmod(0o755)


def test_duplicate_slot_and_corrupt_other_slot_block_reports_and_claims(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    state = prepare(repo_dir, tool_env, runtime_bash)
    duplicate = state.parent.parent / "1"
    duplicate.mkdir(mode=0o700)
    copied = duplicate / "state"
    copied.write_bytes(state.read_bytes())
    copied.chmod(0o600)
    for body in ["ms_state_load", "ms_pair_resolve\nms_state_reset\nms_claims_collect"]:
        assert run(repo_dir, tool_env, runtime_bash, body).returncode != 0
    copied.write_bytes(b"corrupt\0")
    assert run(repo_dir, tool_env, runtime_bash, "ms_state_load").returncode != 0


def test_report_generation_fence_rejects_changed_state(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    prepare(repo_dir, tool_env, runtime_bash)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_report_begin\nms_lock_acquire "$MS_PREFIX"\nms_state_commit\nms_lock_release_all\nms_report_end',
    )
    assert result.returncode != 0
    assert "retry report" in result.stderr


def test_prune_claims_keep_pending_and_other_pairs_but_allow_current_inactive(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    release(tool_env, "rg")
    result = run(repo_dir, tool_env, runtime_bash,
        'ms_state_load\nms_lock_acquire "$MS_PREFIX"\n'
        'ms_row_add tool rg binary bin/rg\nremote_ssh_release_validate "$MS_PREFIX/rg-1.0" rg\n'
        'ms_release_save\nms_state_commit\nms_claims_collect prune\n'
        'if ms_claimed_path "$MS_PREFIX/rg-1.0"; then exit 91; fi\n')
    assert_ok(result)
    other = tool_env.home / "other-bin"
    other.mkdir()
    tool_env.env["INSTALL_BIN_DIR"] = str(other)
    result = run(repo_dir, tool_env, runtime_bash,
        'ms_state_load\nms_claims_collect prune\nms_claimed_path "$MS_PREFIX/rg-1.0"\n'
        '[[ "${MS_FOREIGN_CLAIM_PATHS[0]}" == "$MS_PREFIX/rg-1.0" ]]')
    assert_ok(result)
