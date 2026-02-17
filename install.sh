#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/tools/lib/env.sh"

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/install.lib.sh"

# Docelowo
# DEFAULT_TOOLS=(fd rg fzf yazi bat eza zoxide jq starship)
DEFAULT_TOOLS=(fd rg fzf bat yazi nvim starship eza)

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
  (( $# == 0 )) && tools=("${DEFAULT_TOOLS[@]}")

  log_info "install started."
  install_check_requirements
  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  install_shell_dir
  install_bin_dir
  install_dots_dir

  log_info "install finished."
  install_print_post_install
}

main "$@"
