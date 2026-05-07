# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_check_usage() {
  cat <<'EOF' >&2
Usage: remote-ssh check [--strict] [tool ...]

Reports pinned remote-ssh tools, local installation symlinks, and the binary
that currently wins in PATH.

Without tool arguments, checks the default install set.
With --strict, exits non-zero when a tool is missing, stale, external-only,
shadowed, or otherwise not managed by remote-ssh.
EOF
}

remote_ssh_check_print_path_value() {
  local value="$1"

  if [[ -n "$value" ]]; then
    printf '%s\n' "$value"
  else
    printf '[missing]\n'
  fi
}

remote_ssh_check_read_link_target() {
  local path="$1"

  if [[ -L "$path" ]]; then
    readlink "$path"
  else
    printf '%s\n' "$path"
  fi
}

remote_ssh_check_target_matches_version() {
  local target="$1" tool="$2" version="$3"

  case "$target" in
    "$INSTALL_PREFIX/${tool}-${version}/"* | "$INSTALL_PREFIX/${tool}-${version}".*/*)
      return 0
      ;;
  esac

  return 1
}

remote_ssh_check_report_tool() {
  local tool="$1" def_dir="$2"
  local local_bin path_bin local_target status alias_name
  local tool_problem=0

  load_defs "$def_dir" "$tool"

  local_bin="${INSTALL_BIN_DIR}/${TOOL_NAME}"
  path_bin="$(command -v "$TOOL_NAME" 2>/dev/null || true)"
  status="missing"

  # VERSION is assigned by load_defs.
  # shellcheck disable=SC2153
  if [[ -x "$local_bin" ]]; then
    local_target="$(remote_ssh_check_read_link_target "$local_bin")"
    if ! [[ -L "$local_bin" ]]; then
      status="unmanaged-local"
      tool_problem=1
    elif ! remote_ssh_check_target_matches_version "$local_target" "$TOOL_NAME" "$VERSION"; then
      status="stale-local"
      tool_problem=1
    elif [[ "$path_bin" == "$local_bin" ]]; then
      status="ok"
    elif [[ -n "$path_bin" ]]; then
      status="path-shadowed"
      tool_problem=1
    else
      status="local-not-in-path"
      tool_problem=1
    fi
  elif [[ -n "$path_bin" ]]; then
    local_target="[missing]"
    status="external-only"
    tool_problem=1
  else
    local_target="[missing]"
    tool_problem=1
  fi

  printf '%s\n' "$TOOL_NAME"
  printf '  %-10s %s\n' 'expected:' "VERSION=${VERSION} ${GH_REPO}@${RELEASE_TAG}"
  printf '  %-10s %s\n' 'local:' "$(remote_ssh_check_print_path_value "$local_bin")"
  printf '  %-10s %s\n' 'target:' "$local_target"
  printf '  %-10s %s\n' 'path:' "$(remote_ssh_check_print_path_value "$path_bin")"
  printf '  %-10s %s\n' 'status:' "$status"

  if ((${#BINARY_ALIASES[@]} > 0)); then
    for alias_name in "${BINARY_ALIASES[@]}"; do
      printf '  %-10s %s -> %s\n' \
        'alias:' \
        "$alias_name" \
        "$(remote_ssh_check_print_path_value "$(command -v "$alias_name" 2>/dev/null || true)")"
    done
  fi

  return "$tool_problem"
}

remote_ssh_check_main() {
  local strict=0 arg tool def_dir problems=0
  local -a tools=()

  for arg in "$@"; do
    case "$arg" in
      --strict) strict=1 ;;
      -h|--help)
        remote_ssh_check_usage
        return 0
        ;;
      -*)
        remote_ssh_check_usage
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
    if ! remote_ssh_check_report_tool "$tool" "$def_dir"; then
      problems=1
    fi
  done

  if ((strict == 1 && problems == 1)); then
    return 1
  fi
}
