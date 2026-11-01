from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable
from pty_shell import PtyShell

SOURCE_HASH = "60dde7dd731f9963b19f313c9b44870b1b0a6836c38bf22e96134251cc834d5a"


@pytest.fixture
def upstream_env(repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str) -> dict[str, str]:
    source = repo_dir / "dev/tests/fixtures/atuin/v18.14.1/atuin.bash"
    assert 'VERSION="18.14.1"' in (repo_dir / "tools/defs/atuin.sh").read_text()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_HASH
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "sk",
        '#!/bin/sh\n[ -z "$SKIM_CALLS" ] || printf "sk\\n" >> "$SKIM_CALLS"\nexit 0\n',
    )
    write_executable(
        isolated_env.bin_dir / "atuin",
        r"""#!/bin/sh
        printf '%s\n' "$*" >> "$ATUIN_CALLS"
        case "$1" in
          init)
            [ "${FAIL_INIT:-0}" != 1 ] || exit 1
            up=true; ctrl=true
            for arg in "$@"; do
              [ "$arg" != --disable-up-arrow ] || up=false
              [ "$arg" != --disable-ctrl-r ] || ctrl=false
            done
            printf '__atuin_bind_ctrl_r=%s\n__atuin_bind_up_arrow=%s\n' "$ctrl" "$up"
            cat "$ATUIN_SOURCE"
            if [ "${FAIL_AFTER_SOURCE:-0}" = 1 ]; then printf '\nfalse\n'; fi
            ;;
          uuid) printf 'fixture-session\n' ;;
          history)
            if [ "$2" = start ]; then
              id="history-$$"
              printf '%s\n' "$id"
              [ -z "$ATUIN_EVENTS" ] || printf 'start\t%s\t%s\n' "$id" "$*" >> "$ATUIN_EVENTS"
            elif [ "$2" = end ]; then
              for arg in "$@"; do id=$arg; done
              [ -z "$ATUIN_EVENTS" ] || printf 'end\t%s\t%s\n' "$id" "$4" >> "$ATUIN_EVENTS"
              [ "${FAIL_HISTORY_END:-0}" != 1 ] || exit 1
            fi
            ;;
        esac
        """,
    )
    return isolated_env.env | {
        "ATUIN_SOURCE": str(source),
        "ATUIN_CALLS": str(isolated_env.home / "atuin.calls"),
        "HISTFILE": str(isolated_env.home / "user history"),
        "REMOTE_SSH_CONFIG": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
        "REMOTE_SSH_ENABLE_ATUIN": "1",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        "TERM": "xterm-256color",
    }


@pytest.mark.parametrize("mode", ["emacs", "vi"])
@pytest.mark.parametrize("fallback", [False, True])
def test_ctrl_r_uses_selected_backend(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], mode: str, fallback: bool
) -> None:
    env = upstream_env | {
        "REPO": str(repo_dir),
        "REMOTE_SSH_ENABLE_ATUIN": "0" if fallback else "1",
        "SKIM_CALLS": str(Path(upstream_env["HOME"]) / "sk.calls"),
    }
    with PtyShell(runtime_bash, env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(f"set -o {mode}")
        calls = Path(env["SKIM_CALLS"] if fallback else env["ATUIN_CALLS"])
        shell.keypress(
            b"\x12",
            lambda: (
                calls.exists()
                and (
                    fallback or any(x.startswith("search ") for x in calls.read_text().splitlines())
                )
            ),
        )
    if not fallback:
        assert "init bash --disable-up-arrow --disable-ctrl-r --disable-ai" in calls.read_text()


@pytest.mark.parametrize("nobind", [False, True])
def test_only_editable_ctrl_r_changes_and_reload_preserves_user_edits(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], nobind: bool
) -> None:
    script = r"""
    audit_keys() {
      local map
      for map in emacs vi-insert vi-command; do
        bind -m "$map" -p; bind -m "$map" -s
      done | grep -E '^"(\\e\[A|\\eOA|k|/|\\C-r)":'
    }
    for map in emacs vi-insert vi-command; do
      bind -m "$map" '"\e[A":"user-up"'
      bind -m "$map" '"\eOA":"user-up-other"'
    done
    bind -m emacs '"?":self-insert'
    bind -m vi-command '"k":forward-char'
    bind -m vi-command '"/":vi-search'
    bind -m vi-command '"\C-r":vi-redo'
    before="$(audit_keys)"
    . "$REPO/shell/rc.sh"
    after="$(audit_keys)"
    [[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin ]] || exit 10
    [[ "$ATUIN_NOBIND" != 1 || "$after" == "$before" ]] || exit 11
    for map in emacs vi-insert; do bind -m "$map" '"\C-r":"user-later"'; done
    edited="$(audit_keys)"
    REMOTE_SSH_ENABLE_ATUIN=0
    rcrc; rcrc
    [[ "$(audit_keys)" == "$edited" && "$HISTFILE" == '' ]] || exit 12
    [[ "$(bind -m emacs -p)" == *'"?": self-insert'* ]] || exit 20
    [[ "$(bind -m vi-command -p)" == *'"k": forward-char'* ]] || exit 13
    [[ "$(bind -m vi-command -p)" == *'"/": vi-search'* ]] || exit 14
    [[ "$(bind -m vi-command -p)" == *'"\C-r": vi-redo'* ]] || exit 15
    [[ "$(bind -m emacs -s)" == *'"\e[A": "user-up"'* ]] || exit 16
    """
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env | {"REPO": str(repo_dir), "ATUIN_NOBIND": "1" if nobind else ""},
    )
    assert_ok(result)


