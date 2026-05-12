# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_update_check_enabled() {
  case "${REMOTE_SSH_UPDATE_CHECK:-1}" in
    0 | false | no | off) return 1 ;;
    *) return 0 ;;
  esac
}

remote_ssh_update_check_state_dir() {
  if [[ -n "${REMOTE_SSH_UPDATE_CHECK_STATE_DIR:-}" ]]; then
    printf '%s\n' "$REMOTE_SSH_UPDATE_CHECK_STATE_DIR"
    return 0
  fi

  [[ -n "${HOME:-}" ]] || return 1
  printf '%s\n' "${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh"
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

remote_ssh_update_check_interval() {
  case "${REMOTE_SSH_UPDATE_CHECK_INTERVAL:-86400}" in
    '' | *[!0-9]*) printf '86400\n' ;;
    *) printf '%s\n' "$REMOTE_SSH_UPDATE_CHECK_INTERVAL" ;;
  esac
}

remote_ssh_update_check_now() {
  date +%s 2>/dev/null
}

remote_ssh_update_check_is_stale() {
  local file="$1" now checked_at interval

  now="$(remote_ssh_update_check_now)" || return 1
  checked_at="$(remote_ssh_update_check_cache_get "$file" checked_at 2>/dev/null || true)"
  interval="$(remote_ssh_update_check_interval)"

  case "$checked_at" in
    '' | *[!0-9]*) return 0 ;;
  esac

  ((now - checked_at >= interval))
}

remote_ssh_update_check_print_cached_message() {
  local file="$1" status

  status="$(remote_ssh_update_check_cache_get "$file" status 2>/dev/null || true)"
  if [[ "$status" == "update-available" ]]; then
    printf 'remote-ssh: update available. Run: remote-ssh update\n'
  fi
}

remote_ssh_update_check_refresh_in_background() {
  local file="$1" state_dir lock_dir pid

  have remote-ssh || return 0
  have git || return 0

  state_dir="${file%/*}"
  mkdir -p "$state_dir" 2>/dev/null || return 0

  lock_dir="${file}.lock"
  mkdir "$lock_dir" 2>/dev/null || return 0

  (
    trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT
    if remote-ssh update check --quiet --write-cache >/dev/null 2>&1; then
      remote-ssh update check --cached-message 2>/dev/null || true
    fi
  ) &
  pid=$!
  disown "$pid" 2>/dev/null || true
}

case $- in
  *i*) ;;
  *) return 0 ;;
esac

remote_ssh_update_check_enabled || return 0

REMOTE_SSH_UPDATE_CHECK_CACHE_FILE="$(remote_ssh_update_check_cache_file 2>/dev/null)" || return 0

remote_ssh_update_check_print_cached_message "$REMOTE_SSH_UPDATE_CHECK_CACHE_FILE"

if remote_ssh_update_check_is_stale "$REMOTE_SSH_UPDATE_CHECK_CACHE_FILE"; then
  remote_ssh_update_check_refresh_in_background "$REMOTE_SSH_UPDATE_CHECK_CACHE_FILE"
fi

unset REMOTE_SSH_UPDATE_CHECK_CACHE_FILE
