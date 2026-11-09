"""Guard/ownership tests with a mock builtin; native ABI tests are separate."""

from __future__ import annotations

import shlex

import pytest
from conftest import assert_ok, run_cmd
from pty_shell import PtyShell


@pytest.mark.parametrize(
    "case",
    [
        "disabled",
        "term",
        "external",
        "existing",
        "ble",
        "missing",
        "load-failure",
        "settings-failure",
        "active",
        "atuin",
        "nobind",
        "skim",
    ],
)
def test_editor_selection_is_once_per_process(repo_dir, isolated_env, runtime_bash, case):
    env = isolated_env.env | {"TERM": "xterm-256color", "REPO": str(repo_dir), "CASE": case}
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    REMOTE_SSH_ENABLE_FLYLINE=1
    REMOTE_SSH_HISTORY_BACKEND=bash
    loaded=0; calls=; bindings=
    function builtin() {
      case "$1" in
        type) if [[ "$CASE" == existing ]]; then echo builtin; else command builtin "$@"; fi ;;
        enable)
          calls+=" $2"
          if [[ "$2" == -f ]]; then
            [[ "$CASE" != load-failure ]] || return 1
            loaded=1; FLYLINE_VERSION=new; export FLYLINE_VERSION
          else loaded=0; unset FLYLINE_VERSION; fi ;;
        flyline)
          calls+=" flyline"
          if [[ "$2" == key && "$3" == bind ]]; then bindings+="|$5"; fi
          [[ "$CASE:$2:$3" != settings-failure:key:--vim-mode ]] ;;
        *) command builtin "$@" ;;
      esac
    }
    remote_flyline_library() { [[ "$CASE" != missing ]] && printf /fixture/libflyline.dylib; }
    case "$CASE" in
      disabled) REMOTE_SSH_ENABLE_FLYLINE=0 ;;
      term) TERM=dumb ;;
      external) REMOTE_SSH_HISTORY_BACKEND=external ;;
      ble) BLE_VERSION=external ;;
      atuin|nobind) REMOTE_SSH_HISTORY_BACKEND=atuin ;;
      skim) __skim_history() { :; } ;;
    esac
    [[ "$CASE" != nobind ]] || ATUIN_NOBIND=1
    FLYLINE_VERSION=inherited; FLYLINE_LOAD_DIR=/inherited
    remote_flyline_finalize
    expected=skipped
    case "$CASE" in
      disabled) expected=disabled ;;
      active|atuin|nobind|skim) expected=active ;;
      load-failure|settings-failure) expected=failed ;;
    esac
    if ((BASH_VERSINFO[0] < 4)); then
      [[ "$CASE" == disabled ]] || expected=skipped
    fi
    [[ "$REMOTE_SSH_FLYLINE_STATE" == "$expected" ]] || exit 10
    if [[ "$expected" == active ]]; then
      [[ "$loaded" == 1 && "$calls" == *' -f'* && "$calls" != *' -d'* ]] || exit 11
      case "$CASE" in
        atuin) [[ "$bindings" == *vimInsertMode* && "$bindings" == *'!vimModeEnabled+editingBufferMode'* ]] || exit 12 ;;
        nobind|active) [[ -z "$bindings" ]] || exit 13 ;;
        skim) [[ "$bindings" == *'runBashCommand(__skim_history)'* ]] || exit 14 ;;
      esac
    elif [[ "$expected" == failed ]]; then
      [[ "$FLYLINE_VERSION:$FLYLINE_LOAD_DIR" == inherited:/inherited && "$loaded" == 0 ]] || exit 15
      [[ "$CASE" != settings-failure || "$calls" == *' -d'* ]] || exit 16
    else
      [[ -z "$calls" ]] || exit 17
    fi
    before="$calls:$bindings:$REMOTE_SSH_FLYLINE_STATE"
    REMOTE_SSH_ENABLE_FLYLINE=0; CASE=active
    source "$REPO/shell/rc.d/29-flyline.sh"
    remote_flyline_finalize
    [[ "$calls:$bindings:$REMOTE_SSH_FLYLINE_STATE" == "$before" ]] || exit 18
    """
    # Run inside a genuine TTY; the mock tests ownership/rollback without loading
    # any library into the default offline pytest process.
    script = isolated_env.home / "probe.sh"
    script.write_text(code)
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")


def test_enabled_without_tty_does_not_resolve_or_load(repo_dir, isolated_env, runtime_bash):
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      source "$REPO/shell/rc.d/29-flyline.sh"
      remote_flyline_library() { exit 99; }
      remote_flyline_finalize
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == skipped:terminal ]]
    """,
        ],
        env=isolated_env.env | {"REPO": str(repo_dir), "REMOTE_SSH_ENABLE_FLYLINE": "1"},
    )
    assert_ok(result)
