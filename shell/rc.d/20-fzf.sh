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
if [[ -n "${BASH_VERSION:-}" && $- == *i* ]]; then
  # jeśli readline działa
  bind -q '"\C-r"' >/dev/null 2>&1 && :
  bind -x '"\C-r":__fzf_history' 2>/dev/null || true
fi
