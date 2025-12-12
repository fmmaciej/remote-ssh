# shellcheck shell=bash

# ensure_sourced <label>
#
# Sprawdza, czy plik jest ładowany przez 'source', nie uruchamiany.
# label - nazwa do komunikatu, np. "env.sh" albo "aliases.sh".
ensure_sourced() {
  local label="$1"

  if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    printf 'ERROR: %s must be sourced, not executed.\n' "$label" >&2
    exit 1
  fi
}

ensure_this_file_sourced() {
    ensure_sourced "$(basename "${BASH_SOURCE[0]}")"
}

# load_once <VAR_NAME>
#
# zmienna VAR_NAME jest już ustawiona:
#   - tak -> zwraca 1
#   - nie -> ustawia ją na "1" i zwraca 0
#
# Uwaga: niczego nie zwraca z pliku - tylko mówi,
# czy to pierwsze ładowanie.
load_once() {
  local guard_var="$1"

  # Załadowane
  [ -n "${!guard_var:-}" ] && return 1

  # ustaw VAR=1 dynamicznie
  printf -v "$guard_var" '%s' 1
  return 0
}

init_lib() {
  local guard_var="$1"
  local label="$2"

  ensure_sourced "$label"
  load_once "$guard_var"
}
