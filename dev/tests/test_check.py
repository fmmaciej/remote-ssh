from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command
from test_managed_reports import report_repo


@pytest.mark.parametrize(
    "kind",
    [
        "directory-alias",
        "relative",
        "empty",
        "function",
        "missing-path",
        "external-alias",
    ],
)
def test_check_physical_path_and_shadowing(engine: EngineEnv, kind: str) -> None:
    report_repo(engine)
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    env = engine.env.copy()
    cwd = engine.bin
    body = 'exec "$1" "$2" check nu'
    if kind == "directory-alias":
        alias = engine.bin.parent / "bin-alias"
        alias.symlink_to(engine.bin, target_is_directory=True)
        env["INSTALL_BIN_DIR"] = str(alias)
        env["PATH"] = f"{alias}:{env['PATH']}"
    elif kind == "relative":
        env["PATH"] = f"{os.path.relpath(engine.bin, cwd)}:{env['PATH']}"
    elif kind == "empty":
        env["PATH"] = f":{env['PATH']}"
    elif kind == "function":
        body = "nu() { :; }; export -f nu; " + body
    elif kind == "missing-path":
        env["PATH"] = ":".join(env["PATH"].split(":")[1:])
    else:
        (engine.bin / "nushell").unlink()
        write_executable(
            Path(env["PATH"].split(":")[1]) / "nushell", "#!/bin/sh\nexit 0\n"
        )
    result = subprocess.run(
        [
            engine.bash,
            "-c",
            body,
            "_",
            engine.bash,
            str(engine.repo / "bin/remote-ssh"),
        ],
        env=env,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if kind in {"directory-alias", "relative", "empty"}:
        assert_ok(result)
    else:
        assert result.returncode == 1
        assert {
            "function": "path-shadowed",
            "missing-path": "local-not-in-path",
            "external-alias": "external-only",
        }[kind] in result.stdout


def test_check_alias_target_from_another_owned_version_is_broken(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    old = (engine.bin / "nu").resolve()
    engine.asset("nu", version="2.0", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    alias = engine.bin / "nushell"
    alias.unlink()
    alias.symlink_to(old)
    result = command(engine, "check", "nu")
    assert (
        result.returncode == 1
        and "broken" in result.stdout
        and "alias: nushell status=broken" in result.stdout
    )
