from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_ok,
    prepare_runme_checkout,
    run_cmd,
    write_fake_runme_git,
)


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
    assert "pull --ff-only" in git_log.read_text(encoding="utf-8")


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
    assert "checkout --detach FETCH_HEAD" in output
