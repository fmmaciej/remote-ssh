# shellcheck shell=bash

ensure_this_file_sourced

# ===========================================
# build_asset_name <template> <prefix> <version> <arch> <os>
#
# Obsługiwane szablony:
#   prefix-version-arch-os   -> ripgrep, fd
#   prefix-version-os_arch   -> fzf
#   prefix-arch-os           -> yazi
#   prefix-arch-os-tgz       -> starship
#   prefix-os-arch           -> nvim
#
# Argumenty:
#   template - nazwa szablonu
#   prefix   - nazwa toola (np. "fzf", "rg")
#   version  - wersja bez prefiksów
#   arch     - finalna architektura (z map_arch)
#   os       - finalny system (z map_os)
#
# Zwraca (echo):
#   pełną nazwę pliku archiwum .tar.gz
#
# Zakończenie:
#   EXIT 1 przy nieznanym szablonie.
# ===========================================
build_asset_name() {
  local template="$1" prefix="$2" version="$3" arch="$4" os="$5"

  # base = prefix-version
  local base="$prefix"
  if [[ "$prefix" =~ - ]]; then
      base="${prefix}${version}"

  else
      base="${prefix}-${version}"

  fi

  case "$template" in
    prefix-version-arch-os) echo "${base}-${arch}-${os}.tar.gz" ;;

    # tmux
    prefix-version-os_arch) echo "${base}-${os}_${arch}.tar.gz" ;;

    # yazi
    prefix-arch-os)         echo "${prefix}-${arch}-${os}.zip" ;;

    # starship
    prefix-arch-os-tgz)     echo "${prefix}-${arch}-${os}.tar.gz" ;;

    # nvim
    # Uwaga: ignorujemy 'version', używane tylko w tagu URL,
    # a nie w samej nazwie pliku tar.gz.
    prefix-os-arch)         echo "${prefix}-${os}-${arch}.tar.gz" ;;

    *)
      echo "Nieznany ASSET_TEMPLATE: ${template}" >&2
      return 1
      ;;
  esac
}

# ===========================================
# find_binary_path_by_name <extract_dir> <binary_name>
#
# Przeszukiwanie:
#   - maksymalna głębokość: 4 poziomy,
#   - zwraca pierwsze dopasowanie.
#
# Zwraca (echo):
#   ścieżkę względną względem <extract_dir>
#   np. "fzf" albo "bin/rg"
#
# Jeśli brak - zwraca pusty string.
# ===========================================
find_binary_path_by_name() {
  local extract_dir="$1"
  local bin_name="$2"

  local bin
  bin="$(find "$extract_dir" -maxdepth 4 -type f -name "$bin_name" | head -n1)"
  bin="${bin#"$extract_dir"/}"

  echo "$bin"
}
