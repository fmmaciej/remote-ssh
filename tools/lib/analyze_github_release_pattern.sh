# shellcheck shell=bash

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
