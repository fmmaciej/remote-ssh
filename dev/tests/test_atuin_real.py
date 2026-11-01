from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd


def test_real_pinned_cli_suppresses_the_generated_ai_suffix(isolated_env: IsolatedEnv) -> None:
    """Opt in explicitly: generated CLI glue is outside the offline Bash fixture."""
    binary = os.environ.get("REMOTE_SSH_TEST_ATUIN_BIN")
    if not binary:
        pytest.skip("set REMOTE_SSH_TEST_ATUIN_BIN to the local pinned Atuin executable")
    version = run_cmd([binary, "--version"], env=isolated_env.env)
    assert_ok(version)
    assert version.stdout.startswith("atuin 18.14.1 ")
    default = run_cmd([binary, "init", "bash"], env=isolated_env.env)
    assert_ok(default)
    assert "_atuin_ai_question_mark" in default.stdout
    disabled = run_cmd(
        [binary, "init", "bash", "--disable-up-arrow", "--disable-ctrl-r", "--disable-ai"],
        env=isolated_env.env,
    )
    assert_ok(disabled)
    assert "__atuin_bind_ctrl_r=false" in disabled.stdout
    assert "__atuin_bind_up_arrow=false" in disabled.stdout
    assert "_atuin_ai_question_mark" not in disabled.stdout
    assert 'bind -x \'"?"' not in disabled.stdout
    assert Path(binary).is_file()