def test_custom_shell_navigation_binding_survives_actual_keypress(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    marker = Path(upstream_env["HOME"]) / "navigation"
    env = upstream_env | {"REPO": str(repo_dir)}
    with PtyShell(runtime_bash, env) as shell:
        shell.command(
            r"""audit_nav() { echo pressed >> "$HOME/navigation"; }; bind -m vi-command -x '"k":audit_nav'; . "$REPO/shell/rc.sh"; set -o vi"""
        )
        shell.keypress(b"\x1bk", marker.exists)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=0; rcrc")
        marker.unlink()
        shell.keypress(b"\x1bk", marker.exists)


@pytest.mark.parametrize(
    "failure", ["partial", "return", "missing-helper", "binding", "late-binding-no-skim"]
)
def test_failed_initialization_preserves_user_callbacks_keys_and_bind_function(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], failure: str
) -> None:
    atuin = Path(upstream_env["PATH"].split(":")[0]) / "atuin"
    if failure == "late-binding-no-skim":
        (atuin.parent / "sk").unlink()
    script = atuin.read_text().replace(
        'cat "$ATUIN_SOURCE"',
        'cat "$ATUIN_SOURCE"\n'
        + {
            "partial": "printf '\\nfalse\\n'",
            "late-binding-no-skim": "printf '%s\\n' 'atuin-bind() { bind -m emacs '\"'\"'\"\\C-r\":\"attempted\"'\"'\"'; bind -m invalid-keymap '\"'\"'\"x\":forward-char'\"'\"'; }'",
            "return": "printf '\\nreturn 1\\n'",
            "missing-helper": "printf '\\nunset -f __atuin_history\\n'",
            "binding": "printf '%s\\n' 'bind -m invalid-keymap '\"'\"'\"x\":forward-char'\"'\"''",
        }[failure],
    )
    atuin.write_text(script)
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      audit_user() { :; }
      preexec_functions=(audit_user); precmd_functions=(audit_user); BLE_ONLOAD=(audit_user)
      bind() { builtin bind "$@"; }
      saved_bind="$(declare -f bind)"
      bind -m emacs '"?":self-insert'
      audit_ctrl_r() { :; }
      bind -m emacs -x '"\C-r":audit_ctrl_r'
      bind -m vi-command '"k":forward-char'
      bind -m vi-command '"/":vi-search'
      bind -m emacs '"\e[A":"user-up"'
      saved_history="$HISTFILE"
      . "$REPO/shell/rc.sh"
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash && "$HISTFILE" == "$saved_history" ]] || exit 10
      [[ "$(declare -f bind)" == "$saved_bind" ]] || exit 11
      [[ " ${preexec_functions[*]} " != *' __atuin_preexec '* && " ${preexec_functions[*]} " == *' audit_user '* ]] || exit 12
      [[ " ${precmd_functions[*]} " != *' __atuin_precmd '* && " ${precmd_functions[*]} " == *' audit_user '* ]] || exit 13
      [[ "${BLE_ONLOAD[*]}" == audit_user ]] || exit 14
      [[ "$(bind -m vi-command -p)" == *'"k": forward-char'* ]] || exit 15
      [[ "$(bind -m vi-command -p)" == *'"/": vi-search'* ]] || exit 16
      [[ "$(bind -m emacs -s)" == *'"\e[A": "user-up"'* ]] || exit 17
      if [[ "$FAILURE" == late-binding-no-skim ]]; then
        [[ "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" == 0 ]] || exit 18
        [[ "$(bind -m emacs -s)" != *'attempted'* ]] || exit 20
        [[ "$(bind -m emacs -p)" != *'"\C-r":'* ]] || exit 21
      else
        [[ "$REMOTE_SSH_SKIM_HISTORY_BOUND" == 1 ]] || exit 18
      fi
      rcrc; rcrc
      [[ "$(declare -f bind)" == "$saved_bind" ]] || exit 19
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir), "FAILURE": failure},
    )
    assert_ok(result)
    assert (
        sum(
            x.startswith("init ")
            for x in Path(upstream_env["ATUIN_CALLS"]).read_text().splitlines()
        )
        == 1
    )
