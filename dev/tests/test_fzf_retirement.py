from __future__ import annotations

import shutil

import pytest
from conftest import (
    assert_failed,
    assert_ok,
    make_external_tool,
    make_managed_tool,
    run_remote_ssh,
    write_expected_tools,
)


@pytest.mark.parametrize("expected", [["fzf", "sk"], ["sk"], None])
def test_fzf_recovery_after_skipped_migration_window(repo_dir, tool_env, runtime_bash, expected):
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    latest = tool_env.home / "latest"
    recovery = tool_env.home / "recovery"
    for checkout in (latest, recovery):
        for directory in ("lib", "tools", "shell", "bin", "dots"):
            shutil.copytree(repo_dir / directory, checkout / directory)
    # Simulate phase 2 only in the disposable latest checkout.
    (latest / "tools/defs/fzf.sh").unlink()
    fzf = make_managed_tool(tool_env, "fzf", "0.67.0")
    skim = make_managed_tool(tool_env, "sk", "5.9.0")
    external = make_external_tool(tool_env, "fzf")
    expected_path = tool_env.config_dir / "remote-ssh/expected-tools"
    if expected is not None:
        write_expected_tools(tool_env, expected)
    config_before = expected_path.read_bytes() if expected_path.exists() else None
    fzf_before, skim_before, external_before = (
        fzf.read_bytes(),
        skim.read_bytes(),
        external.read_bytes(),
    )
    active = tool_env.opt_dir / ".active"
    active.write_text("unrelated path")
    latest_env = tool_env.env | {"REMOTE_ENV_DIR": str(latest)}

    result = run_remote_ssh(latest, ["uninstall", "--yes", "fzf"], env=latest_env)
    assert_failed(result)
    assert "Unknown tool: fzf" in result.stderr
    assert fzf.read_bytes() == fzf_before
    assert (tool_env.bin_dir / "fzf").is_symlink()
    assert (expected_path.read_bytes() if expected_path.exists() else None) == config_before

    if expected and "fzf" in expected:
        report = run_remote_ssh(latest, ["doctor"], env=latest_env)
        assert "fzf retirement" in report.stdout
        assert "pinned recovery checkout" in report.stdout
        assert "after verifying skim: remote-ssh uninstall fzf" not in report.stdout
        assert expected_path.read_bytes() == config_before

    # An inherited REMOTE_ENV_DIR would redirect the recovery CLI to latest.
    result = run_remote_ssh(
        recovery,
        ["uninstall", "--yes", "fzf"],
        env=latest_env | {"REMOTE_ENV_DIR": str(recovery)},
    )
    assert_ok(result)
    assert not fzf.parent.exists() and not (tool_env.bin_dir / "fzf").is_symlink()
    assert skim.read_bytes() == skim_before and (tool_env.bin_dir / "sk").is_symlink()
    assert external.read_bytes() == external_before
    assert active.read_text() == "unrelated path"
    if expected is None:
        assert not expected_path.exists()
    else:
        assert [
            line
            for line in expected_path.read_text().splitlines()
            if line and not line.startswith("#")
        ] == ["sk"]
