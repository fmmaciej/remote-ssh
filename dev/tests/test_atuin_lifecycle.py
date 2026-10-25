from __future__ import annotations

import hashlib
import os
import pty
import select
import shlex
import signal
import subprocess
import time
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable

SOURCE_HASH = "60dde7dd731f9963b19f313c9b44870b1b0a6836c38bf22e96134251cc834d5a"


@pytest.fixture
def upstream_env(repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str) -> dict[str, str]:
    source = repo_dir / "dev/tests/fixtures/atuin/v18.14.1/atuin.bash"
    assert 'VERSION="18.14.1"' in (repo_dir / "tools/defs/atuin.sh").read_text()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_HASH
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "fzf",
        '#!/bin/sh\n[ -z "$FZF_CALLS" ] || printf "fzf\\n" >> "$FZF_CALLS"\nexit 0\n',
    )
    write_executable(
        isolated_env.bin_dir / "atuin",
        r"""#!/bin/sh
        printf '%s\n' "$*" >> "$ATUIN_CALLS"
        case "$1" in
          init)
            [ "${FAIL_INIT:-0}" != 1 ] || exit 1
            up=true
            for arg in "$@"; do [ "$arg" != --disable-up-arrow ] || up=false; done
            printf '__atuin_bind_ctrl_r=false\n__atuin_bind_up_arrow=%s\n' "$up"
            cat "$ATUIN_SOURCE"
            if [ "${FAIL_AFTER_SOURCE:-0}" = 1 ]; then printf '\nfalse\n'; fi
            ;;
          uuid) printf 'fixture-session\n' ;;
          history)
            if [ "$2" = start ]; then
              id=fixture-history-id
              [ "${ATUIN_UNIQUE_IDS:-0}" != 1 ] || id="history-$$"
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


SETUP = r"""
. "$REPO/lib/guards.sh"
. "$REPO/lib/helpers.sh"
REMOTE_DOTS_DIR="$REPO/dots"
bash_preexec_imported=1
reload_history() {
  . "$REPO/shell/rc.d/06-bash-history.sh"
  . "$REPO/shell/rc.d/20-fzf.sh"
  . "$REPO/shell/rc.d/23-atuin.sh"
}
dump_k() {
  local line
  while IFS= read -r line; do
    case "$line" in '"k"'*) printf '%s\n' "$line" ;; esac
  done < <(bind -m vi-command -p; bind -m vi-command -s; bind -m vi-command -X 2>/dev/null)
}
"""


@pytest.mark.parametrize("wrapper", ["none", "alias", "function"])
def test_upstream_atuin_full_rc_lifecycle(
    repo_dir: Path,
    runtime_bash: str,
    upstream_env: dict[str, str],
    wrapper: str,
) -> None:
    script = r"""
audit_user_exec() { :; }
audit_user_cmd() { :; }
audit_user_onload() { :; }
audit_late_hook() { :; }
preexec_functions=(audit_user_exec)
precmd_functions=(audit_user_cmd)
BLE_ONLOAD=(audit_user_onload)
case "$WRAPPER" in
  alias) alias atuin='command atuin' ;;
  function) atuin() { command atuin "$@"; } ;;
