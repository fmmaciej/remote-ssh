# shellcheck shell=bash

# Jeśli zwróci błąd (zmienna już ustawiona), przerwij dalsze ładowanie pliku.
ensure_this_file_sourced

# log_info "message"
log() {
  printf '%s\n' "$*" >&2
}

# log_info "message"
log_info() {
  printf '[INFO] %s\n' "$*" >&2
}

# log_debug "message"
# Debug działa tylko jeśli DEBUG=1
log_debug() {
  if [[ "${DEBUG:-0}" == "1" ]]; then
    printf '[DEBUG] %s\n' "$*" >&2
  fi
}

# log_error "message"
log_error() {
  printf '[ERROR] %s\n' "$*" >&2
}
