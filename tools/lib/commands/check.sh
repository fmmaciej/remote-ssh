# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_check_usage() {
  cat <<'EOF' >&2
Usage: remote-ssh check [--strict] [tool ...]

Reports pinned remote-ssh tools, local installation symlinks, and the binary
that currently wins in PATH.

Without tool arguments, checks the saved expected tool set from:
  ${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools

With --strict, exits non-zero when a tool is missing, stale, external-only,
shadowed, or otherwise not managed by remote-ssh.
EOF
}

remote_ssh_cmd_check_report_tool() {
  local tool="$1" def_dir="$2"
  local alias_record alias_name alias_rest alias_path alias_target alias_status

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
      alias_rest="${alias_record#*|}"
      alias_path="${alias_rest%%|*}"
      alias_rest="${alias_rest#*|}"
      alias_target="${alias_rest%%|*}"
      alias_status="${alias_rest#*|}"
      printf '  %-10s %s -> %s status=%s target=%s\n' \
        'alias:' \
        "$alias_name" \
        "$(remote_ssh_tool_status_print_path_value "$alias_path")" \
        "$alias_status" \
        "$alias_target"
    done
  fi

  return "$REMOTE_SSH_TOOL_STATUS_PROBLEM"
}

remote_ssh_cmd_check_main() {
  remote_ssh_cmd_require_install_libs

  local strict=0 arg tool def_dir problems=0
  local -a tools=()

  REMOTE_SSH_UNKNOWN_TOOLS=()
  REMOTE_SSH_UNSUPPORTED_TOOLS=()

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
    if ! read_expected_tools_for_current_platform; then
      printf 'No expected tools config found: %s\n' "$(expected_tools_file)" >&2
      printf 'Run: remote-ssh install --full --yes\n' >&2
      printf 'Or install a selected set, for example: remote-ssh install fd rg fzf\n' >&2
      return 1
    fi
    tools=("${REMOTE_SSH_EXPECTED_TOOLS[@]}")
  fi

  ((${#tools[@]} > 0)) || {
    printf 'No supported expected tools configured for this platform.\n' >&2
    return 1
  }

  def_dir="$TOOLS_DIR/defs"

  printf 'remote-ssh check\n\n'
  printf 'Install paths\n'
  printf '  %-10s %s\n' 'prefix:' "$INSTALL_PREFIX"
  printf '  %-10s %s\n' 'bin:' "$INSTALL_BIN_DIR"

  if ((${#REMOTE_SSH_UNKNOWN_TOOLS[@]} > 0)); then
    printf '\nWarnings\n'
    printf '  unknown expected tool: %s\n' "${REMOTE_SSH_UNKNOWN_TOOLS[@]}"
  fi

  if ((${#REMOTE_SSH_UNSUPPORTED_TOOLS[@]} > 0)); then
    printf '\nSkipped unsupported expected tools\n'
    printf '  %s\n' "${REMOTE_SSH_UNSUPPORTED_TOOLS[@]}"
  fi

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
