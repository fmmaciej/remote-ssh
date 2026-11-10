from __future__ import annotations

from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command, snapshot
from test_managed_reports import report_repo


@pytest.mark.parametrize("problem", ["rc", "git", "runtime", "optional", "mismatch"])
def test_merged_check_environment(engine: EngineEnv, problem: str) -> None:
    report_repo(engine)
    if problem == "rc":
        (engine.repo / "shell/rc.sh").write_text("if then\n")
    elif problem == "git":
        (engine.repo / ".git").rename(engine.repo / "synthetic-git-away")
    elif problem == "runtime":
        write_executable(
            Path(engine.env["PATH"].split(":")[1]) / "find", "#!/bin/sh\nexit 8\n"
        )
    elif problem == "optional":
        # Missing optional helpers are informational; the empty managed set is healthy.
        pass
    else:
        other = engine.assets / "other-script"
        other.mkdir()
        result = engine.private(
            '. "$TOOLS_LIB_DIR/commands.lib.sh"\nremote_ssh_cmd_check_main "$REPO_DIR" "$1" "$REPO_DIR"\n',
            str(other),
        )
        assert result.returncode == 1 and "mismatch" in result.stdout
        return
    before = snapshot(engine)
    result = command(engine, "check")
    if problem == "optional":
        assert_ok(result)
    else:
        assert result.returncode == 1
    assert snapshot(engine) == before


@pytest.mark.parametrize("hint", ["legacy", "managed", "external", "none"])
def test_merged_check_fzf_hint_is_readonly_and_informational(
    engine: EngineEnv, hint: str
) -> None:
    report_repo(engine)
    if hint == "legacy":
        path = Path(engine.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
        path.parent.mkdir(parents=True)
        path.write_text("fzf\n")
    elif hint == "managed":
        engine.asset("fzf")
        assert_ok(command(engine, "install", "fzf", "--yes"))
    elif hint == "external":
        write_executable(
            Path(engine.env["PATH"].split(":")[1]) / "fzf", "#!/bin/sh\nexit 0\n"
        )
    before = snapshot(engine)
    result = command(engine, "check")
    assert_ok(result)
    assert ("migration-needed" in result.stdout) == (hint in {"legacy", "managed"})
    assert snapshot(engine) == before
