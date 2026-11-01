# shellcheck shell=bash

ensure_this_file_sourced
[[ -n "${BASH_VERSION:-}" && $- == *i* ]] || return 0
[[ -z "${REMOTE_SSH_HISTORY_BACKEND+x}" ]] || return 0
# External Atuin owns its history policy, including an unset HISTFILE.
[[ "${__atuin_initialized:-}" != true ]] || return 0

# An explicit empty HISTFILE or /dev/null is a user choice. Keep in-memory
# history; only successful owned Atuin setup suppresses file persistence.
if [[ -z "${HISTFILE+x}" ]]; then HISTFILE="$HOME/.bash_history"; fi
