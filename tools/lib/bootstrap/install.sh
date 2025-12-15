# shellcheck shell=bash

ensure_this_file_sourced

# Sprawdza, czy narzędzie jest już dostępne:
#   1) symlink:  ~/.local/bin/<tool>
#   2) jakakolwiek binarka w PATH: `command -v <tool>`
#
# Zwraca:
#   0 - jeśli tool jest dostępny (pomijamy instalację),
#   1 - jeśli trzeba instalować.
is_tool_installed() {
  local tool="$1"
  local local_bin="${BIN_DIR}/${tool}"

  if [[ "${FORCE:-0}" == "1" ]]; then
    log_info "FORCE=1"
    return 1
  fi

  # 1. ~/.local/bin
  if [[ -x "$local_bin" ]]; then
    log_info "'$tool' is installed in ${local_bin} - SKIPPING."
    return 0
  fi

  # 2. cokolwiek w PATH (np. z systemowego pakietu)
  if have "$tool"; then
    local existing
    existing="$(command -v "$tool")"
    log_info "'$tool' is present in PATH (${existing}) - SKIPPING."
    return 0
  fi

  # Trzeba instalować
  return 1
}

install_tool() {
  local tool="$1"
  local install_tool_sh="$TOOLS_DIR/install-tool.sh"

  is_tool_installed "$tool" && return 0

  "$install_tool_sh" "$tool" || { log_error "'$tool': installation failed."; return 1; }
}

install_tools() {
  local -a tools=("$@")

  mkdir -p "$INSTALL_PREFIX" "$BIN_DIR"

  local t
  for t in "${tools[@]}"; do install_tool "$t"; done
}
