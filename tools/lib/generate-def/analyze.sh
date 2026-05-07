# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

infer_tool_name_from_repo() {
  local repo="${1:?repo required}"
  local tool="${repo##*/}"

  tool="${tool%.git}"
  echo "$tool"
}

# tag_prefix_and_version <tag>
# Input: tag (np. "v1.2.3")
# Output: sets globals RELEASE_TAG + VERSION
tag_prefix_and_version() {
  local tag="${1:?tag required}"

  RELEASE_TAG="$tag"
  VERSION="$tag"

  if [[ $tag == v* ]]; then
    VERSION="${tag#v}"
  fi
}

# detect_asset_prefix <tool> <version> <assets...>
# Input: tool+version+assets
# Output: sets global ASSET_FILTER_PREFIX (np. "fd-v" vs "fd")
detect_asset_prefix() {
  local tool="${1:?tool required}"
  local version="${2:?version required}"
  shift 2

  ASSET_FILTER_PREFIX="$tool"

  local a

  # 1) fd-v10.3.0-...
  for a in "$@"; do
    [[ $a == "${tool}-v${version}"* ]] && {
      ASSET_FILTER_PREFIX="${tool}-v"
      return 0
    }
  done

  # 2) rg-14.1.0-... / fzf-0.67.0-...
  for a in "$@"; do
    [[ $a == "${tool}-${version}"* ]] && {
      ASSET_FILTER_PREFIX="${tool}"
      return 0
    }
  done

  # 3) fzf_0.67.0
  for a in "$@"; do
    [[ $a == "${tool}_${version}"* ]] && {
      ASSET_FILTER_PREFIX="${tool}"
      return 0
    }
  done

  return 0
}

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

build_checksums_from_assets() {
  local selected=("$@")
  CHECKSUMS_EMIT=()

  if ! declare -p GITHUB_ASSET_DIGESTS >/dev/null 2>&1; then
    return 0
  fi
  ((${#GITHUB_ASSET_DIGESTS[@]} > 0)) || return 0

  local rec asset digest selected_asset
  for rec in "${GITHUB_ASSET_DIGESTS[@]}"; do
    asset="${rec%%|*}"
    digest="${rec#*|}"

    for selected_asset in "${selected[@]}"; do
      [[ $asset == "$selected_asset" ]] || continue
      CHECKSUMS_EMIT+=("\"${asset}|${digest}\"")
      break
    done
  done
}

build_checksums_from_emitted_assets() {
  local selected=()
  local rec

  for rec in "${ASSETS_EMIT[@]}"; do
    rec="${rec%\"}"
    rec="${rec#\"}"
    selected+=("${rec#*|}")
  done

  build_checksums_from_assets "${selected[@]}"
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
