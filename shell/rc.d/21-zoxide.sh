# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

have zoxide || return 0

case "${BASH_VERSION:+bash}${ZSH_VERSION:+zsh}" in
  bash)
    eval "$(zoxide init bash 2>/dev/null || true)"
    ;;
  zsh)
    eval "$(zoxide init zsh 2>/dev/null || true)"
    ;;
esac
