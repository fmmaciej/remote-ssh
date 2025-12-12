# shellcheck shell=bash

# Jeśli zwróci błąd (zmienna już ustawiona), przerwij dalsze ładowanie pliku.
ensure_this_file_sourced

# shellcheck source=/dev/null
. "$LIB_DIR/helpers.sh"

# Wspólna biblioteka helperów dla instalatora narzędzi z GitHuba.
# Definicje tooli są tylko zbiorem parametrów; cała logika arch/OS,
# wzorców nazw assetów i wyszukiwania binarek jest tutaj.

# ===========================================
# detect_arch_os_raw
#
# Pobiera surowe informacje o platformie:
#   RAW_ARCH - architektura z uname -m (np. x86_64, arm64)
#   RAW_OS   - system operacyjny z uname -s (lowercase)
#
# Zmienne RAW_ARCH i RAW_OS nie są modyfikowane ani mapowane.
# Mapa arch/OS odbywa się później w resolve_arch_os().
#
# Globalnie ustawia:
#   RAW_ARCH, RAW_OS
#
# Nie przyjmuje argumentów, nie zwraca nic.
# ===========================================
detect_arch_os_raw() {
  # shellcheck disable=SC2034
  RAW_ARCH="$(uname -m)"

  # shellcheck disable=SC2034
  RAW_OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
}

# ===========================================
# map_arch <arch_kind> <raw_arch>
#
# Mapuje surową architekturę (RAW_ARCH) na format wymagany
# przez dany projekt (fzf, ripgrep, fd itp.).
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
        x86_64)
          echo "amd64"
          ;;
        aarch64|arm64)
          echo "arm64"
          ;;
        *)
          echo "$arch"
          ;;
      esac
      ;;

    # ripgrep i fd
    x86_64_aarch64)
      case "$arch" in
        x86_64)
          echo "x86_64"
          ;;
        aarch64|arm64)
          echo "aarch64"
          ;;
        *)
          echo "$arch"
          ;;
      esac
      ;;

    # nvim: x86_64 / arm64
    x86_64_arm64)
      case "$arch" in
        x86_64)
          echo "x86_64"
          ;;
        aarch64|arm64)
          echo "arm64"
          ;;
        *)
          echo "$arch"
          ;;
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
# Mapuje nazwę systemu operacyjnego na format używany przez projekt.
# W defs/<tool>.sh wybiera się schemat (OS_KIND).
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
        linux)
          echo "linux"
          ;;
        darwin)
          echo "darwin"
          ;;
        *)
          echo "$os"
          ;;
      esac
      ;;

    # Mapowanie w stylu Rust target triple (ripgrep, fd)
    rust_triple)
      # projekty Rustowe mają różne warianty
      case "$os" in
        linux)
          echo "unknown-linux-gnu"
          ;;
        darwin)
          echo "apple-darwin"
          ;;
        *)
          echo "$os"
          ;;
      esac
      ;;

    # nvim: linux / macos
    linux_macos)
      case "$os" in
        linux)
          echo "linux"
          ;;
        darwin)
          echo "macos"
          ;;
        *)
          echo "$os"
          ;;
      esac
      ;;

    # starship: rust musl / darwin
    rust_musl)
      case "$os" in
        linux)
          echo "unknown-linux-musl"
          ;;
        darwin)
          echo "apple-darwin"
          ;;
        *)
          echo "$os"
          ;;
      esac
      ;;

    # Nie modyfikujemy OS
    *)
      echo "$os"
      ;;
  esac
}

# ===========================================
# build_asset_name <template> <prefix> <version> <arch> <os>
#
# Buduje nazwę pliku release (asset) na podstawie wybranego szablonu.
# Szablon pochodzi z defs/<tool>.sh.
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
    prefix-version-arch-os)
      echo "${base}-${arch}-${os}.tar.gz"
      ;;

    # tmux
    prefix-version-os_arch)
      echo "${base}-${os}_${arch}.tar.gz"
      ;;

    # yazi
    prefix-arch-os)
      echo "${prefix}-${arch}-${os}.zip"
      ;;

    # starship
    prefix-arch-os-tgz)
      echo "${prefix}-${arch}-${os}.tar.gz"
      ;;

    # nvim
    prefix-os-arch)
      # Uwaga: ignorujemy 'version', używane tylko w tagu URL,
      # a nie w samej nazwie pliku tar.gz.
      echo "${prefix}-${os}-${arch}.tar.gz"
      ;;

    *)
      echo "Nieznany ASSET_TEMPLATE: ${template}" >&2
      return 1
      ;;
  esac
}