esac
. "$REPO/shell/rc.sh"
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 20
preexec_functions+=(audit_late_hook)
precmd_functions+=(audit_late_hook)
BLE_ONLOAD+=(audit_late_hook)
exec_count=${#preexec_functions[@]}
cmd_count=${#precmd_functions[@]}
ble_count=${#BLE_ONLOAD[@]}
for cycle in 1 2 3; do
  REMOTE_SSH_ENABLE_ATUIN=0
  rcrc
  [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 && "$HISTFILE" == "$SAVED_HISTORY" ]] || exit 21
  [[ " ${preexec_functions[*]} " == *' audit_user_exec '* && " ${preexec_functions[*]} " == *' audit_late_hook '* ]] || exit 22
  [[ " ${precmd_functions[*]} " == *' audit_user_cmd '* && " ${precmd_functions[*]} " == *' audit_late_hook '* ]] || exit 29
  pending_count=0
  [[ -z "${REMOTE_SSH_ATUIN_PENDING_ID:-}" ]] || pending_count=1
  [[ ${#preexec_functions[@]} == $((exec_count - 1)) && ${#precmd_functions[@]} == $((cmd_count - 1 + pending_count)) ]] || exit 31
  [[ "${BLE_ONLOAD[*]}" == 'audit_user_onload audit_late_hook' ]] || exit 30
  REMOTE_SSH_ENABLE_ATUIN=1
  rcrc
  rcrc
  [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 && "$HISTFILE" == '' ]] || exit 23
  # This directly entered multiline loop changes the outer call site. Pending
  # completion is conservatively discarded; only the active hooks remain.
  [[ -z "${REMOTE_SSH_ATUIN_PENDING_ID:-}" && -z "${REMOTE_SSH_ATUIN_PENDING_TIME:-}" && -z "${REMOTE_SSH_ATUIN_PENDING_CONTEXT:-}" ]] || exit 32
  [[ ${#preexec_functions[@]} == "$exec_count" && ${#precmd_functions[@]} == "$cmd_count" && ${#BLE_ONLOAD[@]} == "$ble_count" ]] || exit 24
done
command atuin noop
mv "$ATUIN_BIN" "$ATUIN_BIN.saved"
rcrc
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]] || exit 25
mv "$ATUIN_BIN.saved" "$ATUIN_BIN"
rcrc
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 && "$__atuin_initialized" == true ]] || exit 26
audit_check_callbacks() {
  trap - DEBUG
  __atuin_preexec audit-functional-marker
  [[ "$ATUIN_HISTORY_ID" == fixture-history-id ]] || exit 27
  __atuin_precmd
  [[ "$ATUIN_HISTORY_ID" == '' ]] || exit 28
}
audit_check_callbacks
printf 'lifecycle-ok\n'
exit
"""
    # Send separate interactive lines: this runs the real rcrc alias and the
    # bash-preexec prompt hooks instead of modeling a reload with direct calls.
    result = subprocess.run(
        [runtime_bash, "--noprofile", "--norc", "-i"],
        input=script,
        text=True,
        capture_output=True,
        env=upstream_env
        | {
            "REPO": str(repo_dir),
            "WRAPPER": wrapper,
            "SAVED_HISTORY": upstream_env["HISTFILE"],
            "ATUIN_BIN": str(Path(upstream_env["PATH"].split(":")[0]) / "atuin"),
        },
        timeout=15,
    )
    assert_ok(result)
    assert "lifecycle-ok" in result.stdout
    calls = Path(upstream_env["ATUIN_CALLS"]).read_text().splitlines()
    assert sum(line.startswith("init ") for line in calls) == 1
    assert "history start -- audit-functional-marker" in calls


@pytest.mark.parametrize("initial", ["shell", "macro", "readline", "unbound"])
@pytest.mark.parametrize("change", ["none", "shell", "unbound"])
def test_upstream_atuin_restores_typed_bindings(
    repo_dir: Path,
    runtime_bash: str,
    upstream_env: dict[str, str],
    initial: str,
    change: str,
) -> None:
    if run_cmd([runtime_bash, "-c", "bind -X"], env=upstream_env).returncode != 0:
        pytest.skip("bind -X requires modern Bash; legacy bindings use the PTY regression")
    script = (
        SETUP
        + r"""
case "$INITIAL" in
  shell) bind -m vi-command -x "\"k\": $USER_COMMAND" ;;
  macro) bind -m vi-command '"k":"original-macro"' ;;
  readline) bind -m vi-command '"k":previous-history' ;;
  unbound) bind -m vi-command -r k ;;
esac
expected="$(dump_k)"
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 10
case "$CHANGE" in
  shell) bind -m vi-command -x '"k": audit_changed_while_active' ;;
  unbound) bind -m vi-command -r k ;;
