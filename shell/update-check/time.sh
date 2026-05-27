# shellcheck shell=bash

remote_ssh_update_check_interval() {
  local interval="${REMOTE_SSH_UPDATE_CHECK_INTERVAL:-86400}"

  case "$interval" in
    '' | *[!0-9]*) printf '86400\n' ;;
    *) printf '%s\n' "$interval" ;;
  esac
}

remote_ssh_update_check_now() {
  date +%s 2>/dev/null
}

remote_ssh_update_check_checked_at_text() {
  date '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || date 2>/dev/null || printf 'unknown'
}

remote_ssh_update_check_is_stale() {
  local file="$1" now checked_at interval

  now="$(remote_ssh_update_check_now)" || return 1
  checked_at="$(remote_ssh_update_check_cache_get "$file" checked_at 2>/dev/null || true)"
  interval="$(remote_ssh_update_check_interval)"

  case "$checked_at" in
    '' | *[!0-9]*) return 0 ;;
  esac

  ((checked_at <= now)) || return 0
  ((now - checked_at >= interval))
}