# ===========================================
# find_binary_path_by_name <extract_dir> <binary_name>
#
# Wyszukuje wykonywalny plik o nazwie <binary_name>
# w rozpakowanym katalogu. Używane w install_binary().
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

# ===========================================
# get_latest_github_tag <repo>
#
# Pobiera najnowszy tag (tag_name) z GitHub Releases
# dla repozytorium "owner/repo".
#
# Nie korzysta z jq; parsuje JSON minimalnie sed-em.
#
# Argument:
#   repo - "owner/repo"
#
# Zwraca (echo):
#   tag_name (np. "v0.67.0", "15.1.0", "release-23")
#
# Zakończenie:
#   EXIT 22 (curl) jeśli sieć lub GitHub odpowie błędem,
#   lub pusty output jeśli JSON nie zawiera tag_name.
# ===========================================
get_latest_github_tag() {
  local repo="$1"
  local addr="https://api.github.com/repos/${repo}/releases/latest"

  curl -fsS "$addr" \
      | sed -n 's@.*"tag_name":[[:space:]]*"\([^"]*\)".*@\1@p'
}

# ===========================================
# check_req_tools
#
# Sprawdza obecność minimalnego zestawu narzędzi wymaganych
# do działania instalatora:
#   curl, sed, grep, find, tar, uname, mktemp
#
# Dodatkowo:
#   jeśli dostępne jest 'unzip', ustawia ZIP_SUPPORTED=1
#   inaczej ZIP_SUPPORTED=0
#
# Zwraca:
#   0 - wszystko dostępne
#   1 - brakuje któregoś narzędzia
#
# W przypadku braków wypisuje listę na stderr.
#
# Globalnie ustawia:
#   ZIP_SUPPORTED
# ===========================================
check_req_tools() {
  # Przy braku jest stop
  local required=(curl grep sed find tar uname mktemp)
  local missing=()

  for cmd in "${required[@]}"; do
    if ! have "${cmd}" ; then
      missing+=("$cmd")
    fi
  done

  # Obsługa zipów: jeśli nie ma unzip
  # nie rozpakuje assetów w formacie .zip.
  if have unzip; then
    ZIP_SUPPORTED=1
  else
    # shellcheck disable=SC2034
    ZIP_SUPPORTED=0
  fi

  if ((${#missing[@]} > 0)); then
    echo "Brakuje wymaganych narzedzi do bootstrapa:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    return 1
  fi

  return 0
}

# ===========================================
# analyze_github_release_pattern <repo> <prefix>
#
# Generuje szkic defs/<tool>.sh.
#
# Ustala:
#   - tag_name            (np. "v0.67.0" albo "15.1.0"),
#   - sugerowane:
#       TAG_PREFIX        (np. "v" lub "")
#       DEFAULT_VERSION   (np. "0.67.0" lub "15.1.0")
#       ASSET_PREFIX      (np. "fzf" albo "fd-v")
#       ASSET_TEMPLATE    (prefix-version-arch-os / prefix-version-os_arch)
#
# Argumenty:
#   repo   - "owner/repo"
#   prefix - nazwa bazowa narzędzia (np. "fzf", "fd", "rg")
#
# Funkcja niczego nie zapisuje - tylko wypisuje RAW dane
# oraz sugerowaną zawartość pliku defs/<prefix>.sh.
# ===========================================
analyze_github_release_pattern() {
  local repo="$1"
  local prefix="$2"

  local addr="https://api.github.com/repos/${repo}/releases/latest"
  echo "[INFO] Downloading: $addr" >&2

  local json tag tag_no_v assets

  json="$(curl -fsS "$addr")"

  tag="$(
    printf '%s\n' "$json" \
      | sed -n 's@.*"tag_name":[[:space:]]*"\([^"]*\)".*@\1@p'
  )"

  if [[ -z "$tag" ]]; then
    echo "[ERROR] Nie mogę znaleźć tag_name" >&2
    return 1
  fi

  tag_no_v="$tag"
  [[ "$tag_no_v" == v* ]] && tag_no_v="${tag_no_v#v}"

  # Lista plików (jedna nazwa na linię)
  assets="$(
    printf '%s\n' "$json" \
      | sed -n 's@.*"name":[[:space:]]*"\([^"]*\)".*@\1@p'
  )"

  echo
  echo "=== RAW DATA ==="
  echo "repo:       $repo"
  echo "tag_name:   $tag"
  echo "tag_no_v:   $tag_no_v"
  echo
  echo "assets:"

  # drukujemy linia po linii, bez dzielenia po spacji
  printf '%s\n' "$assets" | sed 's/^/  - /'
  echo

  # --- Detekcja TAG_PREFIX + DEFAULT_VERSION + ASSET_PREFIX ---

  local det_tag_prefix=""
  local det_default_version="$tag_no_v"
  local det_asset_prefix="$prefix"

  # Czy są assety typu: prefix-<tag_no_v>-... ?  (fzf, rg)
  if printf '%s\n' "$assets" | grep -q "^${prefix}-${tag_no_v}-"; then
    # tag_name może być "v0.67.0", ale asset używa "0.67.0"
    det_default_version="$tag_no_v"

    # jeśli w tagu było 'v', to najczęściej TAG_PREFIX="v"
    [[ "$tag" == v* ]] && det_tag_prefix="v"

  # Czy są assety typu: prefix-v<tag_no_v>-... ?  (fd)
  elif printf '%s\n' "$assets" | grep -q "^${prefix}-v${tag_no_v}-"; then
    det_tag_prefix="v"
    det_default_version="$tag_no_v"
    det_asset_prefix="${prefix}-v"

  # Czy są assety typu: prefix-<tag>-... (bez zabawy z 'v')
  elif printf '%s\n' "$assets" | grep -q "^${prefix}-${tag}-"; then
    det_tag_prefix=""
    det_default_version="$tag"
    det_asset_prefix="$prefix"

  else
    # Nie udało się dopasować - zostawiamy domyślne, użytkownik poprawi ręcznie
    det_tag_prefix=""
    det_default_version="$tag_no_v"
    det_asset_prefix="$prefix"

  fi

  # --- Zgadujemy szablon ASSET_TEMPLATE na podstawie przykładowego assetu ---

  local example
  example="$(
    printf '%s\n' "$assets" \
      | grep "^${det_asset_prefix}-\?${det_default_version}-" \
      | head -n1
  )"

  local guessed_template="unknown"
  # arch-os: fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz
  #          fzf-0.67.0-linux_amd64.tar.gz (też przejdzie przez ten regex)
  if [[ "$example" =~ ^${det_asset_prefix}-?${det_default_version}-([A-Za-z0-9._-]+)-([A-Za-z0-9._-]+)\. ]]; then
    guessed_template="prefix-version-arch-os"

  # os_arch: typowo fzf-<version>-linux_amd64.tar.gz, jeśli taki format występuje
  elif [[ "$example" =~ ^${det_asset_prefix}-?${det_default_version}-([A-Za-z0-9._-]+)_([A-Za-z0-9._-]+)\. ]]; then
    guessed_template="prefix-version-os_arch"
  fi

  echo "=== DETECTION ==="
  echo "TAG_PREFIX:        $det_tag_prefix"
  echo "DEFAULT_VERSION:   $det_default_version"
  echo "ASSET_PREFIX:      $det_asset_prefix"
  echo "ASSET_TEMPLATE:    $guessed_template"
  echo "example asset:     $example"
  echo

  echo "=== SUGGESTED defs/$prefix.sh ==="
  echo "TOOL_NAME=\"$prefix\""
  echo "GH_REPO=\"$repo\""
  echo "DEFAULT_VERSION=\"$det_default_version\""
  echo "TAG_PREFIX=\"$det_tag_prefix\""
  echo
  echo "BINARY_NAME=\"$prefix\""
  echo "ASSET_PREFIX=\"$det_asset_prefix\""
  echo "ASSET_TEMPLATE=\"$guessed_template\""
  echo
  echo "ARCH_KIND=\"x86_64_aarch64\"   # dopasuj"
  echo "OS_KIND=\"linux_darwin\"       # dopasuj"
  echo
}