esac
[[ "$CHANGE" == none ]] || expected="$(dump_k)"
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
[[ "$(dump_k)" == "$expected" ]] || exit 11
bind -m vi-command -x '"k": audit_changed_while_disabled'
expected="$(dump_k)"
REMOTE_SSH_ENABLE_ATUIN=1
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 12
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
[[ "$(dump_k)" == "$expected" ]] || exit 13
printf 'bindings-ok\n'
"""
    )
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env
        | {
            "REPO": str(repo_dir),
            "INITIAL": initial,
            "CHANGE": change,
            "USER_COMMAND": "printf '%s\\n' 'quotes \" | \\ path' | cat\n: user-command",
        },
    )
    assert_ok(result)
    assert "bindings-ok" in result.stdout


@pytest.mark.parametrize(
    "keymap,key", [("emacs", r"\e[A"), ("vi-insert", r"\eOA"), ("vi-command", r"\e[A")]
)
def test_upstream_atuin_restores_arrow_shell_commands(
    repo_dir: Path,
    runtime_bash: str,
    upstream_env: dict[str, str],
    keymap: str,
    key: str,
) -> None:
    if run_cmd([runtime_bash, "-c", "bind -X"], env=upstream_env).returncode != 0:
        pytest.skip("legacy shell commands are protected by disabling arrow takeover")
    script = (
        SETUP
        + r"""
bind -m "$KEYMAP" -x "\"$KEY\": audit_user_arrow"
expected="$(bind -m "$KEYMAP" -X)"
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 10
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
[[ "$(bind -m "$KEYMAP" -X)" == *"$expected"* ]] || exit 11
"""
    )
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env | {"REPO": str(repo_dir), "KEYMAP": keymap, "KEY": key},
    )
    assert_ok(result)


def test_upstream_atuin_rolls_back_partial_binding_reattachment(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    if run_cmd([runtime_bash, "-c", "bind -X"], env=upstream_env).returncode != 0:
        pytest.skip("this failure injection targets modern binding takeover")
    script = (
        SETUP
        + r"""
reload_history
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
for map in emacs vi-insert vi-command; do
  bind -m "$map" '"\e[A":"user-arrow"'
  bind -m "$map" '"\eOA":"user-arrow"'
