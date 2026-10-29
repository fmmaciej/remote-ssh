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
    local __rs_wr_module="$1" __rs_wr_renderer="${2:-}"
    local __rs_wr_line __rs_wr_out_file __rs_wr_status=0

    __rs_wr_out_file="$(mktemp "${TMPDIR:-/tmp}/remote-ssh-welcome-module.XXXXXX" 2>/dev/null)" || return 0
    trap 'remote_ssh_welcome_remove_temp_file "$__rs_wr_out_file"' EXIT

    set +e

    if remote_ssh_welcome_debug_enabled; then
      if [[ -n "$__rs_wr_renderer" ]]; then
        (remote_ssh_welcome_bundled_render "$__rs_wr_renderer") >"$__rs_wr_out_file" </dev/null
      else
        "$__rs_wr_module" >"$__rs_wr_out_file" </dev/null
      fi
      __rs_wr_status=$?
    else
      if [[ -n "$__rs_wr_renderer" ]]; then
        (remote_ssh_welcome_bundled_render "$__rs_wr_renderer") >"$__rs_wr_out_file" 2>/dev/null </dev/null
      else
        "$__rs_wr_module" >"$__rs_wr_out_file" 2>/dev/null </dev/null
      fi
      __rs_wr_status=$?
    fi

    while IFS= read -r __rs_wr_line || [[ -n "$__rs_wr_line" ]]; do
      remote_ssh_welcome_print_line "$__rs_wr_line"
    done <"$__rs_wr_out_file"

    if ((__rs_wr_status != 0)) && remote_ssh_welcome_debug_enabled; then
      printf 'remote-ssh welcome: module failed: %s (exit %s)\n' "$__rs_wr_module" "$__rs_wr_status" >&2
    fi

    return "$__rs_wr_status"
  )
}

# Both the ordinary user path and bundled fallback retain the old launch scope:
# exported BASHOPTS sees nullglob on; run_module disables errexit before exec.
remote_ssh_welcome_run_external_paths() {
  local __rs_wr_path __rs_wr_had_nullglob=0

  if shopt -q nullglob; then __rs_wr_had_nullglob=1; fi
  shopt -s nullglob
  for __rs_wr_path in "$@"; do
    [[ -f "$__rs_wr_path" && -x "$__rs_wr_path" ]] || continue
    remote_ssh_welcome_run_module "$__rs_wr_path" || true
  done
  if ((__rs_wr_had_nullglob == 0)); then shopt -u nullglob; fi
  return 0
}

remote_ssh_welcome_run_dir() {
  local __rs_wr_dir="$1" __rs_wr_path __rs_wr_count=0
  local -a __rs_wr_paths=()

  [[ -d "$__rs_wr_dir" ]] || return 0
  for __rs_wr_path in "$__rs_wr_dir"/*; do
    [[ -f "$__rs_wr_path" && -x "$__rs_wr_path" ]] || continue
    __rs_wr_paths[__rs_wr_count]="$__rs_wr_path"
    __rs_wr_count=$((__rs_wr_count + 1))
  done
  ((__rs_wr_count > 0)) || return 0
  remote_ssh_welcome_run_external_paths "${__rs_wr_paths[@]}"
}

remote_ssh_welcome_run_bundled() {
  local __rs_wr_dir="$1" __rs_wr_path __rs_wr_count=0 __rs_wr_qualified=1
  local __rs_wr_loaded_dir __rs_wr_selected_dir __rs_wr_worker __rs_wr_worker_status
  local -a __rs_wr_paths=()

  [[ -d "$__rs_wr_dir" ]] || return 0
  # Filtering the unmatched literal glob gives the same empty-directory result
  # without changing caller options during discovery.
  for __rs_wr_path in "$__rs_wr_dir"/*; do
    [[ -f "$__rs_wr_path" && -x "$__rs_wr_path" ]] || continue
    __rs_wr_paths[__rs_wr_count]="$__rs_wr_path"
    __rs_wr_count=$((__rs_wr_count + 1))
    remote_ssh_welcome_bundled_renderer "$__rs_wr_dir" "$__rs_wr_path" >/dev/null || __rs_wr_qualified=0
  done
  ((__rs_wr_count > 0)) || return 0

  __rs_wr_loaded_dir="$(remote_ssh_welcome_bundled_shell_dir 2>/dev/null)" || __rs_wr_qualified=0
  __rs_wr_selected_dir="$(builtin cd -P -- "$__rs_wr_dir/.." 2>/dev/null && builtin pwd -P)" || __rs_wr_qualified=0
  [ "$__rs_wr_loaded_dir" = "$__rs_wr_selected_dir" ] || __rs_wr_qualified=0
  __rs_wr_worker="$__rs_wr_loaded_dir/welcome/bundled-runner.sh"
  [[ -f "$__rs_wr_worker" && -x "$__rs_wr_worker" ]] || __rs_wr_qualified=0
  [[ -z "${BASH_ENV:-}" ]] || __rs_wr_qualified=0
  remote_ssh_welcome_bundled_options_unexported || __rs_wr_qualified=0

  if ((__rs_wr_qualified == 0)); then
    remote_ssh_welcome_run_external_paths "${__rs_wr_paths[@]}"
    return 0
  fi

  if remote_ssh_welcome_debug_enabled; then
    if "$__rs_wr_worker" -- "${__rs_wr_paths[@]}"; then
      __rs_wr_worker_status=0
    else
      __rs_wr_worker_status=$?
    fi
  elif "$__rs_wr_worker" -- "${__rs_wr_paths[@]}" 2>/dev/null; then
    __rs_wr_worker_status=0
  else
    __rs_wr_worker_status=$?
  fi

  if ((__rs_wr_worker_status == 125)); then
    # Only worker preflight may return 125, before any renderer has started.
    remote_ssh_welcome_run_external_paths "${__rs_wr_paths[@]}"
  elif ((__rs_wr_worker_status != 0)) && remote_ssh_welcome_debug_enabled; then
    printf 'remote-ssh welcome: bundled worker failed (exit %s)\n' "$__rs_wr_worker_status" >&2
  fi
  return 0
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

    remote_ssh_welcome_run_bundled "$bundled_dir"
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
