from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

DEV_DIR = Path(__file__).resolve().parents[1]
if str(DEV_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_DIR))


@dataclass
class IsolatedEnv:
    home: Path
    bin_dir: Path
    env: dict[str, str]


@dataclass
class ToolStateEnv:
    home: Path
    config_dir: Path
    bin_dir: Path
    opt_dir: Path
    external_dir: Path
    env: dict[str, str]


@pytest.fixture(scope="session")
def repo_dir() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def isolated_env(tmp_path: Path) -> IsolatedEnv:
    home = tmp_path / "home"
    bin_dir = tmp_path / "bin"
    xdg_config_home = home / ".config"
    xdg_state_home = home / ".local" / "state"

    home.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    xdg_config_home.mkdir(parents=True)
    xdg_state_home.mkdir(parents=True)

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(xdg_config_home),
            "XDG_STATE_HOME": str(xdg_state_home),
            "PATH": f"{bin_dir}:/usr/bin:/bin",
        }
    )

    return IsolatedEnv(home=home, bin_dir=bin_dir, env=env)


@pytest.fixture
def tool_env(isolated_env: IsolatedEnv) -> ToolStateEnv:
    config_dir = Path(isolated_env.env["XDG_CONFIG_HOME"])
    opt_dir = isolated_env.home / "opt"
    external_dir = isolated_env.home / "external"

    opt_dir.mkdir()
    external_dir.mkdir()

    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt_dir),
        "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        "PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin",
    }

    return ToolStateEnv(
        home=isolated_env.home,
        config_dir=config_dir,
        bin_dir=isolated_env.bin_dir,
        opt_dir=opt_dir,
        external_dir=external_dir,
        env=env,
    )


def run_cmd(
    args: Sequence[str | Path],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=str(cwd) if cwd is not None else None,
        env=dict(env) if env is not None else None,
        text=True,
        capture_output=True,
        check=False,
    )


def run_remote_ssh(
    repo_dir: Path,
    args: Sequence[str],
    *,
    env: Mapping[str, str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["bash", repo_dir / "bin" / "remote-ssh", *args], cwd=cwd, env=env)


def require_git() -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required")


def require_zsh() -> None:
    if shutil.which("zsh") is None:
        pytest.skip("zsh is required")


def copy_repo_for_git_setup(repo_dir: Path, tmp_path: Path) -> Path:
    repo_copy = tmp_path / "repo"
    shutil.copytree(
        repo_dir,
        repo_copy,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
            "uv.lock",
        ),
    )
    return repo_copy


