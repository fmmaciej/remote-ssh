# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

[[ -n "${BASH_VERSION:-}" ]] || return 0

# Keep Bash history available in memory for the current interactive session,
# but let Atuin be the only durable history backend for remote-ssh sessions.
export HISTFILE=
