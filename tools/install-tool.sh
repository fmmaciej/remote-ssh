#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

DEF_DIR="$SCRIPT_DIR/defs"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/env.sh"

# Hardcoded debug
# shellcheck disable=SC2034
DEBUG=0

# Defaults
DEFAULT_ASSET_TEMPLATE="prefix-version-arch-os"
DEFAULT_ARCH_KIND="x86_64_aarch64"
DEFAULT_OS_KIND="linux_darwin"

usage() {
  echo "Usage: $0 <tool> [version|latest]" >&2
  exit 1
}

# ===========================================
# load_defs <tool>
#
# Ładuje definicję narzędzia z katalogu defs/.
# Plik defs/<tool>.sh zawiera jedynie dane konfiguracyjne:
#   - TOOL_NAME
#   - GH_REPO
#   - DEFAULT_VERSION
#   - TAG_PREFIX
#   - BINARY_NAME (opcjonalnie)
#   - ASSET_PREFIX, ASSET_TEMPLATE
#   - ARCH_KIND, OS_KIND
#
# Funkcja:
#   - sprawdza istnienie pliku defs/<tool>.sh,
#   - ładuje wspólne helpery z lib/common.sh,
#   - wczytuje definicję narzędzia,
#   - ustawia domyślne wartości brakujących pól.
#
# Globalne zmienne ustawiane:
#   TOOL_NAME, GH_REPO, DEFAULT_VERSION,
#   BINARY_NAME, ASSET_PREFIX, ASSET_TEMPLATE,
#   ARCH_KIND, OS_KIND, TAG_PREFIX.
#
# Zakończenie:
#   EXIT 1 jeśli brak definicji narzędzia.
# ===========================================
load_defs() {
  local tool="$1"
  local def_file="$DEF_DIR/${tool}.sh"

  if [[ ! -f "$def_file" ]]; then
    log_error "$tool not found in $DEF_DIR)"
    exit 1
  fi

  # shellcheck source=/dev/null
  . "$def_file"

  : "${TOOL_NAME:?}"
  : "${GH_REPO:?}"
  : "${DEFAULT_VERSION:?}"

  BINARY_NAME="${BINARY_NAME:-$TOOL_NAME}"
  ASSET_PREFIX="${ASSET_PREFIX:-$TOOL_NAME}"
  ASSET_TEMPLATE="${ASSET_TEMPLATE:-$DEFAULT_ASSET_TEMPLATE}"
  ARCH_KIND="${ARCH_KIND:-$DEFAULT_ARCH_KIND}"
  OS_KIND="${OS_KIND:-$DEFAULT_OS_KIND}"
  TAG_PREFIX="${TAG_PREFIX:-}"
}

# ===========================================
# resolve_arch_os
#
# Ustala platformę użytkownika:
#   - RAW_ARCH, RAW_OS (z uname),
#   - ARCH, OS (mapowane przez map_arch/map_os).
#
# map_arch i map_os pochodzą z common.sh i zależą
# od wartości ARCH_KIND oraz OS_KIND w defs/<tool>.sh.
#
# Globalne zmienne ustawiane:
#   RAW_ARCH, RAW_OS, ARCH, OS
#
# Nie przyjmuje argumentów, nie zwraca nic.
# ===========================================
resolve_arch_os() {
  detect_arch_os_raw

  ARCH="$(map_arch "$ARCH_KIND" "$RAW_ARCH")"
  OS="$(map_os "$OS_KIND" "$RAW_OS")"
}

# ===========================================
# resolve_version <requested_version>
#
# Ustala wersję narzędzia do zainstalowania.
#
# Logika:
#   - brak argumentu -> VERSION = DEFAULT_VERSION
#   - argument "latest":
#       pobiera tag_name z GitHuba,
#       jeśli TAG_PREFIX jest ustawione
#       i tag zaczyna się od tego prefiksu,
#       usuwa go, aby uzyskać „gołe” VERSION.
#   - argument inny niż "latest":
#       VERSION = ten argument.
#
# Przykłady:
#   TAG_PREFIX="v", tag="v0.67.0"  -> VERSION="0.67.0"
#   TAG_PREFIX="",  tag="15.1.0"   -> VERSION="15.1.0"
#
# Ustawia globalną zmienną:
#   VERSION
#
# Zakończenie:
#   EXIT 1 gdy get_latest_github_tag nie zwróci wersji.
# ===========================================
resolve_version() {
  local req_version="$1"

  if [[ -z "$req_version" ]]; then
    VERSION="$DEFAULT_VERSION"

  elif [[ "$req_version" == "latest" ]]; then
    local tag
    tag="$(get_latest_github_tag "$GH_REPO")"

    # jeśli DEF posiada TAG_PREFIX, spróbuj go zdjąć
    if [[ -n "${TAG_PREFIX}" && "$tag" == "${TAG_PREFIX}"* ]]; then
      VERSION="${tag#"${TAG_PREFIX}"}"
    else
      VERSION="$tag"
    fi

  else
    VERSION="$req_version"
  fi
}

