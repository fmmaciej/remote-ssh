# shellcheck shell=bash

remote_ssh_welcome_print_update() {
  local cache_file status checked_at_text label cache_readable=0

  if ! remote_ssh_update_check_enabled; then
    printf 'update:  disabled\n'
    return 0
  fi

  cache_file="$(remote_ssh_update_check_cache_file 2>/dev/null || true)"
  if [[ -n "$cache_file" && -r "$cache_file" ]]; then
    cache_readable=1
    status="$(remote_ssh_update_check_cache_get "$cache_file" status 2>/dev/null || true)"
    checked_at_text="$(remote_ssh_update_check_cache_get "$cache_file" checked_at_text 2>/dev/null || true)"
  fi

  case "$status" in
    current)
      label="current"
      checked_at_text="${checked_at_text:-unknown}"
      ;;
    update-available)
      label="available"
      checked_at_text="${checked_at_text:-unknown}"
      remote_ssh_welcome_issue update
      ;;
    error)
      label="unavailable"
      checked_at_text="${checked_at_text:-unknown}"
      remote_ssh_welcome_issue doctor
      ;;
    '')
      if ((cache_readable == 1)); then
        label="unavailable"
        checked_at_text="${checked_at_text:-unknown}"
        remote_ssh_welcome_issue doctor
      else
        label="unknown"
        checked_at_text="never"
      fi
      ;;
    *)
      label="unavailable"
      checked_at_text="${checked_at_text:-unknown}"
      remote_ssh_welcome_issue doctor
      ;;
  esac

  printf 'update:  %s (checked: %s)\n' "$label" "$checked_at_text"
}
