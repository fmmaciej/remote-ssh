# shellcheck shell=bash

ensure_this_file_sourced

# : "${check_req_tools:?source tools/lib/install.lib.sh first (check_req_tools missing)}"

install_check_requirements() {
  if ! check_req_tools; then
    log_error "Brakuje wymaganych narzędzi - przerwano install."
    exit 1
  fi
}
