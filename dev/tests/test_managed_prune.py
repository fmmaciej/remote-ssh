from __future__ import annotations

from pathlib import Path

import pytest
from conftest import assert_ok, mark_managed_release
from managed_fixture import EngineEnv
from test_managed_lifecycle import command
from test_managed_public_faults import utility_stub


def inactive(engine: EngineEnv, version: str = "0.5") -> Path:
    root = engine.opt / f"rg-{version}"
    root.mkdir(parents=True)
    mark_managed_release(root, "rg", version)
    return root


def test_prune_completed_unused_release_readonly_bin_and_custom_alias(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    old = (engine.bin / "rg").resolve().parent
    engine.asset("rg", version="2.0")
    assert_ok(command(engine, "install", "rg", "--yes"))
    custom = inactive(engine)
    (engine.bin / "custom\nalias").symlink_to(custom / "rg")
    engine.bin.chmod(0o555)
    try:
        result = command(engine, "prune")
        assert_ok(result)
        assert f"candidate: {old}" in result.stdout and old.exists()
        state = sorted((engine.opt / ".remote-ssh-managed/locations").glob("*/state"))[
            0
        ]
        before = state.read_bytes()
        result = command(engine, "prune", "--apply")
        assert_ok(result)
        assert not old.exists() and custom.exists() and (engine.bin / "rg").exists()
        assert before == state.read_bytes()
    finally:
        engine.bin.chmod(0o755)


@pytest.mark.parametrize("signal", ["KILL", "TERM"])
def test_pending_final_release_survives_prune_and_install_retry(
    engine: EngineEnv, signal: str
) -> None:
    engine.asset("rg")
    stub = utility_stub(
        engine,
        "mv",
        'if [[ "$target" == "$INSTALL_PREFIX/rg-1.0" && ! -e "$HOME/crashed" ]]; then\n "$actual" "$@" || exit $?\n printf once >"$HOME/crashed"\n kill -'
        + signal
        + ' "$PPID"\n exit 0\nfi\n',
    )
    result = command(engine, "install", "rg", "--yes")
    assert result.returncode != 0
    stub.unlink()
    final = engine.opt / "rg-1.0"
    assert final.is_dir() and not (engine.bin / "rg").exists()
    before = sorted((engine.opt / ".remote-ssh-managed/locations").glob("*/state"))[
        0
    ].read_bytes()
    assert_ok(command(engine, "prune", "--apply"))
    assert final.exists()
    assert (
        before
        == sorted((engine.opt / ".remote-ssh-managed/locations").glob("*/state"))[
            0
        ].read_bytes()
    )
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert (engine.bin / "rg").exists()


def test_other_slot_claim_and_corrupt_claim_scan_fail_closed(engine: EngineEnv) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    original = (engine.bin / "rg").resolve().parent
    (engine.bin / "rg").unlink()
    other = engine.bin.parent / "other-bin"
    other.mkdir()
    engine.env["INSTALL_BIN_DIR"] = str(other)
    stale = inactive(engine)
    result = command(engine, "prune", "--apply")
    assert_ok(result)
    assert original.exists() and not stale.exists()
    state = sorted((engine.opt / ".remote-ssh-managed/locations").glob("*/state"))[0]
    state.write_bytes(state.read_bytes() + b"invalid\0")
    stale = inactive(engine)
    result = command(engine, "prune", "--apply")
    assert result.returncode == 1 and stale.exists() and original.exists()


def test_prune_never_uses_receipt_for_missing_payload_delete(engine: EngineEnv) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    root = (engine.bin / "rg").resolve().parent
    (engine.bin / "rg").unlink()
    (root / "rg").unlink()
    assert_ok(command(engine, "prune", "--apply"))
    assert root.exists()


def test_prune_registered_child_fences_reports_after_owner_sigkill(
    engine: EngineEnv,
) -> None:
    import subprocess
    import time

    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    old = inactive(engine)
    entered = engine.assets / "prune-entered"
    release = engine.assets / "prune-release"
    stub = utility_stub(
        engine,
        "rm",
        'if [[ "$1" == -rf && "$target" == "$INSTALL_PREFIX/rg-0.5" ]]; then\n touch "$ASSET_DIR/prune-entered"\n kill -KILL "$PPID"\n for ((n=0;n<300;n++)); do [[ ! -e "$ASSET_DIR/prune-release" ]] || break; sleep 0.05; done\n [[ -e "$ASSET_DIR/prune-release" ]] || exit 88\nfi\n',
    )
    proc = subprocess.Popen(
        [engine.bash, str(engine.repo / "bin/remote-ssh"), "prune", "--apply"],
        env=engine.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 15
        while not entered.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert entered.exists() and old.exists()
        blocked = command(engine, "list", "--installed")
        assert (
            blocked.returncode == 1
            and blocked.stdout == ""
            and "writer active" in blocked.stderr
        )
        blocked_prune = command(engine, "prune", "--apply")
        assert blocked_prune.returncode == 1 and old.exists()
        release.touch()
        proc.communicate(timeout=30)
        assert proc.returncode != 0 and not old.exists()
    finally:
        release.touch()
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=5)
        stub.unlink()
    assert_ok(command(engine, "prune", "--apply"))
    assert_ok(command(engine, "list", "--installed"))
