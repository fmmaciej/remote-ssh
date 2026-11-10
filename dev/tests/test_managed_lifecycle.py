from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok
from managed_fixture import EngineEnv


def command(engine: EngineEnv, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [engine.bash, engine.repo / "bin/remote-ssh", *args],
        env=engine.env,
        text=True,
        input="",
        capture_output=True,
        timeout=120,
    )


def snapshot(engine: EngineEnv) -> dict[str, tuple[str, bytes | str]]:
    result = {}
    for root in [engine.opt, engine.bin]:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            name = str(path)
            if path.is_symlink():
                result[name] = ("link", str(path.readlink()))
            elif path.is_file():
                result[name] = ("file", path.read_bytes())
            else:
                result[name] = ("dir", b"")
    return result


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--yes"],
        ["--bogus"],
        ["--full"],
        ["--skip-unsupported"],
        ["--profile"],
        ["--profile", "mini", "--profile", "mini"],
        ["--profile", "mini", "rg"],
        ["--help", "--bogus"],
        ["--help", "unknown"],
        ["rg", "unknown", "--yes"],
        ["rg"],
    ],
)
def test_public_install_invalid_or_unconfirmed_is_nonmutating(
    engine: EngineEnv, args: list[str]
) -> None:
    engine.asset("rg")
    before = snapshot(engine)
    result = command(engine, "install", *args)
    assert result.returncode == 1, result
    assert snapshot(engine) == before
    assert not (Path(engine.env["HOME"]) / "curl.calls").exists()


def test_public_install_additive_deduplicated_expected_tools_untouched(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    legacy = Path(engine.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    legacy.parent.mkdir()
    legacy.write_text("navi\n")
    assert_ok(command(engine, "install", "--yes", "rg", "rg"))
    assert_ok(command(engine, "install", "nu", "--yes"))
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has nu\n"))
    assert legacy.read_text() == "navi\n"
    assert (engine.bin / "remote-ssh").readlink() == engine.repo / "bin/remote-ssh"
    assert len((Path(engine.env["HOME"]) / "curl.calls").read_text().splitlines()) == 2
    assert_ok(command(engine, "install", "rg", "--yes", "--yes"))
    assert len((Path(engine.env["HOME"]) / "curl.calls").read_text().splitlines()) == 2


def test_public_install_foreign_alias_blocks_whole_selection(engine: EngineEnv) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    engine.bin.mkdir()
    foreign = engine.bin / "nushell"
    foreign.write_text("foreign")
    before = snapshot(engine)
    result = command(engine, "install", "rg", "nu", "--yes")
    assert result.returncode == 1
    assert snapshot(engine) == before
    assert not (Path(engine.env["HOME"]) / "curl.calls").exists()


def test_public_library_and_bundle_installs_use_same_state(engine: EngineEnv) -> None:
    engine.asset("nvim", layout="bundle")
    assert_ok(command(engine, "install", "nvim", "--yes"))
    assert_ok(
        engine.private(
            'ms_state_load\nms_member_has nvim\nms_tool_health nvim "$MS_PREFIX/nvim-1.0"\n'
        )
    )


@pytest.mark.parametrize(
    "answer,success", [("y\n", True), ("n\n", False), ("\n", False), (None, False)]
)
def test_install_terminal_confirmation_and_default_deny(
    engine: EngineEnv, answer: str | None, success: bool
) -> None:
    import os
    import pty

    engine.asset("rg")
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [engine.bash, engine.repo / "bin/remote-ssh", "install", "rg"],
        env=engine.env,
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    os.close(slave)
    try:
        if answer is None:
            os.close(master)
            master = -1
        else:
            os.write(master, answer.encode())
        stdout, stderr = process.communicate(timeout=45)
        assert (process.returncode == 0) == success, (stdout, stderr)
        assert (engine.bin / "rg").is_symlink() == success
        if not success:
            assert not engine.opt.exists() and not engine.bin.exists()
    finally:
        if master >= 0:
            os.close(master)
        if process.poll() is None:
            process.kill()
            process.communicate()


def test_profile_expansion_and_unsupported_selection(engine: EngineEnv) -> None:
    for tool in ["rg", "fd", "sd"]:
        engine.asset(tool)
    definition = engine.repo / "tools/defs/fd.sh"
    definition.write_text(
        definition.read_text().replace("linux:x86_64:gnu", "darwin:x86_64:any")
    )
    result = command(engine, "install", "--profile=mini", "--yes")
    assert_ok(result)
    assert "Skipped unsupported tools" in result.stdout
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nms_member_has sd\nif ms_member_has fd; then exit 91; fi\n"
        )
    )


def test_only_unsupported_selection_is_nonmutating(engine: EngineEnv) -> None:
    engine.asset("rg")
    definition = engine.repo / "tools/defs/rg.sh"
    definition.write_text(
        definition.read_text().replace("linux:x86_64:gnu", "darwin:x86_64:any")
    )
    result = command(engine, "install", "rg", "--yes")
    assert result.returncode == 1
    assert not engine.opt.exists() and not engine.bin.exists()


def test_planned_management_cli_collision_is_rejected_before_any_write(
    engine: EngineEnv,
) -> None:
    engine.asset("rg", aliases=("remote-ssh",))
    result = command(engine, "install", "rg", "--yes")
    assert result.returncode == 1
    assert "conflicts with management CLI" in result.stderr
    assert not engine.opt.exists() and not engine.bin.exists()
    assert not (Path(engine.env["HOME"]) / "curl.calls").exists()
