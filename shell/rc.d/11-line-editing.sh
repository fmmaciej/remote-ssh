# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

if [[ -n "${BASH_VERSION:-}" ]]; then
  set -o vi
  return 0
fi

if [[ -n "${ZSH_VERSION:-}" ]]; then
  bindkey -v
  return 0
fi
