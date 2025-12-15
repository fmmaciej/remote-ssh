# shellcheck shell=bash

ensure_this_file_sourced

have fzf || return 0

: "${FZF_DEFAULT_OPTS:=--height=40% --reverse --border}"
export FZF_DEFAULT_OPTS

__fzf_history() {
  local cmd

  cmd=$(
    history \
      | sed 's/^[[:space:]]*[0-9]\+[[:space:]]*//' \
      | awk '!seen[$0]++' \
      | fzf \
          --prompt='history> ' \
          --preview 'echo {}' \
          --preview-window=down:3:wrap
  ) || return

  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}

# bind tylko jeśli readline (bash interaktywny)
if [[ -n "${BASH_VERSION:-}" ]]; then
  bind -x '"\C-r":__fzf_history'
fi
