#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/tools/lib/env.sh"

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/install.lib.sh"

usage() {
  cat >&2 <<EOF
Usage: $0 [tool1 tool2 ...]
  - bez parametrow: instaluje domyslny zestaw: ${DEFAULT_TOOLS[*]}
  - z parametrami: instaluje tylko podane narzedzia
EOF
  exit 1
}

main() {
  local -a tools=("$@")
  (($# == 0)) && tools=("${DEFAULT_TOOLS[@]}")

  log_info "Begin."
  install_check_requirements
  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  install_shell_dir
  install_bin_dir
  install_dots_dir

  log_info "Done."
  install_print_post_install "$HOME/.local/share/remote-ssh"
}

main "$@"
