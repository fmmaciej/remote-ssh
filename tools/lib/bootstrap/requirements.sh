# shellcheck shell=bash

ensure_this_file_sourced

# : "${check_req_tools:?source tools/lib/bootstrap.sh first (check_req_tools missing)}"

bootstrap_check_requirements() {
  if ! check_req_tools; then
    log_error "Brakuje wymaganych narzędzi - przerwano bootstrap."
    exit 1
  fi
}
