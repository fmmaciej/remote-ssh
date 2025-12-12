# shellcheck shell=bash

ensure_this_file_sourced

if have starship; then
  [ -f "$REMOTE_DOTS_DIR/starship.toml" ] && export STARSHIP_CONFIG="$REMOTE_DOTS_DIR/starship.toml"

  [ -n "${BASH_VERSION:-}" ] && eval "$(starship init bash)"
  [ -n "${ZSH_VERSION:-}" ] && eval "$(starship init zsh)"
fi
