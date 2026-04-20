# shellcheck shell=bash

ensure_this_file_sourced

if have atuin; then
  [[ $- == *i* ]] || return 0

  [ -f "$REMOTE_DOTS_DIR/atuin/config.toml" ] && export ATUIN_CONFIG_DIR="$REMOTE_DOTS_DIR/atuin"

  [ -n "${BASH_VERSION:-}" ] && eval "$(atuin init bash)"
  [ -n "${ZSH_VERSION:-}" ] && eval "$(atuin init zsh)"
fi
