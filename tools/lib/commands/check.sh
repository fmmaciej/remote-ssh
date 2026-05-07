# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_check_usage() {
  cat <<'EOF' >&2
Usage: remote-ssh check [--strict] [tool ...]

Reports pinned remote-ssh tools, local installation symlinks, and the binary
that currently wins in PATH.

Without tool arguments, checks the default install set.
With --strict, exits non-zero when a tool is missing, stale, external-only,
shadowed, or otherwise not managed by remote-ssh.
EOF
}

remote_ssh_cmd_check_report_tool() {
  local tool="$1" def_dir="$2"
  local alias_record alias_name alias_path

  remote_ssh_tool_status_load "$tool" "$def_dir"

  printf '%s\n' "$REMOTE_SSH_TOOL_STATUS_TOOL_NAME"
  printf '  %-10s %s\n' 'expected:' "$REMOTE_SSH_TOOL_STATUS_EXPECTED"
  printf '  %-10s %s\n' 'local:' "$(remote_ssh_tool_status_print_path_value "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN")"
  printf '  %-10s %s\n' 'target:' "$REMOTE_SSH_TOOL_STATUS_TARGET"
  printf '  %-10s %s\n' 'path:' "$(remote_ssh_tool_status_print_path_value "$REMOTE_SSH_TOOL_STATUS_PATH_BIN")"
  printf '  %-10s %s\n' 'status:' "$REMOTE_SSH_TOOL_STATUS_STATUS"

  if ((${#REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS[@]} > 0)); then
    for alias_record in "${REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS[@]}"; do
      alias_name="${alias_record%%|*}"
      alias_path="${alias_record#*|}"
      printf '  %-10s %s -> %s\n' \
        'alias:' \
        "$alias_name" \
        "$(remote_ssh_tool_status_print_path_value "$alias_path")"
    done
  fi

  return "$REMOTE_SSH_TOOL_STATUS_PROBLEM"
}

remote_ssh_cmd_check_main() {
  remote_ssh_cmd_require_install_libs

  local strict=0 arg tool def_dir problems=0
  local -a tools=()

  for arg in "$@"; do
    case "$arg" in
      --strict) strict=1 ;;
      -h|--help)
        remote_ssh_cmd_check_usage
        return 0
        ;;
      -*)
        remote_ssh_cmd_check_usage
        return 1
        ;;
      *) tools+=("$arg") ;;
    esac
  done

  if ((${#tools[@]} == 0)); then
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && tools+=("$tool")
    done < <(current_default_tools)
  fi

  def_dir="$TOOLS_DIR/defs"

  printf 'remote-ssh check\n\n'
  printf 'Install paths\n'
  printf '  %-10s %s\n' 'prefix:' "$INSTALL_PREFIX"
  printf '  %-10s %s\n' 'bin:' "$INSTALL_BIN_DIR"
  printf '\nTools\n'

  for tool in "${tools[@]}"; do
    if ! remote_ssh_cmd_check_report_tool "$tool" "$def_dir"; then
      problems=1
    fi
  done

  if ((strict == 1 && problems == 1)); then
    return 1
  fi
}
