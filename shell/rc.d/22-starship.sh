# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

have starship || return 0

[ -f "$REMOTE_DOTS_DIR/starship.toml" ] && export STARSHIP_CONFIG="$REMOTE_DOTS_DIR/starship.toml"

case "${BASH_VERSION:+bash}${ZSH_VERSION:+zsh}" in
  bash)
    eval "$(starship init bash)"
    ;;
  zsh)
    eval "$(starship init zsh)"
    ;;
esac
