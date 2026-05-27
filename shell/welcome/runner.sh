# shellcheck shell=bash

remote_ssh_welcome_enabled() {
  case "${REMOTE_SSH_WELCOME:-1}" in
    0 | false | no | off) return 1 ;;
    *) return 0 ;;
  esac
}

remote_ssh_welcome_user_enabled() {
  case "${REMOTE_SSH_WELCOME_USER:-1}" in
    0 | false | no | off) return 1 ;;
    *) return 0 ;;
  esac
}

remote_ssh_welcome_print_line() {
  if printf '%s\n' "$1" 2>/dev/null >/dev/tty; then
    return 0
  fi

  printf '%s\n' "$1"
}

remote_ssh_welcome_note_issue() {
  local issue="$1" seen

  [[ -n "$issue" ]] || return 0
  if ! remote_ssh_welcome_issue_allowed "$issue"; then
    if remote_ssh_welcome_debug_enabled; then
      printf 'remote-ssh welcome: ignoring unknown issue: %s\n' "$issue" >&2
    fi
    return 0
  fi
  for seen in "${REMOTE_SSH_WELCOME_ISSUES[@]}"; do
    [[ "$seen" == "$issue" ]] && return 0
  done
  REMOTE_SSH_WELCOME_ISSUES+=("$issue")
}

remote_ssh_welcome_remove_temp_file() {
  local file="${1:-}"

  [[ -n "$file" ]] && rm -f "$file"
}

remote_ssh_welcome_cleanup_issues() {
  local file="${1:-}"

  remote_ssh_welcome_remove_temp_file "$file"
  unset REMOTE_SSH_WELCOME_ISSUES_FILE
  unset REMOTE_SSH_WELCOME_ISSUES
}

remote_ssh_welcome_run_module() {
  (
    local module="$1" line out_file status=0

    out_file="$(mktemp "${TMPDIR:-/tmp}/remote-ssh-welcome-module.XXXXXX" 2>/dev/null)" || return 0
    trap 'remote_ssh_welcome_remove_temp_file "$out_file"' EXIT

    set +e

    if remote_ssh_welcome_debug_enabled; then
      "$module" >"$out_file" </dev/null
      status=$?
    else
      "$module" >"$out_file" 2>/dev/null </dev/null
      status=$?
    fi

    while IFS= read -r line || [[ -n "$line" ]]; do
      remote_ssh_welcome_print_line "$line"
    done <"$out_file"

    if ((status != 0)) && remote_ssh_welcome_debug_enabled; then
      printf 'remote-ssh welcome: module failed: %s (exit %s)\n' "$module" "$status" >&2
    fi

    return "$status"
  )
}

remote_ssh_welcome_run_dir() {
  local dir="$1" module restore_nullglob

  [[ -d "$dir" ]] || return 0

  restore_nullglob="$(shopt -p nullglob || true)"
  shopt -s nullglob
  for module in "$dir"/*; do
    [[ -f "$module" && -x "$module" ]] || continue
    remote_ssh_welcome_run_module "$module" || true
  done
  eval "$restore_nullglob"
}

remote_ssh_welcome_user_dir() {
  if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
    printf '%s/remote-ssh/welcome.d\n' "$XDG_CONFIG_HOME"
  elif [[ -n "${HOME:-}" ]]; then
    printf '%s/.config/remote-ssh/welcome.d\n' "$HOME"
  else
    return 1
  fi
}

remote_ssh_welcome_collect_issues() {
  local file="$1" issue

  [[ -r "$file" ]] || return 0
  while IFS= read -r issue || [[ -n "$issue" ]]; do
    remote_ssh_welcome_note_issue "$issue"
  done <"$file"
}

remote_ssh_welcome_next_command() {
  local issue count

  count="${#REMOTE_SSH_WELCOME_ISSUES[@]}"
  ((count > 0)) || return 1
  ((count == 1)) || {
    printf 'remote-ssh doctor\n'
    return 0
  }

  issue="${REMOTE_SSH_WELCOME_ISSUES[0]}"
  case "$issue" in
    update) printf 'remote-ssh update\n' ;;
    tools) printf 'remote-ssh install\n' ;;
    scripts) printf 'remote-ssh guide scripts\n' ;;
    sw) printf 'remote-ssh git status\n' ;;
    *) printf 'remote-ssh doctor\n' ;;
  esac
}

remote_ssh_welcome_print_next() {
  local command line

  command="$(remote_ssh_welcome_next_command)" || return 0
  line="$(printf 'next:    %s' "$command")"

  remote_ssh_welcome_print_line ""
  if remote_ssh_welcome_color_enabled; then
    remote_ssh_welcome_print_line "$(printf '\033[31m%s\033[0m' "$line")"
  else
    remote_ssh_welcome_print_line "$line"
  fi
}

remote_ssh_welcome_run() {
  local status

  unset REMOTE_SSH_WELCOME_ISSUES_FILE
  unset REMOTE_SSH_WELCOME_ISSUES

  (
    local bundled_dir user_dir issues_file

    trap 'remote_ssh_welcome_cleanup_issues "$issues_file"' EXIT

    REMOTE_SSH_WELCOME_ISSUES=()
    issues_file="$(mktemp "${TMPDIR:-/tmp}/remote-ssh-welcome-issues.XXXXXX" 2>/dev/null || true)"
    if [[ -n "$issues_file" ]]; then
      export REMOTE_SSH_WELCOME_ISSUES_FILE="$issues_file"
    fi
    export REMOTE_SSH_WELCOME_COLOR

    bundled_dir="$(remote_ssh_welcome_bundled_dir)"
    user_dir="$(remote_ssh_welcome_user_dir 2>/dev/null || true)"

    remote_ssh_welcome_run_dir "$bundled_dir"
    if remote_ssh_welcome_user_enabled && [[ -n "$user_dir" ]]; then
      remote_ssh_welcome_run_dir "$user_dir"
    fi
    [[ -n "$issues_file" ]] && remote_ssh_welcome_collect_issues "$issues_file"
    remote_ssh_welcome_print_next
  )
  status=$?

  unset REMOTE_SSH_WELCOME_ISSUES_FILE
  unset REMOTE_SSH_WELCOME_ISSUES
  return "$status"
}

remote_ssh_welcome_main() {
  case $- in
    *i*) ;;
    *) return 0 ;;
  esac

  unset REMOTE_SSH_WELCOME_ISSUES_FILE
  unset REMOTE_SSH_WELCOME_ISSUES

  remote_ssh_welcome_enabled || return 0

  remote_ssh_welcome_run || true
  unset REMOTE_SSH_WELCOME_ISSUES_FILE
  unset REMOTE_SSH_WELCOME_ISSUES
  return 0
}
