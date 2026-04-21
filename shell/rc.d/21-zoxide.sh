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

if ! type z >/dev/null 2>&1; then
  z() {
    if [[ $# -eq 0 ]]; then
      builtin cd -- "$HOME" || return
      return
    fi

    local result
    result="$(command zoxide query --exclude "$PWD" -- "$@")" || return
    builtin cd -- "$result" || return
  }
fi

if ! type zi >/dev/null 2>&1; then
  zi() {
    local result
    result="$(command zoxide query --interactive -- "$@")" || return
    builtin cd -- "$result" || return
  }
fi
