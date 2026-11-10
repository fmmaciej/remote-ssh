from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd


def _run_repo_bash(
    repo_dir: Path,
    script: str,
    *,
    env: dict[str, str],
    args: list[Path] | None = None,
) -> str:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(script).lstrip(),
            "_",
            repo_dir,
            *(args or []),
        ],
        cwd=repo_dir,
        env=env,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def _run_repo_bash_failed(
    repo_dir: Path,
    script: str,
    *,
    env: dict[str, str],
    args: list[Path] | None = None,
) -> str:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(script).lstrip(),
            "_",
            repo_dir,
            *(args or []),
        ],
        cwd=repo_dir,
        env=env,
    )
    assert_failed(result)
    return result.stdout + result.stderr


def _install_env(isolated_env: IsolatedEnv) -> dict[str, str]:
    return isolated_env.env | {
        "INSTALL_PREFIX": str(isolated_env.home / "opt"),
        "INSTALL_BIN_DIR": str(isolated_env.home / "bin"),
    }


def test_default_tools_are_filtered_by_platform(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        default_tools_for_platform darwin aarch64 any
        """,
        env=isolated_env.env,
    ).splitlines()
    unsupported = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        unsupported_default_tools_for_platform darwin aarch64 any
        """,
        env=isolated_env.env,
    ).splitlines()

    assert "fd" in got
    assert "bottom" in got
    assert "zellij" in got
    assert "procs" not in got
    assert "eza" not in got
    assert "dust" not in got
    assert "vector" not in got
    assert "procs" in unsupported
    assert "eza" in unsupported
    assert "dust" in unsupported
    assert "vector" not in unsupported


def test_install_profiles_are_defined(
    repo_dir: Path, isolated_env: IsolatedEnv
) -> None:
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        for profile in "${INSTALL_PROFILES[@]}"; do
          printf '%s=%s\n' "$profile" "$(install_profile_tools "$profile" | tr '\n' ' ' | sed 's/[[:space:]]$//')"
        done
        """,
        env=isolated_env.env,
    )

    assert "mini=rg fd sd" in got
    assert "quick=rg fd sd bat starship eza zoxide sk navi atuin" in got
    assert (
        "full=fd rg sd dust sk bat bottom procs yazi nvim zellij nu starship eza zoxide atuin navi bssh"
        in got
    )


def test_install_dots_dir_reports_bundled_dotfiles(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(
                """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        install_dots_dir
        """
            ).lstrip(),
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env,
    )
    assert_ok(result)
    got = result.stdout + result.stderr

    expected = [
        "  dots/...",
        "    App configs:",
        "      dots/starship.toml",
        "      dots/tmux.conf",
        "      dots/vimrc",
        "      dots/atuin/config.toml",
        "    Setup templates:",
        "      dots/git/config.base",
        "      dots/git/user.local.example",
        "      dots/ssh/config.example",
        "    Cheatsheets:",
        "      dots/navi/cheats/*.cheat",
    ]
    for line in expected:
        assert line in got
    assert "Found bundled dotfiles and app configs" not in got
    assert "Found dots/starship.toml" not in got