def run_git_setup(repo_dir: Path, *, env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    return run_remote_ssh(repo_dir, ["git", "setup"], env=env)


def run_ssh_setup(repo_dir: Path, *, env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    return run_remote_ssh(repo_dir, ["ssh", "setup"], env=env)


def run_setup(repo_dir: Path, *, env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    return run_remote_ssh(repo_dir, ["setup"], env=env)


def git_config(
    args: Sequence[str],
    *,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["git", "config", *args], env=env)


def prepare_minimal_remote_tree(repo_dir: Path, root: Path) -> Path:
    remote = root / "remote"
    (remote / "lib").mkdir(parents=True)
    (remote / "bin").mkdir()
    (remote / "shell" / "rc.d").mkdir(parents=True)

    shutil.copy2(repo_dir / "lib" / "guards.sh", remote / "lib" / "guards.sh")
    shutil.copy2(repo_dir / "lib" / "helpers.sh", remote / "lib" / "helpers.sh")
    shutil.copy2(repo_dir / "shell" / "env.sh", remote / "shell" / "env.sh")
    shutil.copy2(repo_dir / "shell" / "aliases.sh", remote / "shell" / "aliases.sh")
    shutil.copy2(repo_dir / "shell" / "rc.sh", remote / "shell" / "rc.sh")
    return remote


def assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def assert_failed(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0, (
        f"expected command to fail\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def init_git_repo(path: Path, *, env: Mapping[str, str]) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["git", "init", "-q"], cwd=path, env=env)
    assert_ok(result)
    return path


def write_git_user_local(
    dots_dir: Path,
    *,
    name: str = "Session User",
    email: str = "session@example.com",
) -> Path:
    path = dots_dir / "git" / "user.local"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f"""
            [user]
                name = {name}
                email = {email}
            """
        ).lstrip(),
        encoding="utf-8",
    )
    return path


def output_of(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_fake_runme_git(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "git",
        r"""
        #!/usr/bin/env bash
        if [[ -n "${RUNME_GIT_LOG:-}" ]]; then
          printf 'git %s\n' "$*" >>"$RUNME_GIT_LOG"
        fi

        if [[ "${1:-}" == "-C" && "${3:-}" == "pull" && "${4:-}" == "--ff-only" ]]; then
          exit 0
        fi

        if [[ "${1:-}" == "-C" && "${3:-}" == "fetch" && "${4:-}" == "--depth" && "${5:-}" == "1" && "${6:-}" == "origin" && -n "${7:-}" ]]; then
          exit 0
        fi

        if [[ "${1:-}" == "-C" && "${3:-}" == "checkout" && "${4:-}" == "--detach" && "${5:-}" == "FETCH_HEAD" ]]; then
          exit 0
        fi

        printf 'unexpected git args: %s\n' "$*" >&2
        exit 99
        """,
    )


def write_fake_update_git(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "git",
        r"""
        #!/usr/bin/env bash
        if [[ "${1:-}" == "-C" ]]; then
          shift 2
        fi

        case "${1:-}" in
          pull)
            exit 0
            ;;
          rev-parse)
            case "${2:-}" in
              --is-inside-work-tree)
                printf 'true\n'
                exit 0
                ;;
              HEAD)
                printf '%s\n' "${FAKE_LOCAL_HEAD:-local-head}"
                exit 0
                ;;
              --abbrev-ref)
                if [[ "${FAKE_NO_UPSTREAM:-0}" == "1" ]]; then
                  exit 1
                fi
                printf '%s\n' "${FAKE_UPSTREAM:-origin/main}"
                exit 0
                ;;
            esac
            ;;
          symbolic-ref)
            printf '%s\n' "${FAKE_BRANCH:-main}"
            exit 0
            ;;
          ls-remote)
            if [[ "${FAKE_LS_REMOTE_FAIL:-0}" == "1" ]]; then
              printf 'network down\n' >&2
              exit 128
            fi
            printf '%s\trefs/heads/main\n' "${FAKE_REMOTE_HEAD:-${FAKE_LOCAL_HEAD:-local-head}}"
            exit 0
            ;;
        esac

        printf 'unexpected git args: %s\n' "$*" >&2
        exit 99
        """,
    )


def write_fake_ssh_add(bin_dir: Path, output: str, exit_code: int = 0) -> None:
    write_executable(
        bin_dir / "ssh-add",
        f"""
        #!/usr/bin/env bash
        printf '%s\\n' {shlex.quote(output)}
        exit {exit_code}
        """,
    )


def write_fake_ssh(bin_dir: Path, output: str, exit_code: int) -> None:
    write_executable(
        bin_dir / "ssh",
        f"""
        #!/usr/bin/env bash
        printf '%s\\n' {shlex.quote(output)} >&2
        exit {exit_code}
        """,
    )


def write_expected_tools(tool_env: ToolStateEnv, tools: Sequence[str]) -> Path:
    path = tool_env.config_dir / "remote-ssh" / "expected-tools"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(tools) + "\n", encoding="utf-8")
    return path


def make_managed_tool(
    tool_env: ToolStateEnv,
    tool: str,
    version: str,
    *,
    binary: str | None = None,
    link_name: str | None = None,
    content: str | None = None,
) -> Path:
    binary_name = binary or tool
    symlink_name = link_name or binary_name
    release_dir = tool_env.opt_dir / f"{tool}-{version}"
    executable = release_dir / binary_name

    write_executable(
        executable,
        content or f"#!/usr/bin/env bash\nprintf {shlex.quote(binary_name)}\n",
    )
    link = tool_env.bin_dir / symlink_name
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(executable)
    return executable


def make_external_tool(
    tool_env: ToolStateEnv,
    name: str,
    *,
    content: str | None = None,
) -> Path:
    executable = tool_env.external_dir / name
    write_executable(
        executable,
        content or f"#!/usr/bin/env bash\nprintf {shlex.quote(name)}\n",
    )
    return executable


def prepare_runme_checkout(install_dir: Path, output_file: Path) -> None:
    install_dir.joinpath(".git").mkdir(parents=True)
    remote_ssh = install_dir / "bin" / "remote-ssh"
    quoted_output = shlex.quote(str(output_file))
    write_executable(
        remote_ssh,
        f"""
        #!/usr/bin/env bash
        printf '%s\\n' "$@" >{quoted_output}
        """,
    )
