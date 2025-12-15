# shellcheck shell=bash

ensure_this_file_sourced

# ===========================================
# map_arch <arch_kind> <raw_arch>
#
# <arch_kind> pochodzi z defs/<tool>.sh i określa schemat mapowania.
#
# Dostępne schematy:
#   amd64_arm64       -> fzf
#   x86_64_aarch64    -> ripgrep, fd
#   ""                -> identycznie jak x86_64_aarch64
#   anything_else     -> brak mapowania, echo "$raw_arch"
#
# Zwraca (echo):
#   Zmapowaną architekturę (np. amd64, arm64, x86_64, aarch64).
#
# Nie modyfikuje globalnych zmiennych.
# ===========================================
map_arch() {
  local kind="$1"
  local arch="$2"

  case "$kind" in
    # fzf
    amd64_arm64)
      case "$arch" in
        x86_64)         echo "amd64" ;;
        aarch64|arm64)  echo "arm64" ;;
        *)              echo "$arch" ;;
      esac
      ;;

    # ripgrep i fd
    x86_64_aarch64)
      case "$arch" in
        x86_64)         echo "x86_64" ;;
        aarch64|arm64)  echo "aarch64" ;;
        *)              echo "$arch" ;;
      esac
      ;;

    # nvim: x86_64 / arm64
    x86_64_arm64)
      case "$arch" in
        x86_64)         echo "x86_64" ;;
        aarch64|arm64)  echo "arm64" ;;
        *)              echo "$arch" ;;
      esac
      ;;

    # Nie zmieniamy nazwy
    *)
      echo "Nieznany ARCH_KIND: $kind" >&2
      return 1
      ;;
  esac
}

# ===========================================
# map_os <os_kind> <raw_os>
#
# Dostępne schematy:
#   linux_darwin      -> zwraca: linux, darwin
#   linux_macos       -> zwraca: linux, macos
#   rust_triple       -> zwraca: unknown-linux-gnu, apple-darwin
#   rust_musl         -> zwraca: unknown-linux-musl, apple-darwin
#   ""                -> działa jak linux_darwin
#   anything_else     -> echo "$raw_os"
#
# Zwraca (echo):
#   Zmapowaną nazwę systemu do użycia w nazwie assetu.
#
# Nie modyfikuje globalnych zmiennych.
# ===========================================
map_os() {
  local kind="$1"
  local os="$2"

  case "$kind" in
    # Proste mapowanie (fzf, fd w prostszej wersji)
    linux_darwin|"")
      case "$os" in
        linux)  echo "linux" ;;
        darwin) echo "darwin" ;;
        *)      echo "$os" ;;
      esac
      ;;

    # Mapowanie w stylu Rust target triple (ripgrep, fd)
    rust_triple)
      # projekty Rustowe mają różne warianty
      case "$os" in
        linux)  echo "unknown-linux-gnu" ;;
        darwin) echo "apple-darwin" ;;
        *)      echo "$os" ;;
      esac
      ;;

    # nvim: linux / macos
    linux_macos)
      case "$os" in
        linux)  echo "linux" ;;
        darwin) echo "macos" ;;
        *)      echo "$os" ;;
      esac
      ;;

    # starship: rust musl / darwin
    rust_musl)
      case "$os" in
        linux)  echo "unknown-linux-musl" ;;
        darwin) echo "apple-darwin" ;;
        *)      echo "$os" ;;
      esac
      ;;

    # Nie modyfikujemy OS
    *) echo "$os" ;;
  esac
}
