#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/tools/lib/env.sh"

# Docelowo
# DEFAULT_TOOLS=(fd rg fzf yazi bat exa zoxide jq starship)
DEFAULT_TOOLS=(fd rg fzf yazi nvim starship)

usage() {
  cat >&2 <<EOF
Usage: $0 [tool1 tool2 ...]
  - bez parametrow: instaluje domyslny zestaw: ${DEFAULT_TOOLS[*]}
  - z parametrami: instaluje tylko podane narzedzia
EOF
  exit 1
}

check_requirements() {
  if ! check_req_tools; then
    log_error "Brakuje wymaganych narzedzi - przerwano bootstrap."

    exit 1
  fi
}

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

  # FOrce
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

  "$install_tool_sh" "$tool" || {
    log_error "'$tool': installation failed."

    return 1
  }
}

install_tools() {
  local tools=("$@")

  mkdir -p "$INSTALL_PREFIX" "$BIN_DIR"

  for t in "${tools[@]}"; do
    install_tool "$t"
  done
}

shell_dir() {
  log_info "  shell/..."

  [ -f "$SHELL_DIR/rc.sh" ] && chmod +x "$SHELL_DIR/rc.sh"

  # [ -d "$SHELL_DIR" ] && find "$SHELL_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

bin_dir() {
  log_info "  bin/..."

  [ -d "$BIN_DIR" ] && find "$BIN_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

dots_dir() {
  log_info "  dots/..."

  [ -f "$DOTS_DIR/starship.toml" ] && log_info "    Found dots/starship.toml"
}

print_post_install() {
  local template_file="$REPO_DIR/POST_INSTALL.txt"

  if [[ -f "$template_file" ]]; then
    echo
    echo "================= POST INSTALL ================="
    echo
    sed "s|@INSTALL_DIR@|$REPO_DIR|g" "$template_file"
    echo
    echo "================================================"
    echo
  fi
}

main() {
  local tools=("$@")

  (( $# == 0 )) && tools=("${DEFAULT_TOOLS[@]}")

  log_info "Bootstrap started."
  check_requirements
  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  shell_dir
  bin_dir
  dots_dir

  log_info "Bootstrap finished."

  print_post_install
}

main "$@"
