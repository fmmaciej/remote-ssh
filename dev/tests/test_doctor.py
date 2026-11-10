from __future__ import annotations

from pathlib import Path

import pytest
from conftest import (
    ToolStateEnv,
    assert_failed,
    assert_ok,
    make_external_tool,
    make_managed_tool,
    run_cmd,
    run_remote_ssh,
    write_executable,
    write_expected_tools,
)


def test_doctor_suggests_explicit_skim_migration(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    expected = write_expected_tools(tool_env, ["rg", "fzf"])
    before = expected.read_bytes()
    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)
    assert "ssh-find sk:      missing-optional" in result.stdout
    assert "remote-ssh tool install sk" in result.stdout
    assert f"add sk to {expected} (replace fzf if migrating)" in result.stdout
    assert expected.read_bytes() == before

    write_executable(tool_env.bin_dir / "sk", "#!/bin/sh\nexit 0\n")
    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)
    assert "ssh-find sk:      ok" in result.stdout
    assert "install skim:" not in result.stdout


def test_remote_ssh_doctor_reports_missing_tools(repo_dir: Path, tool_env: ToolStateEnv) -> None:
    write_expected_tools(tool_env, ["rg"])

    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    output = result.stdout
    assert "remote-ssh doctor" in output
    assert "status: ok" in output
    assert "Repository" in output
    assert "branch:" in output
    assert "commit:" in output
    assert "dirty:" in output
    assert "Shell rc" in output
    assert "shell/rc.sh" in output
    assert "Optional helpers" in output
    assert "ssh-find python3:" in output
    assert "ssh-find ssh:" in output
    assert "ssh-find sk:" in output
    assert "Tool check" in output
    assert "summary: failed" in output
    assert "Next steps" in output
    assert "run: remote-ssh install" in output
    assert "inspect: remote-ssh check --strict" in output


def test_remote_ssh_doctor_reports_path_shadow_hint(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["rg"])
    make_managed_tool(tool_env, "rg", "15.1.0", content="#!/usr/bin/env bash\nprintf managed-rg\n")
    make_external_tool(tool_env, "rg", content="#!/usr/bin/env bash\nprintf external-rg\n")
    env = tool_env.env | {"PATH": f"{tool_env.external_dir}:{tool_env.bin_dir}:/usr/bin:/bin"}

    result = run_remote_ssh(repo_dir, ["doctor"], env=env)

    assert_failed(result)
    assert "status:    path-shadowed" in result.stdout
    assert (
        f"check PATH order: {tool_env.bin_dir} should come before external tool directories"
        in result.stdout
    )
    assert "inspect: remote-ssh check --strict" in result.stdout


