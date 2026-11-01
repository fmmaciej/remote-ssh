from __future__ import annotations

from pathlib import Path

import pytest
from conftest import assert_ok, run_cmd
from pty_shell import PtyShell
from test_atuin_lifecycle import upstream_env as upstream_env
from test_atuin_ownership import ends, history_id
from test_atuin_ownership import event_env as event_env

# Bounded combinations cover alias expansion, function attributes and ownership.
CASES = [
    ("disabled", "none", "on", True, "custom"),
    ("absent", "none", "on", False, "empty"),
    ("success", "none", "on", True, "custom"),
    ("success", "exported", "on", True, "custom"),
    ("success", "exported", "off", True, "custom"),
    ("partial", "ordinary", "on", False, "empty"),
    ("return", "exported", "on", False, "null"),
    ("readonly", "readonly", "on", False, "custom"),
    ("readonly-alias", "readonly", "on", True, "empty"),
    ("external", "readonly", "on", True, "null"),
    ("external-unset", "readonly", "off", False, "unset"),
]


@pytest.mark.parametrize("case,function,expansion,skim,history", CASES)
def test_bind_alias_function_and_option_ownership(
    repo_dir: Path,
    runtime_bash: str,
    upstream_env: dict[str, str],
    case: str,
    function: str,
    expansion: str,
    skim: bool,
    history: str,
) -> None:
    bindir = Path(upstream_env["PATH"].split(":")[0])
    if not skim:
        (bindir / "sk").unlink()
    if case == "absent":
        (bindir / "atuin").unlink()
    if case == "return":
        tool = bindir / "atuin"
        tool.write_text(
            tool.read_text().replace(
                'cat "$ATUIN_SOURCE"', 'cat "$ATUIN_SOURCE"\nprintf "\\nreturn 1\\n"'
            )
        )
    env = upstream_env | {
        "REPO": str(repo_dir),
        "CASE": case,
        "FUNCTION": function,
        "EXPANSION": expansion,
        "HISTORY_CHOICE": history,
        "REMOTE_SSH_ENABLE_ATUIN": "0" if case == "disabled" else "1",
        "FAIL_AFTER_SOURCE": "1" if case in {"partial", "readonly", "readonly-alias"} else "0",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "1" if case.startswith("readonly") else "0",
    }
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      audit_sentinel() { :; }
      preexec_functions=(audit_sentinel); precmd_functions=(audit_sentinel); BLE_ONLOAD=(audit_sentinel)
      function audit_keys() {
        local map line
        for map in emacs vi-insert vi-command; do
          while IFS= read -r line; do
            case "$line" in
              '"\C-x\C-_A'*|'"\C-xQ"'*|'"\C-xS"'*|'"\e[A"'*|'"\eOA"'*|'"k":'*|'"/":'*|'"?":'*)
                printf '%s|%s\n' "$map" "$line" ;;
            esac
          done < <(builtin bind -m "$map" -p; builtin bind -m "$map" -s)
        done
      }
      for map in emacs vi-insert vi-command; do
        builtin bind -m "$map" '"\C-x\C-_A0\a":"user-private-zero"'
        builtin bind -m "$map" '"\C-x\C-_A4\a":"user-private-four"'
        builtin bind -m "$map" '"\C-xQ":"user-private-Q"'
        builtin bind -m "$map" '"\C-xS":"user-private-S"'
        builtin bind -m "$map" '"\e[A":"user-up"'
        builtin bind -m "$map" '"\eOA":"user-up-other"'
      done
      builtin bind -m vi-command '"k":forward-char'
      builtin bind -m vi-command '"/":vi-search'
      builtin bind -m vi-command '"\C-r":vi-redo'
      builtin bind -m emacs '"?":self-insert'
      builtin bind -m emacs '"\C-r":"user-ctrl-r"'
      builtin bind -m vi-insert '"\C-r":"user-ctrl-r"'
      case "$FUNCTION" in
        ordinary|exported|readonly) function bind() { builtin bind "$@"; } ;;
      esac
      [[ "$FUNCTION" != exported ]] || export -f bind
      [[ "$FUNCTION" != readonly ]] || readonly -f bind
      saved_function="$(builtin declare -f bind)"
      # The plain readonly case also establishes behavior without an alias.
      [[ "$CASE" == readonly ]] || alias bind='builtin bind'
      saved_alias="$(builtin alias bind 2>/dev/null)"
      if [[ "$EXPANSION" == off ]]; then shopt -u expand_aliases; else shopt -s expand_aliases; fi
      case "$HISTORY_CHOICE" in
        empty) HISTFILE= ;; null) HISTFILE=/dev/null ;; unset) unset HISTFILE ;;
      esac
      saved_history="${HISTFILE-UNSET}"
      case "$CASE" in external*) __atuin_initialized=true ;; esac
      before="$(audit_keys)"
      builtin source "$REPO/shell/rc.sh"
      [[ "$(builtin alias bind 2>/dev/null)" == "$saved_alias" ]] || exit 10
      [[ "$(builtin declare -f bind)" == "$saved_function" ]] || exit 11
      if [[ "$EXPANSION" == on ]]; then shopt -q expand_aliases || exit 12
      else shopt -q expand_aliases && exit 13; fi
      case "$CASE" in
        success)
          [[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin && "$HISTFILE" == '' ]] || exit 14
          [[ " ${preexec_functions[*]} " == *' __atuin_preexec '* ]] || exit 15
          ;;
        *)
          [[ "$(audit_keys)" == "$before" && "${HISTFILE-UNSET}" == "$saved_history" ]] || exit 16
          [[ " ${preexec_functions[*]} " != *' __atuin_preexec '* && " ${preexec_functions[*]} " == *' audit_sentinel '* ]] || exit 17
          [[ " ${precmd_functions[*]} " != *' __atuin_precmd '* && " ${precmd_functions[*]} " == *' audit_sentinel '* ]] || exit 18
          [[ "${BLE_ONLOAD[*]}" == audit_sentinel ]] || exit 19
          case "$CASE" in external*) [[ "$REMOTE_SSH_HISTORY_BACKEND" == external ]] || exit 20 ;;
            *) [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash ]] || exit 21 ;;
          esac
          ;;
      esac
      case "$CASE" in disabled|absent|external*) [[ -z "${bash_preexec_imported+x}" ]] || exit 22 ;; esac
      if [[ "$FUNCTION" == readonly ]]; then
        (builtin unset -f bind) 2>/dev/null && exit 23
      elif [[ "$FUNCTION" == exported ]]; then
        "$BASH" -c 'builtin declare -F bind >/dev/null' || exit 24
      else
        "$BASH" -c 'builtin declare -F bind >/dev/null' && exit 25
      fi
      if [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash && "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" != 1 ]]; then
        [[ "$(builtin bind -m emacs -s)" == *'"\C-r": "user-ctrl-r"'* ]] || exit 26
        [[ "$(builtin bind -m vi-insert -s)" == *'"\C-r": "user-ctrl-r"'* ]] || exit 27
      fi
      old_backend="$REMOTE_SSH_HISTORY_BACKEND"
      builtin bind -m emacs '"\C-r":"later-user-edit"'
      builtin bind -m emacs '"\C-x\C-_A0\a":"later-private-edit"'
      edited="$(audit_keys)"
      REMOTE_SSH_ENABLE_ATUIN=0; PATH=/usr/bin:/bin
      builtin source "$REPO/shell/rc.sh"
      REMOTE_SSH_ENABLE_ATUIN=1
      builtin source "$REPO/shell/rc.sh"
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == "$old_backend" && "$(audit_keys)" == "$edited" ]] || exit 28
      [[ "$(builtin bind -m emacs -s)" == *'"\C-r": "later-user-edit"'* ]] || exit 29
      [[ "$(builtin alias bind 2>/dev/null)" == "$saved_alias" && "$(builtin declare -f bind)" == "$saved_function" ]] || exit 30
    """,
        ],
        env=env,
    )
    assert_ok(result)
    assert "syntax error" not in result.stderr
    assert "readonly function" not in result.stderr
    calls = Path(env["ATUIN_CALLS"])
    lines = calls.read_text().splitlines() if calls.exists() else []
    assert sum(x.startswith("init ") for x in lines) == (case in {"success", "partial", "return"})
    assert not any(x.startswith("import ") for x in lines)


@pytest.mark.parametrize("case", ["partial", "readonly"])
def test_alias_failed_setup_preserves_private_shell_action_in_real_pty(
    runtime_bash: str, event_env: dict[str, str], case: str
) -> None:
    bindir = Path(event_env["PATH"].split(":")[0])
    (bindir / "sk").unlink()
    env = event_env | {"FAIL_AFTER_SOURCE": "1", "CASE": case}
    marker = Path(env["HOME"]) / "private-key"
    with PtyShell(runtime_bash, env) as shell:
        shell.command(
            r"""
          function audit_private() { echo pressed >> "$HOME/private-key"; }
          function bind() { builtin bind "$@"; }
          [[ "$CASE" != readonly ]] || readonly -f bind
          builtin bind -m emacs -x '"\C-xR":audit_private'
          builtin bind -m emacs -x '"\C-r":audit_private'
          alias bind='builtin bind'
          builtin source "$REPO/shell/rc.sh"
          set -o emacs
          [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash ]]
        """.strip()
        )
        shell.keypress(b"\x18R", marker.exists)
        marker.unlink()
        shell.keypress(b"\x12", marker.exists)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=0; rcrc; rcrc; set -o emacs")
        marker.unlink()
        shell.keypress(b"\x18R", marker.exists)


def test_alias_success_records_exit_status_and_preserves_exported_function(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command(
            r"""
          function bind() { builtin bind "$@"; }
          export -f bind
          alias bind='builtin bind'
          builtin source "$REPO/shell/rc.sh"
          [[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin ]]
        """.strip()
        )
        shell.command(": alias-recording; REMOTE_SSH_ENABLE_ATUIN=0; rcrc; (exit 7)", status=7)
        entry = history_id(event_env, "alias-recording")
        shell.until(lambda: bool(ends(event_env, entry)))
        assert ends(event_env, entry) == [("end", entry, "7")]
        shell.command('"$BASH" -c "builtin declare -F bind >/dev/null"; shopt -q expand_aliases')
