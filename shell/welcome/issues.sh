# shellcheck shell=bash

remote_ssh_welcome_issue_allowed() {
  case "${1:-}" in
    update | tools | scripts | sw | doctor) return 0 ;;
    *) return 1 ;;
  esac
}

remote_ssh_welcome_issue() {
  local issue="$1"

  [[ -n "$issue" ]] || return 0
  if ! remote_ssh_welcome_issue_allowed "$issue"; then
    if remote_ssh_welcome_debug_enabled; then
      printf 'remote-ssh welcome: ignoring unknown issue: %s\n' "$issue" >&2
    fi
    return 0
  fi
  [[ -n "${REMOTE_SSH_WELCOME_ISSUES_FILE:-}" ]] || return 0
  printf '%s\n' "$issue" >>"$REMOTE_SSH_WELCOME_ISSUES_FILE" 2>/dev/null || true
}
