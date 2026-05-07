# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

asset_matches_prefix() {
  local asset="${1##*/}"
  local prefix="${2:?prefix required}"
  local version="${3:?version required}"
  local suffix

  [[ $asset == "${prefix}${version}"* ]] && return 0
  [[ $asset == "${prefix}-${version}"* ]] && return 0
  [[ $asset == "${prefix}_${version}"* ]] && return 0

  if [[ $asset == "$prefix"-* ]]; then
    suffix="${asset#"$prefix"-}"
    [[ $suffix =~ ^(x86_64|aarch64|arm64|amd64|linux|macos|darwin)([-_.]|$) ]] && return 0
  fi

  if [[ $asset == "$prefix"_* ]]; then
    suffix="${asset#"$prefix"_}"
    [[ $suffix =~ ^(x86_64|aarch64|arm64|amd64|linux|macos|darwin)([-_.]|$) ]] && return 0
  fi

  return 1
}

# build_assets_from_assets <assets...>
# Input: asset names
# Output: sets global array ASSETS_EMIT with unique
#         "<os>:<arch>:<libc>|<asset_name>" records
build_assets_from_assets() {
  local assets=("$@")
  local seen=()
  ASSETS_EMIT=()

  local a os arch libc key
  for a in "${assets[@]}"; do
    # pomijamy sumy, sygnatury, itp.
    case "$a" in
    *.sha256 | *.sha256sum | *.sig | *.asc) continue ;;
    *.deb | *.rpm | *.apk | *.pkg) continue ;;
    *-update) continue ;;
    esac

    if [[ -n ${ASSET_FILTER_PREFIX:-} && -n ${VERSION:-} ]]; then
      asset_matches_prefix "$a" "$ASSET_FILTER_PREFIX" "$VERSION" || continue
    fi

    os="$(detect_os "$a")"
    [[ -n $os ]] || continue
    arch="$(detect_arch "$a")"
    [[ -n $arch ]] || continue
    arch="$(normalize_raw_arch "$arch")"

    libc="any"
    [[ $os == "linux" ]] && libc="$(detect_libc "$a")"

    key="${os}:${arch}:${libc}"
    if ((${#seen[@]} > 0)) && has_seen_key "$key" "${seen[@]}"; then
      continue
    fi
    seen+=("$key")

    ASSETS_EMIT+=("\"${key}|${a}\"")
  done

  if ((${#ASSETS_EMIT[@]} == 0)); then
    echo "WARN: no assets detected; sample assets:" >&2
    printf '  - %s\n' "${assets[@]:0:10}" >&2
    ASSETS_EMIT+=('"linux:x86_64:gnu|example-x86_64-unknown-linux-gnu.tar.gz" # TODO: adjust')
  fi
}

has_seen_key() {
  local needle="$1"
  shift

  local item
  for item in "$@"; do
    [[ $item == "$needle" ]] && return 0
  done

  return 1
}
