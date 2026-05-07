# shellcheck shell=bash

ensure_this_file_sourced

is_tool_installed() {
  local tool="$1"
  local expected_version="${2:-}"
  local local_bin="${INSTALL_BIN_DIR}/${tool}"
  local target existing

  if [[ ${FORCE:-0} == "1" ]]; then
    log_info "FORCE=1"
    return 1
  fi

  if [[ -x $local_bin ]]; then
    if [[ -z $expected_version ]]; then
      log_info "'$tool' is installed in ${local_bin} - SKIPPING."
      return 0
    fi

    if [[ -L $local_bin ]]; then
      target="$(readlink "$local_bin")"
      case "$target" in
        "$INSTALL_PREFIX/${tool}-${expected_version}/"* | "$INSTALL_PREFIX/${tool}-${expected_version}".*/*)
          log_info "'$tool' ${expected_version} is installed in ${local_bin} - SKIPPING."
          return 0
          ;;
      esac

      log_info "'$tool' is installed in ${local_bin}, but target is not VERSION=${expected_version}: ${target}"
      return 1
    fi

    log_info "'$tool' exists in ${local_bin}, but is not a managed version symlink - installing pinned VERSION=${expected_version}."
    return 1
  fi

  if have "$tool"; then
    existing="$(command -v "$tool")"
    log_info "'$tool' is present in PATH (${existing}), but remote-ssh pinned VERSION=${expected_version} is not installed."
  fi

  return 1
}

install_tool() {
  local tool="$1"
  local install_tool_sh="$TOOLS_DIR/install-tool.sh"
  local def_dir="$TOOLS_DIR/defs"

  load_defs "$def_dir" "$tool"

  is_tool_installed "$TOOL_NAME" "$VERSION" && return 0

  "$install_tool_sh" "$tool" || {
    log_error "'$tool': installation failed."
    return 1
  }
}

install_tools() {
  local -a tools=("$@")

  mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"

  local t
  for t in "${tools[@]}"; do install_tool "$t"; done
}
