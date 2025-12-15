# shellcheck shell=bash

# Jeśli zwróci błąd (zmienna już ustawiona), przerwij dalsze ładowanie pliku.
ensure_this_file_sourced

# Sprawdza, czy komenda istnieje w PATH.
have() {
  command -v "$1" >/dev/null 2>&1
}

# Bezpiecznie dodaje katalog na początek ścieżki PATH (bez duplikatów).
path_prepend() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0

  case ":$PATH:" in
    *":$dir:"*)
      ;;
    *)
      PATH="$dir:$PATH"
      ;;
  esac
}

fetch_json() {
  local api="${1:?api url required}"
  curl -fsS "$api"
}
