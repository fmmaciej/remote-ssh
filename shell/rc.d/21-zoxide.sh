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

# Share the same picker between zi and z's interactive completion. Neither
# path may call zoxide query --interactive, which launches fzf internally.
remote_zoxide_pick() {
  have sk || {
    printf 'zoxide selection requires skim (sk): remote-ssh install sk\n' >&2
    return 127
  }
  local candidates result
  candidates="$(command zoxide query --list "$@")" || return
  [[ -n "$candidates" ]] || return 1
  result="$(printf '%s\n' "$candidates" | sk --no-sort --prompt='directory> ' \
    --preview='ls -Cp -- {}' --preview-window=down:30%:wrap)" || return
  [[ -n "$result" ]] || return 1
  printf '%s\n' "$result"
}

zi() {
  local result
  result="$(remote_zoxide_pick -- "$@")" || return
  builtin cd -- "$result" || return
  if [[ "${_ZO_ECHO:-0}" == 1 ]]; then printf '%s\n' "$PWD"; fi
}

# Retain the upstream registration and Readline helper on Bash versions where
# zoxide installs its completion (4.4+); replace only the selection callback.
if [[ -n "${BASH_VERSION:-}" ]] &&
  declare -F __zoxide_z_complete >/dev/null && declare -F __zoxide_z_complete_helper >/dev/null; then
  __zoxide_z_complete() {
    local count="${#COMP_WORDS[@]}" entry current
    ((count == COMP_CWORD + 1)) || return 0
    if ((count == 2)); then
      COMPREPLY=()
      while IFS= read -r entry; do COMPREPLY+=("$entry"); done < <(
        compgen -A directory -- "${COMP_WORDS[1]}" || true
      )
    elif ((count > 2)) && [[ -z "${COMP_WORDS[count-1]}" ]]; then
      current="$(__zoxide_pwd)"
      COMPREPLY=()
      if __zoxide_result="$(remote_zoxide_pick --exclude "$current" -- "${COMP_WORDS[@]:1:count-2}")"; then
        # zoxide init supplies the prefix consumed by its z function.
        # shellcheck disable=SC2154
        COMPREPLY=("${__zoxide_z_prefix}${__zoxide_result}/")
        bind -x '"\e[0n": __zoxide_z_complete_helper'
      else
        bind '"\e[0n": redraw-current-line' 2>/dev/null || true
      fi
      printf '\e[5n' 2>/dev/null >/dev/tty || true
    fi
    return 0
  }
fi
