#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/tools/lib/env.sh"

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/bootstrap.lib.sh"

# Docelowo
# DEFAULT_TOOLS=(fd rg fzf yazi bat exa zoxide jq starship)
DEFAULT_TOOLS=(fd rg fzf bat yazi nvim starship exa)

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

  log_info "Bootstrap started."
  bootstrap_check_requirements
  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  bootstrap_shell_dir
  bootstrap_bin_dir
  bootstrap_dots_dir

  log_info "Bootstrap finished."
  bootstrap_print_post_install
}

main "$@"
