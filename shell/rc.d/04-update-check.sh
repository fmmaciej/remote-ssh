# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

# shellcheck source=/dev/null
. "$REMOTE_SHELL_DIR/update-check.lib.sh"

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
    remote-ssh update check --quiet --write-cache >/dev/null 2>&1 || true
  ) &
  pid=$!
  disown "$pid" 2>/dev/null || true
}

remote_ssh_update_check_enabled || return 0

REMOTE_SSH_UPDATE_CHECK_CACHE_FILE="$(remote_ssh_update_check_cache_file 2>/dev/null)" || return 0

if remote_ssh_update_check_is_stale "$REMOTE_SSH_UPDATE_CHECK_CACHE_FILE"; then
  remote_ssh_update_check_refresh_in_background "$REMOTE_SSH_UPDATE_CHECK_CACHE_FILE"
fi

unset REMOTE_SSH_UPDATE_CHECK_CACHE_FILE
