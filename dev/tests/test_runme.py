from __future__ import annotations

from pathlib import Path

import pytest
from conftest import (
    IsolatedEnv,
    assert_ok,
    prepare_runme_checkout,
    run_cmd,
    write_executable,
    write_fake_runme_git,
)
from test_install_cli import footer_commands, prepare_cli_install


def runme_install_dir(env: IsolatedEnv) -> Path:
    return env.home / ".local" / "share" / "remote-ssh"


def prepare_runme(env: IsolatedEnv, args_file: Path) -> None:
    write_fake_runme_git(env.bin_dir)
    prepare_runme_checkout(runme_install_dir(env), args_file)


def default_install_args(repo_dir: Path) -> str:
    result = run_cmd(
        [
            "bash",
            "-lc",
            """
            set -euo pipefail
            . "$PWD/tools/lib/env.sh"
            . "$TOOLS_LIB_DIR/install.lib.sh"
            printf '%s\\n' install "${DEFAULT_TOOLS[@]}"
            """,
        ],
        cwd=repo_dir,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def test_runme_uses_default_tool_selection(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(["bash", repo_dir / "runme.sh"], env=isolated_env.env)

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8").rstrip("\n") == default_install_args(repo_dir)


def test_runme_uses_argument_tool_selection(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(["bash", repo_dir / "runme.sh", "fd", "rg"], env=isolated_env.env)

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8") == "install\nfd\nrg\n"


def test_runme_forwards_yes_verbatim(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(["bash", repo_dir / "runme.sh", "--yes"], env=isolated_env.env)

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8") == "install\n--yes\n"


def test_runme_forwards_yes_to_argument_tool_selection(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(
        ["bash", repo_dir / "runme.sh", "--yes", "fd", "rg"],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8") == "install\n--yes\nfd\nrg\n"


def test_runme_forwards_full_install(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(
        ["bash", repo_dir / "runme.sh", "--full", "--yes"],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8") == "install\n--full\n--yes\n"


def test_runme_forwards_profile_install(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    prepare_runme(isolated_env, args_file)

    result = run_cmd(
        ["bash", repo_dir / "runme.sh", "--profile", "quick", "--yes"],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert args_file.read_text(encoding="utf-8") == "install\n--profile\nquick\n--yes\n"


def test_runme_updates_existing_checkout_by_default(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    args_file = isolated_env.home / "args"
    git_log = isolated_env.home / "git.log"
    prepare_runme(isolated_env, args_file)
    env = isolated_env.env | {"RUNME_GIT_LOG": str(git_log)}

    result = run_cmd(["bash", repo_dir / "runme.sh", "fd"], env=env)

    assert_ok(result)
    output = git_log.read_text(encoding="utf-8")
    assert "fetch origin main" in output
    assert "reset --hard origin/main" in output
    assert "ls-files --others --exclude-standard" in output
    assert "pull --ff-only" not in output
    assert "clean" not in output


def test_runme_checks_out_requested_ref(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    args_file = isolated_env.home / "args"
    git_log = isolated_env.home / "git.log"
    prepare_runme(isolated_env, args_file)
    env = isolated_env.env | {
        "REMOTE_SSH_REF": "v1.2.3",
        "RUNME_GIT_LOG": str(git_log),
    }

    result = run_cmd(["bash", repo_dir / "runme.sh", "fd"], env=env)

    assert_ok(result)
    output = git_log.read_text(encoding="utf-8")
    assert "fetch --depth 1 origin v1.2.3" in output
    assert "checkout --force --detach FETCH_HEAD" in output


@pytest.mark.parametrize("step", ["FETCH", "RESET"])
def test_runme_stops_before_install_after_git_failure(
    repo_dir: Path, isolated_env: IsolatedEnv, step: str
) -> None:
    args_file = isolated_env.home / "args"
    log = isolated_env.home / "git.log"
    prepare_runme(isolated_env, args_file)
    result = run_cmd(
        ["bash", repo_dir / "runme.sh", "fd"],
        env=isolated_env.env
        | {
            f"FAKE_{step}_EXIT": "17",
            "RUNME_GIT_LOG": str(log),
        },
    )
    assert result.returncode == 17
    assert not args_file.exists()
    if step == "FETCH":
        assert "reset" not in log.read_text()


@pytest.mark.parametrize("path_present", [False, True])
def test_runme_real_install_then_fresh_ordinary_shell(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, path_present: bool
) -> None:
    # The older fixtures intentionally test forwarding only. This fixture keeps
    # the real dispatcher, install facade, tools and rcfile, replacing Git
    # transport with a local copy and leaving observable fail-fast network stubs.
    c = prepare_cli_install(repo_dir, isolated_env, runtime_bash)
    c.env.pop("INSTALL_BIN_DIR")
    c.bin = c.home / ".local/bin"
    c.bin.mkdir(parents=True)
    (c.bin / "demo").symlink_to(c.home / "opt/demo-1/demo")
    c.env["CANDIDATE_TREE"] = str(c.root)
    c.env["GIT_LOG"] = str(c.home / "git.log")
    if path_present:
        c.env["PATH"] = f"{c.bin}:{c.env['PATH']}"
    write_executable(
        c.transport / "git",
        """#!/bin/sh
printf '%s\n' "$*" >> "$GIT_LOG"
if [ "$1" = clone ]; then
  /bin/cp -R "$CANDIDATE_TREE" "$5" || exit $?
  /bin/mkdir "$5/.git"
  exit $?
fi
if [ "$1" = -C ]; then shift 2; fi
case "$1" in
rev-parse) printf 'origin/main\n';;
fetch|reset|ls-files) :;;
*) exit 98;;
esac
""",
    )
    startup = {p: p.read_bytes() for p in c.home.glob(".*") if p.is_file()}
    for iteration in range(2):
        result = c.shell([runtime_bash, repo_dir / "runme.sh", "--yes", "demo"])
        assert_ok(result)
        installed_tree = c.home / ".local/share/remote-ssh"
        assert c.command.readlink() == installed_tree / "bin/remote-ssh"
        assert c.expected.read_text().splitlines()[-1] == "demo"
        assert c.command.is_symlink()
        assert set(p.name for p in c.bin.iterdir()) == {"demo", "remote-ssh"}
        guide, _, export = footer_commands(result.stdout)
        ordinary = """
set -e
[[ -z ${REMOTE_ENV_DIR+x} && -z ${REMOTE_SHELL_DIR+x} && -z ${PS1+x} ]]
! alias cheats >/dev/null 2>&1
! alias rhelp >/dev/null 2>&1
! declare -F log >/dev/null
! command -v ssh-find >/dev/null
! command -v logrun >/dev/null
"""
        if path_present:
            ordinary += "command -v remote-ssh\nremote-ssh --help\nremote-ssh guide post-install\n"
            assert export is None
        else:
            assert export is not None
            ordinary += "! command -v remote-ssh >/dev/null\n" + guide + "\n"
            ordinary += export + "\ncommand -v remote-ssh\nremote-ssh --help\n"
        fresh = c.shell([runtime_bash, "--noprofile", "--norc", "-c", ordinary])
        assert_ok(fresh)
        assert "Usage: remote-ssh" in fresh.stdout
        assert "Interactive usage" in fresh.stdout
        assert str(c.command) in fresh.stdout
        assert not c.network.exists()
        assert all(p.read_bytes() == before for p, before in startup.items())
        git_log = (c.home / "git.log").read_text()
        if iteration:
            assert "fetch origin main" in git_log
            assert "reset --hard origin/main" in git_log
        else:
            assert "clone --depth 1" in git_log