done
bind -m vi-command '"k":previous-history'
before_emacs="$(bind -m emacs -s)"
before_viins="$(bind -m vi-insert -s)"
before_vicmd="$(bind -m vi-command -s)"
before_k="$(dump_k)"
bind() {
  if [[ "$1" == -m && "$2" == vi-command && "$3" == '"k":'* ]]; then
    binding_failed=1
    return 73
  fi
  builtin bind "$@"
}
REMOTE_SSH_ENABLE_ATUIN=1
reload_history
unset -f bind
[[ "$binding_failed" == 1 && "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]] || exit 10
[[ "$HISTFILE" == "$SAVED_HISTORY" && "$REMOTE_SSH_FZF_HISTORY_BOUND" == 1 ]] || exit 11
[[ "$(bind -m emacs -s)" == "$before_emacs" && "$(bind -m vi-insert -s)" == "$before_viins" && "$(bind -m vi-command -s)" == "$before_vicmd" && "$(dump_k)" == "$before_k" ]] || exit 12
[[ ${#preexec_functions[@]} == 0 && ${#precmd_functions[@]} == 0 && ${#BLE_ONLOAD[@]} == 0 ]] || exit 13
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 14
"""
    )
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env | {"REPO": str(repo_dir), "SAVED_HISTORY": upstream_env["HISTFILE"]},
    )
    assert_ok(result)


@pytest.mark.parametrize("missing", ["__atuin_preexec", "__atuin_history"])
def test_upstream_atuin_failed_reattachment_keeps_fallback(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], missing: str
) -> None:
    script = (
        SETUP
        + r"""
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 10
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
saved_function="$(declare -f "$MISSING")"
unset -f "$MISSING"
audit_user_hook() { :; }
preexec_functions+=(audit_user_hook)
precmd_functions+=(audit_user_hook)
BLE_ONLOAD+=(audit_user_hook)
bind -m vi-command '"k":previous-history'
expected_binding="$(dump_k)"
REMOTE_SSH_ENABLE_ATUIN=1
for attempt in 1 2; do
  reload_history
  [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 && "$HISTFILE" == "$SAVED_HISTORY" ]] || exit 11
  [[ "$REMOTE_SSH_FZF_HISTORY_BOUND" == 1 && "$__atuin_initialized" == true ]] || exit 12
  [[ "${preexec_functions[*]}" == audit_user_hook && "${precmd_functions[*]}" == audit_user_hook && "${BLE_ONLOAD[*]}" == audit_user_hook ]] || exit 13
  [[ "$(dump_k)" == "$expected_binding" ]] || exit 14
done
eval "$saved_function"
reload_history
reload_history
[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 && "$HISTFILE" == '' ]] || exit 15
[[ ${#preexec_functions[@]} == 2 && ${#precmd_functions[@]} == 2 && ${#BLE_ONLOAD[@]} == 3 ]] || exit 16
REMOTE_SSH_ENABLE_ATUIN=0
reload_history
[[ "$(dump_k)" == "$expected_binding" ]] || exit 17
"""
    )
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env
        | {"REPO": str(repo_dir), "MISSING": missing, "SAVED_HISTORY": upstream_env["HISTFILE"]},
    )
    assert_ok(result)
    calls = Path(upstream_env["ATUIN_CALLS"]).read_text().splitlines()
    assert sum(line.startswith("init ") for line in calls) == 1


@pytest.mark.parametrize("scenario", ["external", "failed-init"])
def test_upstream_atuin_preserves_foreign_or_failed_initialization(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], scenario: str
) -> None:
    script = (
        SETUP
        + r"""
audit_user_hook() { :; }
preexec_functions=(audit_user_hook)
precmd_functions=(audit_user_hook)
BLE_ONLOAD=(audit_user_hook)
bind -m vi-command '"k":"user-macro"'
if [[ "$SCENARIO" == external ]]; then
  __atuin_bind_ctrl_r=false
  __atuin_bind_up_arrow=true
  . "$ATUIN_SOURCE"
fi
expected_binding="$(dump_k)"
expected_exec="${preexec_functions[*]}"
expected_cmd="${precmd_functions[*]}"
expected_ble="${BLE_ONLOAD[*]}"
for attempt in 1 2; do
  reload_history
  [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 && "$HISTFILE" == "$SAVED_HISTORY" ]] || exit 10
  [[ "$__atuin_initialized" == true ]] || exit 11
  if [[ "$SCENARIO" == external ]]; then
    [[ "${REMOTE_SSH_FZF_HISTORY_BOUND:-0}" == 0 ]] || exit 14
  else
    [[ "$REMOTE_SSH_FZF_HISTORY_BOUND" == 1 ]] || exit 15
  fi
  [[ "${preexec_functions[*]}" == "$expected_exec" && "${precmd_functions[*]}" == "$expected_cmd" && "${BLE_ONLOAD[*]}" == "$expected_ble" ]] || exit 12
  [[ "$(dump_k)" == "$expected_binding" ]] || exit 13
  REMOTE_SSH_ENABLE_ATUIN=0
  reload_history
  REMOTE_SSH_ENABLE_ATUIN=1
done
"""
    )
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script],
        env=upstream_env
        | {
            "REPO": str(repo_dir),
            "SCENARIO": scenario,
            "FAIL_AFTER_SOURCE": "1" if scenario == "failed-init" else "0",
            "SAVED_HISTORY": upstream_env["HISTFILE"],
        },
    )
    assert_ok(result)
    calls = Path(upstream_env["ATUIN_CALLS"]).read_text().splitlines()
    assert sum(line.startswith("init ") for line in calls) == (scenario == "failed-init")


@pytest.mark.parametrize("initial", ["shell", "readline"])
def test_upstream_atuin_shell_binding_survives_real_keypresses(
    repo_dir: Path,
    runtime_bash: str,
    isolated_env: IsolatedEnv,
    upstream_env: dict[str, str],
    initial: str,
) -> None:
    marker = isolated_env.home / "keypresses"
    setup = isolated_env.home / "setup.sh"
    setup.write_text(
        SETUP
        + r"""
set -o vi
audit_user_binding() { printf 'pressed\n' >> "$KEY_MARKER"; }
bind -m vi-command -x '"k": audit_user_binding'
"""
    )
    env = upstream_env | {"REPO": str(repo_dir), "KEY_MARKER": str(marker), "PS1": "ATUIN_TEST> "}
    pid, fd = pty.fork()
    if pid == 0:
        os.execve(runtime_bash, [runtime_bash, "--noprofile", "--norc", "-i"], env)
    output = bytearray()
    completed_commands = 0

    def until(predicate) -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if predicate():
                return
            readable, _, _ = select.select([fd], [], [], 0.03)
            if readable:
                try:
                    output.extend(os.read(fd, 65536))
                except OSError:
                    break
        raise AssertionError(output.decode(errors="replace"))

    def prompt() -> None:
        until(lambda: b"ATUIN_TEST> " in output)
        output.clear()

    def command(value: str) -> None:
        nonlocal completed_commands
        completed_commands += 1
        marker = f"\x1e{completed_commands}\x1f".encode()
        # Readline may redraw PS1 while consuming a long input. Wait for an
        # executed printf with control bytes that cannot match the input echo.
        suffix = rf"; printf '\036%s\037' {completed_commands}".encode()
        os.write(fd, value.encode() + suffix + b"\n")
        until(lambda: marker in output)
        del output[: output.index(marker) + len(marker)]
        prompt()

    def press_k(count: int) -> None:
        os.write(fd, b"\x1bk")
        until(lambda: marker.exists() and len(marker.read_text().splitlines()) == count)
        output.clear()
        os.write(fd, b"\x03")
        prompt()

    try:
        prompt()
        command(f". {shlex.quote(str(setup))}")
        press_k(1)
        if initial == "readline":
            # Make every tracked binding readable even without bind -X, then
            # introduce an unreadable shell command while Atuin is detached.
            command(
                r"""for map in emacs vi-insert vi-command; do
                  bind -m "$map" '"\e[A":previous-history'
                  bind -m "$map" '"\eOA":previous-history'
                done; bind -m vi-command '"k":previous-history'"""
            )
        command('reload_history; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 20')
        legacy = run_cmd([runtime_bash, "-c", "bind -X"], env=env).returncode != 0
        calls = Path(upstream_env["ATUIN_CALLS"]).read_text()
        assert ("--disable-up-arrow" in calls) == (legacy and initial == "shell")
        command(
            'REMOTE_SSH_ENABLE_ATUIN=0; reload_history; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]] || exit 21'
        )
        if initial == "readline":
            command("bind -m vi-command -x '\"k\": audit_user_binding'")
        command(
            'REMOTE_SSH_ENABLE_ATUIN=1; reload_history; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 22'
        )
        if legacy:
            press_k(2)
        command(
            'REMOTE_SSH_ENABLE_ATUIN=0; reload_history; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]] || exit 23'
        )
        press_k(3 if legacy else 2)
        os.write(fd, b"exit\n")
        until(lambda: b"exit" in output)
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        # Closing the master releases terminal output/teardown before reaping
        # the child. Never let cleanup turn a failed PTY test into a hung suite.
        os.close(fd)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if os.waitpid(pid, os.WNOHANG)[0] == pid:
                break
            time.sleep(0.01)
        else:
            pytest.fail(f"PTY shell {pid} did not exit after SIGKILL and terminal close")
