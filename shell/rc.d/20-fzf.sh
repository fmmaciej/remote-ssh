# shellcheck shell=bash

ensure_this_file_sourced

have fzf || return 0

: "${FZF_DEFAULT_OPTS:=--height=40% --reverse --border}"
export FZF_DEFAULT_OPTS

__fzf_history() {
  local cmd
  builtin history -n 2>/dev/null || true

  cmd=$(
    builtin history |
      sed 's/^[[:space:]]*[0-9]\+[[:space:]]*//' |
      awk '
        { lines[NR] = $0 }
        END {
          for (i = NR; i >= 1; i--) {
            if (!seen[lines[i]]++) {
              print lines[i]
            }
          }
        }
      ' |
      fzf \
        --prompt='history> ' \
        --layout=reverse \
        --preview 'printf "%s\n" {}' \
        --preview-window=down:3:wrap
  ) || return

  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}

# bind tylko jeśli readline (bash interaktywny) i Atuin nie przejmuje historii
if [[ -n ${BASH_VERSION:-} && $- == *i* ]] && ! have atuin; then
  # jeśli readline działa
  bind -q '"\C-r"' >/dev/null 2>&1 && :
  bind -x '"\C-r":__fzf_history' 2>/dev/null || true
fi
