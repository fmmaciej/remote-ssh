from __future__ import annotations

from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, require_zsh, run_cmd, write_executable


def _tool_path(isolated_env: IsolatedEnv) -> str:
    return f"{isolated_env.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin"


def _write_fake_shell_init_tool(
    path: Path,
    tool: str,
    bash_export: str,
    zsh_export: str,
) -> None:
    write_executable(
        path,
        f"""
        #!/usr/bin/env bash
        if [[ "${{1:-}}" == "init" && "${{2:-}}" == "bash" ]]; then
          printf 'export {bash_export}\\n'
          exit 0
        fi
        if [[ "${{1:-}}" == "init" && "${{2:-}}" == "zsh" ]]; then
          printf 'export {zsh_export}\\n'
          exit 0
        fi
        printf 'unexpected {tool} args: %s\\n' "$*" >&2
        exit 1
        """,
    )


def test_starship_initializes_for_bash(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    _write_fake_shell_init_tool(
        isolated_env.bin_dir / "starship",
        "starship",
        "REMOTE_SSH_TEST_STARSHIP_SHELL=bash",
        "REMOTE_SSH_TEST_STARSHIP_SHELL=zsh",
    )
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/22-starship.sh"
            printf "shell=%s\n" "${REMOTE_SSH_TEST_STARSHIP_SHELL:-missing}"
            printf "config=%s\n" "${STARSHIP_CONFIG:-missing}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "shell=bash" in lines
    assert f"config={repo_dir}/dots/starship.toml" in lines


def test_starship_initializes_for_zsh(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_zsh()
    _write_fake_shell_init_tool(
        isolated_env.bin_dir / "starship",
        "starship",
        "REMOTE_SSH_TEST_STARSHIP_SHELL=bash",
        "REMOTE_SSH_TEST_STARSHIP_SHELL=zsh",
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "zsh",
            "-i",
            "-c",
            """
            export PATH="$1:$PATH"
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            source "$REPO_DIR/lib/guards.sh"
            source "$REPO_DIR/lib/helpers.sh"
            source "$REPO_DIR/shell/rc.d/22-starship.sh"
            print -r -- "shell=${REMOTE_SSH_TEST_STARSHIP_SHELL:-missing}"
            print -r -- "config=${STARSHIP_CONFIG:-missing}"
            """,
            "_",
            isolated_env.bin_dir,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "shell=zsh" in lines
    assert f"config={repo_dir}/dots/starship.toml" in lines


def test_zoxide_initializes_for_bash(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    _write_fake_shell_init_tool(
        isolated_env.bin_dir / "zoxide",
        "zoxide",
        "REMOTE_SSH_TEST_ZOXIDE_SHELL=bash",
        "REMOTE_SSH_TEST_ZOXIDE_SHELL=zsh",
    )
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/21-zoxide.sh"
            printf "shell=%s\n" "${REMOTE_SSH_TEST_ZOXIDE_SHELL:-missing}"
            printf "z=%s\n" "$(type -t z || true)"
            printf "zi=%s\n" "$(type -t zi || true)"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "shell=bash" in lines
    assert "z=function" in lines
    assert "zi=function" in lines


def test_zoxide_initializes_for_zsh(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_zsh()
    _write_fake_shell_init_tool(
        isolated_env.bin_dir / "zoxide",
        "zoxide",
        "REMOTE_SSH_TEST_ZOXIDE_SHELL=bash",
        "REMOTE_SSH_TEST_ZOXIDE_SHELL=zsh",
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "zsh",
            "-i",
            "-c",
            """
            export PATH="$1:$PATH"
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            source "$REPO_DIR/lib/guards.sh"
            source "$REPO_DIR/lib/helpers.sh"
            source "$REPO_DIR/shell/rc.d/21-zoxide.sh"
            print -r -- "shell=${REMOTE_SSH_TEST_ZOXIDE_SHELL:-missing}"
            if whence -w z >/dev/null 2>&1; then
              print -r -- "z=function"
            else
              print -r -- "z=missing"
            fi
            if whence -w zi >/dev/null 2>&1; then
              print -r -- "zi=function"
            else
              print -r -- "zi=missing"
            fi
            """,
            "_",
            isolated_env.bin_dir,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "shell=zsh" in lines
    assert "z=function" in lines
    assert "zi=function" in lines


def test_atuin_plugin_initializes_for_bash(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "atuin",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
          printf 'export ATUIN_INIT_SHELL=bash\n'
          printf '%s\n' '__atuin_initialized=true; __atuin_preexec() { :; }; __atuin_precmd() { :; }; __atuin_history() { :; }; atuin-bind() { :; }; preexec_functions+=(__atuin_preexec); precmd_functions+=(__atuin_precmd)'
        fi
        """,
    )
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            export bash_preexec_imported=1
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            REMOTE_ENV_DIR="$REPO_DIR"
            . "$REPO_DIR/shell/rc.d/05-bash-preexec.sh"
            . "$REPO_DIR/shell/rc.d/23-atuin.sh"
            printf "%s\n" "${ATUIN_INIT_SHELL:-missing}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "bash"


@pytest.mark.parametrize("cancel", [False, True])
def test_skim_history_preserves_options_and_readline_on_cancel(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, cancel: bool
) -> None:
    write_executable(
        isolated_env.bin_dir / "sk",
        '#!/bin/sh\ncat >"$HISTORY_INPUT"\n[ "$CANCEL" = 0 ] || exit 130\nprintf "echo selected\\n"\n',
    )
    history_input = isolated_env.home / "history.input"
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-c",
            """
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        . "$1/shell/rc.d/20-skim.sh"
            set +o history
            history -c
        history -s 'echo older'
        history -s 'echo newer'
        history -s 'echo older'
        READLINE_LINE='keep this'; READLINE_POINT=3
        __skim_history || true
        printf '%s\n%s\n%s\n' "$READLINE_LINE" "$READLINE_POINT" "$SKIM_DEFAULT_OPTIONS"
        """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "HISTORY_INPUT": str(history_input),
            "CANCEL": str(int(cancel)),
            "SKIM_DEFAULT_OPTIONS": "--height=60% --reverse",
        },
    )
    assert_ok(result)
    assert history_input.read_text().splitlines() == ["echo older", "echo newer"]
    assert result.stdout.splitlines() == [
        "keep this" if cancel else "echo selected",
        "3" if cancel else "13",
        "--height=60% --reverse",
    ]


def test_sk_history_bind_is_fallback_when_atuin_is_missing(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(isolated_env.bin_dir / "sk", "#!/usr/bin/env bash\nexit 0\n")
    bind_log = isolated_env.home / "bind.log"
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "REPO_DIR": str(repo_dir),
        "BIND_LOG": str(bind_log),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            bind() {
              if [[ "${3:-}" == "-x" && "${4:-}" == *"__skim_history"* ]]; then
                printf "%s\n" "$4" >> "$BIND_LOG"
              fi
              return 0
            }
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/20-skim.sh"
            REMOTE_DOTS_DIR="$REPO_DIR/dots"
            . "$REPO_DIR/shell/rc.d/23-atuin.sh"
            if [[ -s "$BIND_LOG" ]]; then
              printf bound
            else
              printf missing
            fi
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout == "bound"


def test_sk_history_bind_is_skipped_when_atuin_exists(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(isolated_env.bin_dir / "sk", "#!/usr/bin/env bash\nexit 0\n")
    write_executable(isolated_env.bin_dir / "atuin", "#!/usr/bin/env bash\nexit 0\n")
    bind_log = isolated_env.home / "bind.log"
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "REPO_DIR": str(repo_dir),
        "BIND_LOG": str(bind_log),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            bind() {
              if [[ "${3:-}" == "-x" && "${4:-}" == *"__skim_history"* ]]; then
                printf "%s\n" "$4" >> "$BIND_LOG"
              fi
              return 0
            }
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/20-skim.sh"
            if [[ -s "$BIND_LOG" ]]; then
              printf bound
            else
              printf skipped
            fi
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout == "skipped"


def _write_auto_import_atuin(path: Path) -> None:
    write_executable(
        path,
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "import" && "${2:-}" == "auto" ]]; then
          printf 'import auto\n' >> "$ATUIN_TEST_LOG"
          exit "${IMPORT_STATUS:-0}"
        fi
        if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
          printf 'export REMOTE_SSH_TEST_ATUIN_BASH_INIT=1\n'
          printf '%s\n' '__atuin_initialized=true; __atuin_preexec() { :; }; __atuin_precmd() { :; }; __atuin_history() { :; }; atuin-bind() { :; }; preexec_functions+=(__atuin_preexec); precmd_functions+=(__atuin_precmd)'
          exit 0
        fi
        exit 0
        """,
    )


def test_atuin_auto_import_runs_once_when_marker_is_missing(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    _write_auto_import_atuin(isolated_env.bin_dir / "atuin")
    import_log = isolated_env.home / "import.log"
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "ATUIN_TEST_LOG": str(import_log),
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            export bash_preexec_imported=1
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            REMOTE_ENV_DIR="$REPO_DIR"
            . "$REPO_DIR/shell/rc.d/05-bash-preexec.sh"
            . "$REPO_DIR/shell/rc.d/23-atuin.sh"
            printf "log=%s\n" "$(cat "$ATUIN_TEST_LOG")"
            printf "marker=%s\n" "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done"
            printf "marked=%s\n" "$([[ -f "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done" ]] && printf 1 || printf 0)"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "log=import auto" in lines
    assert "marked=1" in lines


def test_atuin_auto_import_is_skipped_when_marker_exists(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    _write_auto_import_atuin(isolated_env.bin_dir / "atuin")
    marker = Path(isolated_env.env["XDG_STATE_HOME"]) / "remote-ssh" / "atuin-import-auto.done"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    import_log = isolated_env.home / "import.log"
    env = isolated_env.env | {
        "PATH": _tool_path(isolated_env),
        "ATUIN_TEST_LOG": str(import_log),
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            export REMOTE_DOTS_DIR="$REPO_DIR/dots"
            export bash_preexec_imported=1
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            REMOTE_ENV_DIR="$REPO_DIR"
            . "$REPO_DIR/shell/rc.d/05-bash-preexec.sh"
            . "$REPO_DIR/shell/rc.d/23-atuin.sh"
            printf "logged=%s\n" "$([[ -f "$ATUIN_TEST_LOG" ]] && printf 1 || printf 0)"
            printf "marked=%s\n" "$([[ -f "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done" ]] && printf 1 || printf 0)"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "logged=0" in lines
    assert "marked=1" in lines


def test_bash_preexec_loads_in_rc_flow(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = isolated_env.env | {
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            . "$REPO_DIR/shell/rc.sh"
            printf "%s\n" "${bash_preexec_imported:-missing}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "missing"


def test_atuin_init_sets_bash_config_and_runs_init(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "atuin",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
          cat <<'SCRIPT'
        export REMOTE_SSH_TEST_ATUIN_BASH_INIT=1
        __atuin_initialized=true; __atuin_preexec() { :; }; __atuin_precmd() { :; }; __atuin_history() { :; }; atuin-bind() { :; }; preexec_functions+=(__atuin_preexec); precmd_functions+=(__atuin_precmd)
        SCRIPT
          exit 0
        fi
        exit 1
        """,
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REMOTE_SSH_REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            """
            export REMOTE_DOTS_DIR="$REMOTE_SSH_REPO_DIR/dots"
            export bash_preexec_imported=1
            REMOTE_ENV_DIR="$REMOTE_SSH_REPO_DIR"
            source "$REMOTE_SSH_REPO_DIR/shell/rc.d/05-bash-preexec.sh"
            source "$REMOTE_SSH_REPO_DIR/shell/rc.d/23-atuin.sh"
            printf "init=%s\n" "${REMOTE_SSH_TEST_ATUIN_BASH_INIT:-0}"
            printf "config=%s\n" "${ATUIN_CONFIG_DIR:-}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "init=1" in lines
    assert f"config={repo_dir}/dots/atuin" in lines


def test_atuin_init_sets_zsh_config_and_runs_init(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_zsh()
    write_executable(
        isolated_env.bin_dir / "atuin",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
          cat <<'SCRIPT'
        export REMOTE_SSH_TEST_ATUIN_ZSH_INIT=1
        SCRIPT
          exit 0
        fi
        exit 1
        """,
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REMOTE_SSH_REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "zsh",
            "-i",
            "-c",
            """
            export PATH="$1:$PATH"
            export REMOTE_DOTS_DIR="$REMOTE_SSH_REPO_DIR/dots"
            REMOTE_ENV_DIR="$REMOTE_SSH_REPO_DIR"
            source "$REMOTE_SSH_REPO_DIR/shell/rc.d/05-bash-preexec.sh"
            source "$REMOTE_SSH_REPO_DIR/shell/rc.d/23-atuin.sh"
            print -r -- "init=${REMOTE_SSH_TEST_ATUIN_ZSH_INIT:-0}"
            print -r -- "config=${ATUIN_CONFIG_DIR:-}"
            """,
            "_",
            isolated_env.bin_dir,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "init=1" in lines
    assert f"config={repo_dir}/dots/atuin" in lines


@pytest.mark.parametrize("disabled", [False, True])
def test_import_failure_retries_only_in_new_shell(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, disabled: bool
) -> None:
    atuin = isolated_env.bin_dir / "atuin"
    _write_auto_import_atuin(atuin)
    log = isolated_env.home / "import.log"
    env = isolated_env.env | {
        "REPO": str(repo_dir),
        "ATUIN_TEST_LOG": str(log),
        "REMOTE_SSH_CONFIG": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0" if disabled else "1",
    }
    command = '. "$REPO/shell/rc.sh"\nrcrc\nrcrc'
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", command], env=env | {"IMPORT_STATUS": "1"}
    )
    assert_ok(result)
    marker = Path(env["XDG_STATE_HOME"]) / "remote-ssh/atuin-import-auto.done"
    assert not marker.exists()
    assert log.read_text().splitlines() == ["import auto"] if not disabled else not log.exists()
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", command], env=env | {"IMPORT_STATUS": "0"}
    )
    assert_ok(result)
    assert marker.exists() == (not disabled)
    if not disabled:
        assert log.read_text().splitlines() == ["import auto", "import auto"]


def test_bundled_atuin_is_local_by_default(repo_dir: Path) -> None:
    config = (repo_dir / "dots/atuin/config.toml").read_text()
    assert "auto_sync = false" in config
    assert "update_check = false" in config
    assert "enter_accept = false" in config
    assert "sync_frequency" not in config
    assert "shell_up_key_binding" not in config
