# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

[[ -n "${BASH_VERSION:-}" ]] || return 0

remote_history_use_bash() {
  if [[ "${REMOTE_SSH_HISTORY_OWNED:-0}" == 1 && "${HISTFILE:-}" == '' ]]; then
    HISTFILE="$REMOTE_SSH_HISTORY_PRE_ATUIN"
  fi
  REMOTE_SSH_HISTORY_OWNED=0
  # An explicit empty HISTFILE or /dev/null is a user choice.
  if [[ -z "${HISTFILE+x}" ]]; then HISTFILE="$HOME/.bash_history"; fi
}

remote_history_use_atuin() {
  if [[ "${REMOTE_SSH_HISTORY_OWNED:-0}" == 1 && "${HISTFILE:-}" == '' ]]; then return 0; fi
  REMOTE_SSH_HISTORY_PRE_ATUIN="${HISTFILE-$HOME/.bash_history}"
  REMOTE_SSH_HISTORY_OWNED=1
  HISTFILE=
}

remote_history_use_bash
