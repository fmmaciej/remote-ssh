# shellcheck shell=bash

remote_ssh_update_check_state_dir() {
  if [[ -n "${REMOTE_SSH_UPDATE_CHECK_STATE_DIR:-}" ]]; then
    printf '%s\n' "$REMOTE_SSH_UPDATE_CHECK_STATE_DIR"
    return 0
  fi

  if [[ -n "${XDG_STATE_HOME:-}" ]]; then
    printf '%s/remote-ssh\n' "$XDG_STATE_HOME"
  elif [[ -n "${HOME:-}" ]]; then
    printf '%s/.local/state/remote-ssh\n' "$HOME"
  else
    return 1
  fi
}

remote_ssh_update_check_cache_file() {
  local state_dir

  state_dir="$(remote_ssh_update_check_state_dir)" || return 1
  printf '%s/update-check\n' "$state_dir"
}

remote_ssh_update_check_cache_get() {
  local file="$1" key="$2" line

  [[ -r "$file" ]] || return 1
  line="$(grep -m 1 "^${key}=" "$file" 2>/dev/null)" || return 1
  printf '%s\n' "${line#*=}"
}
