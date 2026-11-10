from __future__ import annotations

import shlex
from pathlib import Path

from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv


def test_private_engine_real_staging_additive_reuse_and_alias_health(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    engine.asset("nu", aliases=("nushell",))
    assert_ok(engine.install("rg", "nu"))
    assert (engine.bin / "nushell").readlink() == engine.opt / "nu-1.0/nu"
    calls = (Path(engine.env["HOME"]) / "curl.calls").read_bytes()
    assert_ok(engine.install("rg", "nu"))
    assert (Path(engine.env["HOME"]) / "curl.calls").read_bytes() == calls
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has nu\n"))
    (engine.bin / "nushell").unlink()
    assert_ok(engine.install("nu"))
    assert (engine.bin / "nushell").is_symlink()
    assert (engine.opt / "nu-1.0").exists()
    assert_ok(engine.private("ms_state_load\nms_member_has rg\nms_member_has nu\n"))


def test_private_bundle_manifest_and_required_data_repaired(engine: EngineEnv) -> None:
    engine.asset("nvim", layout="bundle")
    assert_ok(engine.install("nvim"))
    old = (engine.bin / "nvim").readlink().parent.parent
    (old / "share/nvim/runtime/data").unlink()
    assert_ok(engine.install("nvim"))
    new = (engine.bin / "nvim").readlink().parent.parent
    assert new != old
    assert (new / "share/nvim/runtime/data").read_text() == "required runtime data"
    assert old.exists()


def test_private_engine_checksum_failure_keeps_previous_member_and_not_run_tail(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    assert_ok(engine.install("rg"))
    engine.asset("fd")
    engine.asset("sk")
    with (engine.assets / "fd.tar.gz").open("ab") as output:
        output.write(b"corruption")
    result = engine.install("fd", "sk")
    assert result.returncode != 0
    assert "Checksum mismatch" in result.stderr
    assert "failed: fd" in result.stdout and "not-run: sk" in result.stdout
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nif ms_member_has fd || ms_member_has sk; then exit 91; fi\n"
        )
    )
    assert (engine.bin / "rg").is_symlink()
    assert not (engine.bin / "fd").exists()


def test_private_library_install_uses_qualified_probe_and_absolute_active_link(
    engine: EngineEnv,
) -> None:
    engine.asset("flyline", layout="bash-builtin")
    # This asserts the existing qualification protocol; fake ELF content does
    # not establish native ABI compatibility and no library is loaded here.
    fake_bin = Path(engine.env["PATH"].split(":")[1])
    (fake_bin / "bash").unlink()
    write_executable(
        fake_bin / "bash",
        f'#!{engine.bash}\nif [[ "$*" == *remote-ssh-library-probe* ]]; then printf probe >>"$HOME/probe"; exit 0; fi\nexec {shlex.quote(engine.bash)} "$@"\n',
    )
    assert_ok(engine.install("flyline"))
    assert (
        engine.opt / ".active/flyline"
    ).readlink() == engine.opt / "flyline-1.0/lib/flyline.so"
    assert (Path(engine.env["HOME"]) / "probe").read_text() == "probe"
    assert not (engine.bin / "flyline").exists()


def test_shared_fixture_excludes_synthetic_private_config_without_reading_it(
    engine: EngineEnv,
) -> None:
    from conftest import IsolatedEnv
    from managed_fixture import make_engine

    # The secondary source is a disposable public checkout. Give the tracked
    # whitelist real index metadata BEFORE adding excluded synthetic configs.
    from test_managed_update import git
    git(engine, engine.repo, "init", "-q")
    git(engine, engine.repo, "add", ".")
    paths = [
        engine.repo / "dots/git/user.local",
        engine.repo / "tools/.env",
        engine.repo / "dots/credentials.fixture",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic configuration fixture")
        path.chmod(0)
    base = Path(engine.env["HOME"]) / "sanitized-child"
    home, helpers = base / "home", base / "bin"
    home.mkdir(parents=True)
    helpers.mkdir()
    env = engine.env | {
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_STATE_HOME": str(home / ".state"),
        "PATH": f"{helpers}:/usr/bin:/bin",
    }
    try:
        child = make_engine(engine.repo, IsolatedEnv(home, helpers, env), engine.bash)
        for path in paths:
            assert not (child.repo / path.relative_to(engine.repo)).exists()
        assert (child.repo / "bin/remote-ssh").is_file()
    finally:
        for path in paths:
            path.chmod(0o600)
