# shellcheck shell=bash
# Definitions only: rc.sh finalizes the editor after OS and host hooks.

[[ "${REMOTE_SSH_FLYLINE_MODULE_PID:-}" != "${BASHPID:-$$}" ]] || return 0
REMOTE_SSH_FLYLINE_MODULE_PID="${BASHPID:-$$}"
export -n REMOTE_SSH_FLYLINE_MODULE_PID

remote_flyline_library() {
  local INSTALL_PREFIX="${INSTALL_PREFIX:-$HOME/.local/opt}"
  local TOOLS_DIR="$REMOTE_ENV_DIR/tools"
  # shellcheck disable=SC2034 # Scope every variable written by the definition.
  local TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME INSTALL_LAYOUT
  # shellcheck disable=SC2034
  local -a ASSETS CHECKSUMS LIBRARY_MEMBERS BINARY_ALIASES
  [[ -r "$TOOLS_DIR/defs/flyline.sh" ]] || return 1
  # Trusted pinned checkout data, with definition variables scoped to this call.
  # shellcheck source=/dev/null
  . "$TOOLS_DIR/defs/flyline.sh"
  [[ "$TOOL_NAME" == flyline && "$INSTALL_LAYOUT" == bash-builtin ]] || return 1
  # shellcheck source=/dev/null
  . "$TOOLS_DIR/lib/common/release.sh"
  remote_ssh_library_install_valid "$INSTALL_PREFIX/.active/flyline" flyline "$VERSION" || return 1
  printf '%s/%s\n' "$REMOTE_SSH_RELEASE_DIR" "$REMOTE_SSH_RELEASE_LIBRARY"
}

__remote_ssh_flyline_history_vi() { __atuin_history --keymap-mode=vim-insert; }
__remote_ssh_flyline_history_emacs() { __atuin_history --keymap-mode=emacs; }

remote_flyline_settings() {
  builtin flyline run-tutorial false &&
    builtin flyline --show-animations false --enable-easter-eggs false \
      --enable-extended-key-codes false --send-shell-integration-codes none \
      --set-mouse-mode disabled set-cursor --backend terminal &&
    builtin flyline suggestions --auto-suggest false --auto-suggest-inline false --use-flycomp false &&
    builtin flyline history --backend bash || return 1

  local vi_action='' emacs_action=''
  case "${REMOTE_SSH_HISTORY_BACKEND:-bash}" in
    atuin)
      if [[ -z "${ATUIN_NOBIND:-}" ]]; then
        vi_action='vimInsertMode=runBashCommand(__remote_ssh_flyline_history_vi)'
        emacs_action='!vimModeEnabled+editingBufferMode=runBashCommand(__remote_ssh_flyline_history_emacs)'
      fi
      ;;
    bash)
      if declare -F __skim_history >/dev/null; then
        vi_action='vimInsertMode=runBashCommand(__skim_history)'
        emacs_action='!vimModeEnabled+editingBufferMode=runBashCommand(__skim_history)'
      fi
      ;;
  esac
  if [[ -n "$vi_action" ]]; then
    builtin flyline key --vim-mode true bind Ctrl+r "$vi_action" &&
      builtin flyline key bind Ctrl+r "$emacs_action"
  else
    builtin flyline key --vim-mode true
  fi
}

