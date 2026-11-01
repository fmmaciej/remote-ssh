# shellcheck shell=bash

ensure_this_file_sourced

if [[ -n "${BASH_VERSION:-}" && $- == *i* && -n "${REMOTE_SSH_HISTORY_BACKEND+x}" ]]; then return 0; fi

have sk || return 0

: "${SKIM_DEFAULT_OPTIONS:=--height=40% --reverse --border}"
export SKIM_DEFAULT_OPTIONS

__skim_history() {
  local cmd
  builtin history -n 2>/dev/null || true

  cmd=$(
    builtin history |
      sed 's/^[[:space:]]*[0-9][0-9]*[[:space:]]*//' |
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
      sk \
        --prompt='history> ' \
        --layout=reverse \
        --preview 'printf "%s\n" {}' \
        --preview-window=down:3:wrap
  ) || return

  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}

remote_skim_history_bind() {
  [[ -n ${BASH_VERSION:-} && $- == *i* ]] || return 0
  [[ "${REMOTE_SSH_HISTORY_BACKEND:-}" == bash ]] || return 0
  [[ "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" != 1 ]] || return 0
  bind -m emacs -x '"\C-r":__skim_history' 2>/dev/null || return 0
  bind -m vi-insert -x '"\C-r":__skim_history' 2>/dev/null || return 0
  REMOTE_SSH_SKIM_HISTORY_BOUND=1
}

# 23-atuin.sh finalizes ownership after the initial Atuin attempt.
