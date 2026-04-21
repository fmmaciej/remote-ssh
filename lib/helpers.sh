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
  [[ -d $dir ]] || return 0

  case ":$PATH:" in
  *":$dir:"*) ;;
  *)
    PATH="$dir:$PATH"
    ;;
  esac
}

remote_source_file() {
  local file="$1"

  [[ -r "$file" ]] || return 0
  # shellcheck disable=SC1090
  . "$file"
}

remote_source_dir() {
  local dir="$1"
  local f

  [[ -d "$dir" ]] || return 0

  case "${BASH_VERSION:+bash}${ZSH_VERSION:+zsh}" in
    bash)
      local restore_nullglob
      restore_nullglob="$(shopt -p nullglob || true)"
      shopt -s nullglob
      for f in "$dir"/*.sh; do
        remote_source_file "$f"
      done
      eval "$restore_nullglob"
      ;;
    zsh)
      setopt local_options null_glob
      for f in "$dir"/*.sh; do
        remote_source_file "$f"
      done
      ;;
  esac
}

remote_os_id() {
  case "$(uname -s 2>/dev/null)" in
  Linux) echo "linux" ;;
  Darwin) echo "darwin" ;;
  *)
    uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]'
    ;;
  esac
}

remote_hostname_short() {
  hostname -s 2>/dev/null || hostname 2>/dev/null || true
}

remote_git_config_add() {
  local key="${1:?git config key required}"
  local value="${2:?git config value required}"
  local n="${GIT_CONFIG_COUNT:-0}"

  export "GIT_CONFIG_KEY_${n}=$key"
  export "GIT_CONFIG_VALUE_${n}=$value"
  export GIT_CONFIG_COUNT="$((n + 1))"
}

fetch_json() {
  local api="${1:?api url required}"
  local token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

  if [[ -n $token && $api == https://api.github.com/* ]]; then
    curl -fsS \
      -H "Authorization: Bearer $token" \
      -H "Accept: application/vnd.github+json" \
      "$api"
  else
    curl -fsS "$api"
  fi
}

remote_atuin_debug() {
    echo "shell=${SHELL:-}"
    echo "interactive_flags=$-"
    echo "BASH_VERSION=${BASH_VERSION:-}"
    echo "ZSH_VERSION=${ZSH_VERSION:-}"
    echo "ATUIN_CONFIG_DIR=${ATUIN_CONFIG_DIR:-}"
    echo "bash_preexec_imported=${bash_preexec_imported:-}"
    if command -v atuin >/dev/null 2>&1; then
        echo "atuin=found"
    else
        echo "atuin=missing"
    fi
}