# ===========================================
# download_and_extract <version> <arch> <os>
#
# Pobiera i rozpakowuje archiwum z GitHub Releases.
#
# Operacje wykonywane:
#   1. Buduje nazwę assetu:
#        archive_name = build_asset_name(...)
#   2. Buduje poprawny tag do URL:
#        tag_for_url = TAG_PREFIX + version
#   3. Pobiera archiwum do tymczasowego katalogu (TMPDIR).
#   4. Rozpakowuje .tar.gz lub .zip.
#   5. Ustawia globalne:
#        EXTRACT_DIR = TMPDIR
#
# tmp katalog:
#   - TMPDIR jest globalny, aby trap na EXIT
#     mógł go posprzątać nawet po wyjściu z funkcji.
#
# Argumenty:
#   version - "goła" wersja (np. 0.67.0)
#   arch    - architektura po mapowaniu (np. amd64)
#   os      - system po mapowaniu (np. linux)
#
# Globalnie ustawia:
#   EXTRACT_DIR - katalog z rozpakowanym archiwum
#
# Globalnie korzysta:
#   INSTALL_PREFIX, INSTALL_BIN_DIR
#
# Błędy:
#   EXIT 1 przy nieznanym formacie archiwum
#   EXIT 1 gdy brakuje unzip przy plikach .zip
# ===========================================
download_and_extract() {
  local version="$1"
  local arch="$2"
  local os="$3"

  local archive_name
  local tag_for_url
  local url

  mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"

  archive_name="$(build_asset_name "$ASSET_TEMPLATE" "$ASSET_PREFIX" "$version" "$arch" "$os")"
  tag_for_url="${TAG_PREFIX}${version}"

  url="https://github.com/${GH_REPO}/releases/download/${tag_for_url}/${archive_name}"

  # TMPDIR globalne, żeby trap miał do czego się odwołać przy EXIT
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  log_info "Downloading: $url"

  # cd tylko w subshellu
  # po wyjściu z funkcji wracamy do poprzedniego katalogu
  # sprytne cd -
  (
    cd "$TMPDIR"
    curl -fsSLO "$url"

    case "$archive_name" in
      *.tar.gz|*.tgz)
        tar xzf "$archive_name"
        ;;
      *.zip)
        if [[ "${ZIP_SUPPORTED:-0}" -ne 1 ]]; then
          log_error "Do rozpakowania ${archive_name} potrzebny jest 'unzip', a nie jest dostepny."
          exit 1
        fi
        unzip -q "$archive_name"
        ;;
      *)
        log_error "Unknown archive file format: $archive_name"
        exit 1
        ;;
    esac
  )

  EXTRACT_DIR="$TMPDIR"

  log_debug "download_and_extract()"
  log_debug "  version=$version"
  log_debug "  arch=$arch"
  log_debug "  os=$os"
  log_debug "  ASSET_TEMPLATE=$ASSET_TEMPLATE"
  log_debug "  archive_name=$archive_name"
  log_debug "  url=$url"
}

# ===========================================
# install_binary
#
# Kopiuje rozpakowaną binarkę do ~/.local/opt
# i tworzy symlink w ~/.local/bin.
#
# Funkcja zakłada, że download_and_extract wcześniej
# ustawiło globalny EXTRACT_DIR.
#
# Operacje:
#   - wyszukuje ścieżkę binarki w EXTRACT_DIR,
#   - weryfikuje, że jest wykonywalna,
#   - tworzy katalog docelowy:
#       ~/.local/opt/<tool>-<VERSION>,
#   - kopiuje binarkę,
#   - tworzy symlink:
#       ~/.local/bin/<TOOL_NAME> -> binarka.
#
# Globalnie używa:
#   EXTRACT_DIR, TOOL_NAME, BINARY_NAME, VERSION,
#   INSTALL_PREFIX, INSTALL_BIN_DIR
#
# Zakończenie:
#   EXIT 1 jeśli nie znaleziono binarki,
#   EXIT 1 jeśli binarka nie jest wykonywalna.
# ===========================================
install_binary() {
  local bin_rel_path
  local target_dir

  bin_rel_path="$(find_binary_path_by_name "$EXTRACT_DIR" "$BINARY_NAME")"

  if [[ -z "$bin_rel_path" ]]; then
    log_error "Binary $BINARY_NAME not found in ${EXTRACT_DIR}"
    exit 1
  fi

  if [[ ! -x "$EXTRACT_DIR/$bin_rel_path" ]]; then
    log_error "File is not executable: $EXTRACT_DIR/$bin_rel_path"
    exit 1
  fi

  target_dir="${INSTALL_PREFIX}/${TOOL_NAME}-${VERSION}"
  rm -rf "$target_dir"
  mkdir -p "$target_dir"

  cp "$EXTRACT_DIR/$bin_rel_path" "$target_dir/"
  ln -sf "$target_dir/$BINARY_NAME" "$INSTALL_BIN_DIR/$TOOL_NAME"

  log_info "Installed:   ${target_dir}"
  log_info "Symlink:     ${INSTALL_BIN_DIR}/${TOOL_NAME}"
}

# ===========================================
# main <tool> [version]
#
# Główna funkcja koordynująca instalację.
#
# Kroki:
#   1. Wczytuje definicję narzędzia (load_defs).
#   2. Sprawdza wymagane narzędzia (check_req_tools).
#   3. Ustala platformę (resolve_arch_os).
#   4. Ustala wersję (resolve_version).
#   5. Pobiera i rozpakowuje asset (download_and_extract).
#   6. Instaluje binarkę (install_binary).
#
# Argumenty:
#   tool    - nazwa pliku defs/<tool>.sh
#   version - "latest" albo konkretna wersja
#
# Zakończenie:
#   EXIT 1 przy każdym krytycznym błędzie,
#   0 po pomyślnej instalacji.
# ===========================================
main() {
  local tool="${1:-}"
  local req_version="${2:-}"

  [ -z "$tool" ] && usage

  load_defs "$tool"

  ! check_req_tools && exit 1

  resolve_arch_os
  resolve_version "$req_version"

  log_info "Installing:  ${GH_REPO}, version: ${VERSION}, arch: ${ARCH}, os: ${OS}"

  download_and_extract "$VERSION" "$ARCH" "$OS"
  install_binary
}

main "$@"

