# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

# tag_prefix_and_version <tag>
# Input: tag (np. "v1.2.3")
# Output: sets globals TAG_PREFIX + DEFAULT_VERSION
tag_prefix_and_version() {
  local tag="${1:?tag required}"

  TAG_PREFIX=""
  DEFAULT_VERSION="$tag"

  if [[ $tag == v* ]]; then
    TAG_PREFIX="v"
    DEFAULT_VERSION="${tag#v}"
  fi
}

# detect_asset_prefix <tool> <version> <assets...>
# Input: tool+version+assets
# Output: sets global ASSET_PREFIX (np. "fd-v" vs "fd")
detect_asset_prefix() {
  local tool="${1:?tool required}"
  local version="${2:?version required}"
  shift 2

  ASSET_PREFIX="$tool"

  local a

  # 1) fd-v10.3.0-...
  for a in "$@"; do
    [[ $a == "${tool}-v${version}"* ]] && {
      ASSET_PREFIX="${tool}-v"
      return 0
    }
  done

  # 2) rg-14.1.0-... / fzf-0.67.0-...
  for a in "$@"; do
    [[ $a == "${tool}-${version}"* ]] && {
      ASSET_PREFIX="${tool}"
      return 0
    }
  done

  # 3) fzf_0.67.0
  for a in "$@"; do
    [[ $a == "${tool}_${version}"* ]] && {
      ASSET_PREFIX="${tool}"
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

# build_variants_from_assets <assets...>
# Input: asset names
# Output: sets global array VARIANTS_EMIT with unique
#         "<os>:<arch>:<libc>|<template>|<arch_kind>|<os_kind>" records
build_variants_from_assets() {
  local assets=("$@")
  local seen=()
  VARIANTS_EMIT=()

  local a os arch libc key template arch_kind os_kind
  for a in "${assets[@]}"; do
    # pomijamy sumy, sygnatury, itp.
    case "$a" in
    *.sha256 | *.sha256sum | *.sig | *.asc) continue ;;
    *.deb | *.rpm | *.apk | *.pkg) continue ;;
    *-update) continue ;;
    esac

    if [[ -n ${ASSET_PREFIX:-} && -n ${DEFAULT_VERSION:-} ]]; then
      asset_matches_prefix "$a" "$ASSET_PREFIX" "$DEFAULT_VERSION" || continue
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

    template="$(guess_template "$a")"
    arch_kind="$(guess_arch_kind "$a")"
    os_kind="$(guess_os_kind "$a")"

    [[ $os == "linux" && $libc == "musl" ]] && os_kind="rust_musl"

    VARIANTS_EMIT+=("\"${key}|${template}|${arch_kind}|${os_kind}\"")
  done

  if ((${#VARIANTS_EMIT[@]} == 0)); then
    echo "WARN: no variants detected; sample assets:" >&2
    printf '  - %s\n' "${assets[@]:0:10}" >&2
    VARIANTS_EMIT+=('"linux:x86_64:gnu|prefix-version-arch-os|x86_64_aarch64|rust_triple" # TODO: adjust')
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
