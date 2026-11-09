"""Guard/ownership tests with a mock builtin; native ABI tests are separate."""

from __future__ import annotations

import shlex
import shutil

import pytest
from conftest import assert_ok, run_cmd, write_executable
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
          if [[ "$2" == -a ]]; then
            command builtin enable -a
            [[ "$CASE" != existing ]] || printf 'enable flyline\n'
            return
          fi
          calls+=" $2"
          if [[ "$2" == -f ]]; then
            [[ "$CASE" != load-failure ]] || return 1
            loaded=1; FLYLINE_VERSION=new; export FLYLINE_VERSION
          else loaded=0; unset FLYLINE_VERSION; fi ;;
        flyline)
          calls+=" flyline"
          if [[ "$2" == key && "$3" == bind ]]; then bindings+="|$5"; fi
          if [[ "$2" == key && "$3" == --vim-mode && "${5:-}" == bind ]]; then bindings+="|$7"; fi
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
      atuin|nobind) REMOTE_SSH_HISTORY_BACKEND=atuin; __atuin_initialized=true ;;
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


@pytest.mark.parametrize("hook", ["os", "host"])
@pytest.mark.parametrize("atuin_toggle", ["0", "1"])
def test_late_external_atuin_ownership_through_full_rc(
    repo_dir,
    isolated_env,
    runtime_bash,
    hook,
    atuin_toggle,
):
    root = isolated_env.home / "checkout"
    for name in ("shell", "lib", "bin", "dots"):
        shutil.copytree(repo_dir / name, root / name)
    hook_dir = root / "shell/rc.d" / f"{hook}.d"
    hook_dir.mkdir(exist_ok=True)
    (hook_dir / ("linux.sh" if hook == "os" else "ownership-test.sh")).write_text(
        r"""
        REMOTE_HOOK_VISITS=$(( ${REMOTE_HOOK_VISITS:-0} + 1 ))
        [[ "${__atuin_initialized:-}" != true ]] || return 0
        __atuin_initialized=true
        __atuin_history() { printf external-history; }
        __external_precmd() { :; }
        precmd_functions+=(__external_precmd)
        bind -m vi-insert '"\C-r":"external-owner"'
        """
    )
    write_executable(isolated_env.bin_dir / "uname", "#!/bin/sh\necho Linux\n")
    write_executable(isolated_env.bin_dir / "hostname", "#!/bin/sh\necho ownership-test\n")
    env = isolated_env.env | {
        "TERM": "xterm-256color",
        "REPO": str(root),
        "REMOTE_SSH_ENABLE_FLYLINE": "1",
        "REMOTE_SSH_ENABLE_ATUIN": atuin_toggle,
        "REMOTE_SSH_CONFIG": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
    }
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    calls=
    remote_flyline_library() { printf resolver >> "$HOME/flyline-calls"; printf /fixture/library; }
    function builtin() {
      case "$1:$2" in
        enable:-a) command builtin enable -a ;;
        enable:-f|enable:-d|flyline:*) calls+="|$*" ;;
        *) command builtin "$@" ;;
      esac
    }
    source "$REPO/shell/rc.sh"
    [[ "$__atuin_initialized:$REMOTE_SSH_HISTORY_BACKEND" == true:bash ]] || exit 21
    expected=external
    ((BASH_VERSINFO[0] >= 4)) || expected=bash
    [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == skipped:$expected ]] || exit 22
    [[ -z "$calls" && ! -e "$HOME/flyline-calls" ]] || exit 23
    [[ "$(bind -m vi-insert -s)" == *external-owner* ]] || exit 24
    [[ " ${precmd_functions[*]} " == *' __external_precmd '* ]] || exit 25
    [[ "$(__atuin_history)" == external-history ]] || exit 26
    bind -m vi-insert '"\C-r":"later-user-edit"'
    before="$REMOTE_SSH_HISTORY_BACKEND:$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON"
    REMOTE_SSH_ENABLE_ATUIN=1; REMOTE_SSH_ENABLE_FLYLINE=0
    eval rcrc; eval rcrc
    [[ "$REMOTE_HOOK_VISITS" == 3 ]] || exit 30
    [[ "$REMOTE_SSH_HISTORY_BACKEND:$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == "$before" ]] || exit 27
    [[ "$(bind -m vi-insert -s)" == *later-user-edit* ]] || exit 28
    if [[ "${FRESH:-0}" == 0 ]]; then
      FRESH=1 REMOTE_SSH_ENABLE_ATUIN=0 REMOTE_SSH_ENABLE_FLYLINE=1 "$BASH" --noprofile --norc -ic 'source "$HOME/late-probe.sh"' || exit 29
    fi
    """
    script = isolated_env.home / "late-probe.sh"
    script.write_text(
        "run_late_probe() {\n" + code.replace("exit ", "return ") + "\n}\nrun_late_probe\n"
    )
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")


@pytest.mark.parametrize(
    "entry", ["enabled", "disabled", "function", "alias", "unrelated", "absent"]
)
def test_external_editor_detection_is_read_only(repo_dir, isolated_env, runtime_bash, entry):
    env = isolated_env.env | {
        "TERM": "xterm-256color",
        "REPO": str(repo_dir),
        "ENTRY": entry,
        "REMOTE_SSH_ENABLE_FLYLINE": "1",
    }
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    REMOTE_SSH_HISTORY_BACKEND=bash
    calls=; loaded=0
    case "$ENTRY" in
      function) flyline() { return 99; } ;;
      alias) alias flyline='return 99' ;;
    esac
    FLYLINE_VERSION=stale; FLYLINE_LOAD_DIR=/stale; export FLYLINE_VERSION FLYLINE_LOAD_DIR
    remote_flyline_library() { printf resolve >> "$HOME/resolve"; printf /fixture/library; }
    function builtin() {
      case "$1:$2" in
        type:-t)
          case "$ENTRY" in enabled) echo builtin;; *) command builtin "$@";; esac ;;
        enable:-a)
          command builtin enable -a
          case "$ENTRY" in enabled) echo 'enable flyline';; disabled) echo 'enable -n flyline';; unrelated) echo 'enable -n flyline-extra';; esac ;;
        enable:-f) calls+="load"; loaded=1; FLYLINE_VERSION=new; export FLYLINE_VERSION ;;
        enable:-d) calls+="unload"; loaded=0 ;;
        flyline:*) calls+="settings" ;;
        *) command builtin "$@" ;;
      esac
    }
    remote_flyline_finalize
    if ((BASH_VERSINFO[0] < 4)); then
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == skipped:bash ]] || return 31
    else
      case "$ENTRY" in
        enabled|disabled|function|alias)
          [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == skipped:external ]] || return 32
          [[ -z "$calls" && "$loaded" == 0 && ! -e "$HOME/resolve" ]] || return 33
          [[ "$FLYLINE_VERSION:$FLYLINE_LOAD_DIR" == stale:/stale ]] || return 34 ;;
        unrelated|absent)
          [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON:$loaded" == active:managed:1 ]] || return 35
          [[ "$calls" == load*settings* && -e "$HOME/resolve" ]] || return 36 ;;
      esac
    fi
    """
    script = isolated_env.home / "external-probe.sh"
    script.write_text("probe() {\n" + code + "\n}\nprobe\n")
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")


@pytest.mark.parametrize("variable", ["FLYLINE_LOAD_DIR", "FLYLINE_VERSION"])
@pytest.mark.parametrize(
    "state", ["unset", "exported-unset", "empty", "exported-empty", "value", "exported-value"]
)
@pytest.mark.parametrize("failure", ["load", "settings"])
def test_activation_rollback_restores_variable_attributes(
    repo_dir,
    isolated_env,
    runtime_bash,
    variable,
    state,
    failure,
):
    if runtime_bash == "/bin/bash":
        pytest.skip("Bash 3.2 rejects native activation before variable mutation")
    env = isolated_env.env | {
        "TERM": "xterm-256color",
        "REPO": str(repo_dir),
        "VARIABLE": variable,
        "VARIABLE_STATE": state,
        "FAILURE": failure,
        "REMOTE_SSH_ENABLE_FLYLINE": "1",
    }
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    REMOTE_SSH_HISTORY_BACKEND=bash
    unset FLYLINE_LOAD_DIR FLYLINE_VERSION
    case "$VARIABLE_STATE" in
      exported-unset) export "$VARIABLE" ;;
      empty|exported-empty) printf -v "$VARIABLE" '%s' '' ;;
      value|exported-value) printf -v "$VARIABLE" '%s' ' old "quoted" value \ $ * ' ;;
    esac
    case "$VARIABLE_STATE" in exported-empty|exported-value) export "$VARIABLE";; esac
    before="$(declare -p "$VARIABLE" 2>/dev/null)"; before_exists=$?
    before_env="$(/usr/bin/env | /usr/bin/grep '^FLYLINE_' || :)"
    remote_flyline_library() { printf /fixture/library; }
    loaded=0
    function builtin() {
      case "$1:$2" in
        enable:-a) command builtin enable -a ;;
        enable:-f)
          FLYLINE_LOAD_DIR=changed-dir; export FLYLINE_LOAD_DIR
          FLYLINE_VERSION=changed-version; export FLYLINE_VERSION
          [[ "$FAILURE" != load ]] || return 1
          loaded=1 ;;
        enable:-d) loaded=0; unset FLYLINE_LOAD_DIR FLYLINE_VERSION ;;
        *) command builtin "$@" ;;
      esac
    }
    remote_flyline_settings() { return 1; }
    remote_flyline_finalize
    after="$(declare -p "$VARIABLE" 2>/dev/null)"; after_exists=$?
    after_env="$(/usr/bin/env | /usr/bin/grep '^FLYLINE_' || :)"
    [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON:$loaded" == failed:$FAILURE:0 ]] || return 41
    [[ "$before_exists:$before" == "$after_exists:$after" ]] || { printf 'before=<%s> after=<%s>\n' "$before" "$after"; return 42; }
    [[ "$before_env" == "$after_env" ]] || return 43
    """
    script = isolated_env.home / "rollback-probe.sh"
    script.write_text("probe() {\n" + code + "\n}\nprobe\n")
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")


@pytest.mark.parametrize("unload_fails", [False, True], ids=["active", "unload-failure"])
def test_managed_variable_values_are_kept_when_builtin_remains_loaded(
    repo_dir,
    isolated_env,
    runtime_bash,
    unload_fails,
):
    if runtime_bash == "/bin/bash":
        pytest.skip("Bash 3.2 rejects native activation before variable mutation")
    env = isolated_env.env | {
        "TERM": "xterm-256color",
        "REPO": str(repo_dir),
        "REMOTE_SSH_ENABLE_FLYLINE": "1",
        "UNLOAD_FAILS": "1" if unload_fails else "0",
    }
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    REMOTE_SSH_HISTORY_BACKEND=bash
    FLYLINE_LOAD_DIR=old; FLYLINE_VERSION=old
    export -n FLYLINE_LOAD_DIR FLYLINE_VERSION
    remote_flyline_library() { printf /fixture/library; }
    function builtin() {
      case "$1:$2" in
        enable:-a) command builtin enable -a ;;
        enable:-f) FLYLINE_VERSION=managed-version; export FLYLINE_VERSION ;;
        enable:-d) return 1 ;;
        *) command builtin "$@" ;;
      esac
    }
    remote_flyline_settings() { [[ "$UNLOAD_FAILS" == 0 ]]; }
    remote_flyline_finalize 2> "$HOME/warning"
    [[ "$FLYLINE_LOAD_DIR:$FLYLINE_VERSION" == /fixture:managed-version ]] || return 44
    [[ "$(declare -p FLYLINE_LOAD_DIR)" == 'declare -x '* ]] || return 45
    [[ "$(declare -p FLYLINE_VERSION)" == 'declare -x '* ]] || return 46
    if [[ "$UNLOAD_FAILS" == 1 ]]; then
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == failed:settings ]] || return 47
      [[ "$(< "$HOME/warning")" == *'rollback failed'* ]] || return 48
    else
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON" == active:managed ]] || return 49
      [[ ! -s "$HOME/warning" ]] || return 50
    fi
    """
    script = isolated_env.home / "loaded-probe.sh"
    script.write_text("probe() {\n" + code + "\n}\nprobe\n")
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")


@pytest.mark.parametrize("failure", ["global-cursor", "vim-bind"])
def test_combined_native_setting_failure_rolls_back_and_stops(
    repo_dir,
    isolated_env,
    runtime_bash,
    failure,
):
    env = isolated_env.env | {
        "TERM": "xterm-256color",
        "REPO": str(repo_dir),
        "REMOTE_SSH_ENABLE_FLYLINE": "1",
        "FAILURE": failure,
    }
    code = r"""
    source "$REPO/shell/rc.d/29-flyline.sh"
    REMOTE_SSH_HISTORY_BACKEND=atuin; __atuin_initialized=true
    FLYLINE_LOAD_DIR=' old "directory" '; export -n FLYLINE_LOAD_DIR
    unset FLYLINE_VERSION; export FLYLINE_VERSION
    before_dir="$(declare -p FLYLINE_LOAD_DIR)"
    before_version="$(declare -p FLYLINE_VERSION)"
    remote_flyline_library() { printf /fixture/library; }
    loaded=0; failed_call=0; after_failure=0
    function builtin() {
      case "$1:$2" in
        enable:-a) command builtin enable -a ;;
        enable:-f) loaded=1; FLYLINE_VERSION=managed; export FLYLINE_VERSION ;;
        enable:-d) loaded=0; unset FLYLINE_LOAD_DIR FLYLINE_VERSION ;;
        flyline:*)
          [[ "$failed_call" == 0 ]] || after_failure=1
          if [[ "$FAILURE" == global-cursor && "$2" == --show-animations && "$*" == *'set-cursor --backend terminal'* ]]; then
            failed_call=1; return 1
          fi
          if [[ "$FAILURE" == vim-bind && "$2" == key && "$3" == --vim-mode && "${5:-}" == bind ]]; then
            failed_call=1; return 1
          fi ;;
        *) command builtin "$@" ;;
      esac
    }
    remote_flyline_finalize
    if ((BASH_VERSINFO[0] < 4)); then
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON:$loaded:$failed_call" == skipped:bash:0:0 ]] || return 61
    else
      [[ "$REMOTE_SSH_FLYLINE_STATE:$REMOTE_SSH_FLYLINE_REASON:$loaded:$failed_call:$after_failure" == failed:settings:0:1:0 ]] || return 62
      [[ "$(declare -p FLYLINE_LOAD_DIR)" == "$before_dir" ]] || return 63
      [[ "$(declare -p FLYLINE_VERSION)" == "$before_version" ]] || return 64
    fi
    """
    script = isolated_env.home / "combined-failure.sh"
    script.write_text("probe() {\n" + code + "\n}\nprobe\n")
    with PtyShell(runtime_bash, env) as shell:
        shell.command(f"source {shlex.quote(str(script))}")
