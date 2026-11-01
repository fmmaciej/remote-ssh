# shellcheck shell=bash

ensure_this_file_sourced

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
  # This also runs before 23-atuin.sh on first load. A guard set by our own
  # failed initializer still needs fallback; an external integration owns its keys.
  if [[ "${__atuin_initialized:-}" == true && "${REMOTE_SSH_ATUIN_INITIALIZED:-0}" != 1 &&
    "${REMOTE_SSH_ATUIN_FAILED_INIT_GUARD:-0}" != 1 ]]; then
    return 0
  fi
  if [[ "${REMOTE_SSH_ATUIN_ACTIVE:-0}" == 1 ]]; then
    if [[ "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" == 1 ]]; then
      bind '"\C-r":reverse-search-history' 2>/dev/null || true
      REMOTE_SSH_SKIM_HISTORY_BOUND=0
    fi
  else
    bind -x '"\C-r":__skim_history' 2>/dev/null || return 0
    REMOTE_SSH_SKIM_HISTORY_BOUND=1
  fi
}

# If Atuin might initialize later, wait for its actual result in 23-atuin.sh.
if ! have atuin || [[ "${REMOTE_SSH_ENABLE_ATUIN:-1}" != 1 ]]; then
  remote_skim_history_bind
fi