remote_flyline_finalize() {
  [[ $- == *i* ]] || return 0
  [[ "${REMOTE_SSH_FLYLINE_PID:-}" != "${BASHPID:-$$}" ]] || return 0
  REMOTE_SSH_FLYLINE_PID="${BASHPID:-$$}"
  REMOTE_SSH_FLYLINE_STATE=disabled
  REMOTE_SSH_FLYLINE_REASON=toggle
  export -n REMOTE_SSH_FLYLINE_PID REMOTE_SSH_FLYLINE_STATE REMOTE_SSH_FLYLINE_REASON
  # The history choice belongs to this process too, even if the caller exported
  # these private variables before a reload.
  export -n REMOTE_SSH_HISTORY_REQUEST REMOTE_SSH_HISTORY_BACKEND
  [[ "${REMOTE_SSH_ENABLE_FLYLINE:-0}" == 1 ]] || return 0
  REMOTE_SSH_FLYLINE_STATE=skipped
  REMOTE_SSH_FLYLINE_REASON=terminal
  [[ -t 0 && -t 1 ]] || return 0
  case "${TERM:-}" in ''|dumb|unknown) return 0 ;; esac
  REMOTE_SSH_FLYLINE_REASON=bash
  ((BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 4))) || return 0
  REMOTE_SSH_FLYLINE_REASON=external
  [[ "${REMOTE_SSH_HISTORY_BACKEND:-bash}" != external ]] || return 0
  # OS/host hooks can initialize Atuin after our process-local selection.
  [[ "${__atuin_initialized:-}" != true || "${REMOTE_SSH_HISTORY_BACKEND:-bash}" == atuin ]] || return 0
  builtin declare -F flyline >/dev/null && return 0
  builtin alias flyline >/dev/null 2>&1 && return 0
  local existing
  # Inspect both builtin states without changing either.
  while IFS= read -r existing; do
    case "$existing" in 'enable flyline'|'enable -n flyline') return 0 ;; esac
  done < <(builtin enable -a)
  [[ -z "${BLE_VERSION:-}${_ble_attached:-}" ]] || return 0
  declare -F ble-attach >/dev/null && return 0

  local library old_dir="${FLYLINE_LOAD_DIR-}" old_version="${FLYLINE_VERSION-}"
  local had_dir="${FLYLINE_LOAD_DIR+x}" had_version="${FLYLINE_VERSION+x}"
  local attributes dir_exported=0 version_exported=0
  attributes="$(declare -p FLYLINE_LOAD_DIR 2>/dev/null)" || attributes=
  attributes="${attributes#declare -}"; attributes="${attributes%% *}"
  [[ "$attributes" != *x* ]] || dir_exported=1
  attributes="$(declare -p FLYLINE_VERSION 2>/dev/null)" || attributes=
  attributes="${attributes#declare -}"; attributes="${attributes%% *}"
  [[ "$attributes" != *x* ]] || version_exported=1
  REMOTE_SSH_FLYLINE_REASON=unavailable
  library="$(remote_flyline_library)" || return 0
  REMOTE_SSH_FLYLINE_STATE=failed
  REMOTE_SSH_FLYLINE_REASON=load
  # Ignore inherited Flyline environment markers: only the actual builtin above
  # establishes ownership in this process. An explicit path avoids lookup hooks.
  if builtin enable -f "$library" flyline; then
    FLYLINE_LOAD_DIR="${library%/*}"
    export FLYLINE_LOAD_DIR
    if remote_flyline_settings; then
      REMOTE_SSH_FLYLINE_STATE=active
      REMOTE_SSH_FLYLINE_REASON=managed
      return 0
    fi
    REMOTE_SSH_FLYLINE_REASON=settings
    builtin enable -d flyline || {
      printf 'remote-ssh: Flyline rollback failed; start a new shell with REMOTE_SSH_ENABLE_FLYLINE=0.\n' >&2
      return 0
    }
  fi
  if [[ -n "$had_dir" ]]; then FLYLINE_LOAD_DIR="$old_dir"; else unset FLYLINE_LOAD_DIR; fi
  if [[ -n "$had_version" ]]; then FLYLINE_VERSION="$old_version"; else unset FLYLINE_VERSION; fi
  # Restore export separately, including declarations which are exported/unset.
  if ((dir_exported)); then export FLYLINE_LOAD_DIR; else export -n FLYLINE_LOAD_DIR; fi
  if ((version_exported)); then export FLYLINE_VERSION; else export -n FLYLINE_VERSION; fi
  printf 'remote-ssh: Flyline initialization failed; using Readline.\n' >&2
  return 0
}
