# shellcheck shell=bash

ensure_this_file_sourced

have atuin || return 0
[[ $- == *i* ]] || return 0

if [[ -n "${BASH_VERSION:-}" ]]; then
  eval "$(atuin init bash)"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
  eval "$(atuin init zsh)"
fi
