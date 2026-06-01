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
    assert "vector" in got
    assert "zellij" in got
    assert "procs" not in got
    assert "eza" not in got
    assert "dust" not in got
    assert "procs" in unsupported
    assert "eza" in unsupported
    assert "dust" in unsupported
    assert "vector" not in unsupported


def test_install_profiles_are_defined(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
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
    assert "quick=rg fd sd bat starship eza zoxide navi atuin" in got
    assert "full=fd rg sd dust fzf bat bottom procs yazi nvim zellij nu starship eza zoxide atuin navi tspin vector" in got


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

    assert "  dots/..." in got
    assert "    Found bundled dotfiles and app configs" in got
    assert "Found dots/starship.toml" not in got


def test_expected_tools_read_write_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        write_expected_tools fd rg
        {
          printf '# comment\n'
          printf '\n'
          printf '  fzf  # inline comment\n'
        } >>"$(expected_tools_file)"
        read_expected_tools
        """,
        env=isolated_env.env,
    )

    assert got == "fd\nrg\nfzf"
    assert (isolated_env.home / ".config" / "remote-ssh" / "expected-tools").is_file()


def test_install_command_saves_selected_expected_tools(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --yes fd rg >/dev/null
        printf 'installed=%s\n' "$(tr '\n' ' ' <"$installed" | sed 's/[[:space:]]$//')"
        printf 'expected=%s\n' "$(grep -v '^#' "$(expected_tools_file)" | tr '\n' ' ' | sed 's/[[:space:]]$//')"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )

    assert "installed=fd rg" in got
    assert "expected=fd rg" in got


def test_install_selected_requires_confirmation(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash_failed(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        remote_ssh_cmd_install_main "$repo" fd rg
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )

    assert "requires confirmation" in got
    assert not installed.exists()
    assert not (isolated_env.home / ".config" / "remote-ssh" / "expected-tools").exists()


def test_install_command_skips_unsupported_tools(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        detect_platform() { printf 'darwin|aarch64\n'; }
        detect_libc() { printf 'any\n'; }
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --yes fd eza
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )
    expected_file = isolated_env.home / ".config" / "remote-ssh" / "expected-tools"

    assert "Skipped unsupported tools:" in got
    assert "eza" in got
    assert installed.read_text(encoding="utf-8").rstrip("\n") == "fd"
    expected = expected_file.read_text(encoding="utf-8")
    assert "fd" in expected
    assert "eza" not in expected.splitlines()


def test_install_without_expected_tools_reports_next_step(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _run_repo_bash_failed(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        remote_ssh_cmd_install_main "$repo"
        """,
        env=isolated_env.env,
    )

    assert "No expected tools config found:" in got
    assert "remote-ssh install --profile quick --yes" in got


def test_install_full_requires_confirmation(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _run_repo_bash_failed(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        remote_ssh_cmd_install_main "$repo" --full
        """,
        env=isolated_env.env,
    )

    assert "requires confirmation" in got


def test_install_full_yes_saves_supported_defaults(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --full --yes >/dev/null
        cat "$installed"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )
    expected = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        current_default_tools
        """,
        env=isolated_env.env,
    )

    assert got == expected


def test_install_profile_quick_yes_saves_supported_profile(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --profile=quick --yes >/dev/null
        printf 'installed=%s\n' "$(tr '\n' ' ' <"$installed" | sed 's/[[:space:]]$//')"
        printf 'expected=%s\n' "$(grep -v '^#' "$(expected_tools_file)" | tr '\n' ' ' | sed 's/[[:space:]]$//')"
        printf 'profile=%s\n' "$(current_install_profile_tools quick | tr '\n' ' ' | sed 's/[[:space:]]$//')"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )

    lines = dict(line.split("=", 1) for line in got.splitlines())
    assert lines["installed"] == lines["profile"]
    assert lines["expected"] == lines["profile"]


def test_install_profile_mini_yes_installs_minimal_tools(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --profile mini --yes >/dev/null
        cat "$installed"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )

    assert got == "rg\nfd\nsd"


def test_install_profile_full_matches_full_alias(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" --profile full --yes >/dev/null
        cat "$installed"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )
    expected = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        current_default_tools
        """,
        env=isolated_env.env,
    )

    assert got == expected


def test_install_profile_rejects_invalid_combinations(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    cases = {
        "unknown": "remote_ssh_cmd_install_main \"$repo\" --profile nope --yes",
        "missing": "remote_ssh_cmd_install_main \"$repo\" --profile --yes",
        "explicit": "remote_ssh_cmd_install_main \"$repo\" --profile quick rg",
        "full": "remote_ssh_cmd_install_main \"$repo\" --full --profile quick",
    }

    for name, command in cases.items():
        got = _run_repo_bash_failed(
            repo_dir,
            f"""
            repo="$1"
            . "$repo/tools/lib/env.sh"
            . "$TOOLS_LIB_DIR/commands.lib.sh"
            remote_ssh_cmd_require_install_libs
            install_check_requirements() {{ :; }}
            {command}
            """,
            env=_install_env(isolated_env),
        )
        assert "remote-ssh install" in got or "Unknown remote-ssh install profile" in got, name


def test_install_expected_tools_does_not_require_confirmation(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    installed = isolated_env.home / "installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        write_expected_tools fd rg
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$installed"; }
        install_shell_dir() { :; }
        install_bin_dir() { :; }
        install_dots_dir() { :; }
        install_print_post_install() { :; }
        remote_ssh_cmd_install_main "$repo" >/dev/null
        cat "$installed"
        """,
        env=_install_env(isolated_env),
        args=[installed],
    )

    assert got == "fd\nrg"


def test_tool_install_does_not_change_expected_tools(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    tool_installed = isolated_env.home / "tool-installed"
    got = _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        tool_installed="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_require_install_libs
        write_expected_tools fd rg
        install_check_requirements() { :; }
        install_tools() { printf '%s\n' "$@" >"$tool_installed"; }
        remote_ssh_cmd_tool_main install fzf >/dev/null
        read_expected_tools
        """,
        env=_install_env(isolated_env),
        args=[tool_installed],
    )

    assert got == "fd\nrg"