def test_remote_ssh_doctor_rejects_mismatched_remote_env_dir(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    other = tool_env.home / "other"
    other.mkdir()
    env = tool_env.env | {"REMOTE_ENV_DIR": str(other)}

    result = run_remote_ssh(repo_dir, ["doctor"], env=env)

    assert_failed(result)
    assert "env status: mismatch" in result.stdout


def test_remote_ssh_doctor_reports_missing_expected_tools_config(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    assert "No expected tools config found:" in result.stdout
    assert "choose tools: remote-ssh install fd rg sk" in result.stdout
    assert "remote-ssh install --profile quick --yes" in result.stdout


def test_remote_ssh_doctor_reports_missing_binary_alias(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    write_expected_tools(tool_env, ["nu"])
    make_managed_tool(tool_env, "nu", "0.112.2")

    result = run_remote_ssh(repo_dir, ["doctor"], env=tool_env.env)

    assert_failed(result)
    assert "alias:     nushell -> [missing] status=missing target=[missing]" in result.stdout
    assert "run: remote-ssh install" in result.stdout
    assert "inspect: remote-ssh check --strict" in result.stdout


def test_doctor_accepts_equivalent_bin_directory(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    make_managed_tool(tool_env, "rg", "15.1.0")
    write_expected_tools(tool_env, ["rg"])
    alias = tool_env.home / "bin alias"
    alias.symlink_to(tool_env.bin_dir, target_is_directory=True)

    result = run_remote_ssh(
        repo_dir, ["doctor"], env=tool_env.env | {"INSTALL_BIN_DIR": str(alias)}
    )

    assert_ok(result)
    assert f"PATH\n  bin:    {alias}\n  status: ok" in result.stdout
    assert "summary: ok" in result.stdout
    assert "path-shadowed" not in result.stdout


@pytest.mark.parametrize(
    "path_form,expected",
    [
        ("physical", True),
        ("symlink", True),
        ("trailing-slash", True),
        ("relative", True),
        ("leading-empty", True),
        ("trailing-empty", True),
        ("middle-empty", True),
        ("empty", True),
        ("other", False),
        ("unset", False),
    ],
)
def test_doctor_path_check_compares_directory_identity(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, path_form: str, expected: bool
) -> None:
    alias = tool_env.home / "bin alias"
    alias.symlink_to(tool_env.bin_dir, target_is_directory=True)
    path_value = {
        "physical": str(tool_env.bin_dir),
        "symlink": str(alias),
        "trailing-slash": str(tool_env.bin_dir) + "/",
        "relative": ".",
        "leading-empty": ":/usr/bin:/bin",
        "trailing-empty": "/usr/bin:/bin:",
        "middle-empty": "/usr/bin::/bin",
        "empty": "",
        "other": str(tool_env.external_dir),
        "unset": "",
    }[path_form]
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        set -euo pipefail
        . "$1/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        INSTALL_BIN_DIR="$2"
        PATH="$3"
        if [[ "$4" == unset ]]; then unset PATH; fi
        if remote_ssh_cmd_doctor_path_contains_install_bin; then
          printf 'present\\n'
        else
          printf 'absent\\n'
        fi
        """,
            "_",
            repo_dir,
            alias,
            path_value,
            path_form,
        ],
        cwd=tool_env.bin_dir,
        env=tool_env.env,
    )

    assert_ok(result)
    assert result.stdout.strip() == ("present" if expected else "absent")


@pytest.mark.parametrize(
    "expected,owned,skim,warn",
    [
        (["fzf"], False, False, True),
        (["fzf", "sk"], True, True, True),
        (["rg"], True, True, True),
        (["rg"], False, True, False),
        (None, True, False, True),
        (None, False, True, False),
        (["sk"], False, True, False),
    ],
)
def test_doctor_fzf_retirement_is_read_only(
    repo_dir, tool_env, runtime_bash, expected, owned, skim, warn
):
    (tool_env.bin_dir / "bash").symlink_to(runtime_bash)
    make_managed_tool(tool_env, "rg", "15.1.0")
    if owned:
        make_managed_tool(tool_env, "fzf", "0.67.0")
    external = make_external_tool(tool_env, "fzf")
    if skim:
        make_managed_tool(tool_env, "sk", "5.9.0")
    if expected is not None:
        write_expected_tools(tool_env, expected)
    env = tool_env.env | {"PATH": f"{tool_env.bin_dir}:{tool_env.external_dir}:/usr/bin:/bin"}

    def snapshot():
        files = {}
        for root in (
            tool_env.config_dir,
            tool_env.opt_dir,
            tool_env.bin_dir,
            tool_env.external_dir,
        ):
            for path in root.rglob("*"):
                if path.is_symlink():
                    files[str(path)] = ("link", str(path.readlink()))
                elif path.is_file():
                    files[str(path)] = ("file", path.read_bytes())
        return files

    before = snapshot()
    result = run_remote_ssh(repo_dir, ["doctor"], env=env)
    assert ("\nfzf retirement\n" in result.stdout) == warn
    if warn:
        assert "status: migration-needed" in result.stdout
        assert "remote-ssh check --strict sk" in result.stdout
        assert "remote-ssh uninstall fzf" in result.stdout
        assert "docs/install.md#migrating-from-fzf-to-skim" in result.stdout
        if expected and "fzf" in expected:
            assert "expected-tools contains fzf" in result.stdout
        if owned:
            assert "managed fzf is installed" in result.stdout
    if expected is not None and (owned or "fzf" not in expected):
        assert_ok(result)
    assert snapshot() == before
    assert external.exists()
