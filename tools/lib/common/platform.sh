# shellcheck shell=bash

ensure_this_file_sourced

normalize_raw_arch() {
  case "$1" in
    arm64|aarch64) echo "aarch64" ;;
    x86_64|amd64)  echo "x86_64" ;;
    *)             echo "$1" ;;
  esac
}

# echo: "<raw_os>|<raw_arch>"
detect_platform() {
  local raw_arch raw_os

  raw_arch="$(uname -m)"
  raw_os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  raw_arch="$(normalize_raw_arch "$raw_arch")"

  printf '%s|%s\n' "$raw_os" "$raw_arch"
}

# echo: "gnu" / "musl" / "any"
detect_libc() {
  local raw_os="$1"

  [[ "$raw_os" == "linux" ]] || { echo "any"; return 0; }

  if have ldd && ldd --version 2>&1 | grep -qi musl; then
    echo "musl"
  else
    echo "gnu"
  fi
}
