# shellcheck shell=bash

ensure_this_file_sourced

detect_os() {
  local n
  n="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  # pomijamy windows
  [[ $n =~ windows|msvc ]] && {
    echo ""
    return
  }
  [[ $n =~ apple-darwin|darwin|macos|osx ]] && {
    echo "darwin"
    return
  }
  [[ $n =~ linux ]] && {
    echo "linux"
    return
  }

  echo ""
}

detect_arch() {
  local n
  n="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  [[ $n =~ aarch64|arm64 ]] && {
    echo "aarch64"
    return
  }
  [[ $n =~ x86_64|amd64|x64 ]] && {
    echo "x86_64"
    return
  }

  echo ""
}

detect_libc() {
  local n
  n="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  [[ $n =~ musl ]] && {
    echo "musl"
    return
  }
  [[ $n =~ gnu|glibc ]] && {
    echo "gnu"
    return
  }

  # jeśli linuxowe releasy nie mówią wprost, zwykle to gnu
  echo "gnu"
}
