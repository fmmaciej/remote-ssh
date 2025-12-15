# shellcheck shell=bash

ensure_this_file_sourced

# tag_prefix_and_version <tag>
# Input: tag (np. "v1.2.3")
# Output: sets globals TAG_PREFIX + DEFAULT_VERSION
tag_prefix_and_version() {
  local tag="${1:?tag required}"

  TAG_PREFIX=""
  DEFAULT_VERSION="$tag"

  if [[ "$tag" == v* ]]; then
    # shellcheck disable=SC2034
    TAG_PREFIX="v"
    # shellcheck disable=SC2034
    DEFAULT_VERSION="${tag#v}"
  fi
}

# detect_asset_prefix <tool> <version> <assets...>
# Input: tool+version+assets
# Output: sets global ASSET_PREFIX (np. "fd-v" vs "fd") based on asset names
detect_asset_prefix() {
  local tool="${1:?tool required}"
  local version="${2:?version required}"
  shift 2

  local assets=("$@")

  # shellcheck disable=SC2034
  ASSET_PREFIX="$tool"

  local a
  for a in "${assets[@]}"; do
    case "$a" in
      "${tool}-v${version}"* )  ASSET_PREFIX="${tool}-v" return 0 ;;
      "${tool}-${version}"* )   ASSET_PREFIX="${tool}" return 0 ;;
      "${tool}_${version}"* )   ASSET_PREFIX="${tool}" return 0 ;;
    esac
  done
}

# build_variants_from_assets <assets...>
# Input: asset names
# Output: sets global array VARIANTS_EMIT with unique
#         "<os>:<arch>:<libc>|<template>|<arch_kind>|<os_kind>" records
build_variants_from_assets() {
  local assets=("$@")
  declare -A seen=()
  VARIANTS_EMIT=()

  local a os arch libc key template arch_kind os_kind
  for a in "${assets[@]}"; do
    # pomijamy sumy, sygnatury, itp.
    case "$a" in
      *.sha256|*.sha256sum|*.sig|*.asc) continue ;;
    esac

    os="$(detect_os "$a")";     [[ -n "$os" ]]   || continue
    arch="$(detect_arch "$a")"; [[ -n "$arch" ]] || continue
    arch="$(normalize_raw_arch "$arch")"

    libc="any"
    [[ "$os" == "linux" ]] && libc="$(detect_libc "$a")"

    key="${os}:${arch}:${libc}"
    [[ -n "${seen[$key]:-}" ]] && continue
    seen["$key"]=1

    template="$(guess_template "$a")"
    arch_kind="$(guess_arch_kind "$a")"
    os_kind="$(guess_os_kind "$a")"

    [[ "$os" == "linux" && "$libc" == "musl" ]] && os_kind="rust_musl"

    VARIANTS_EMIT+=( "\"${key}|${template}|${arch_kind}|${os_kind}\"" )
  done

  if ((${#VARIANTS_EMIT[@]} == 0)); then
    echo "WARN: no variants detected; sample assets:" >&2
    printf '  - %s\n' "${assets[@]:0:10}" >&2
    VARIANTS_EMIT+=( "\"linux:x86_64:gnu|prefix-version-arch-os|x86_64_aarch64|rust_triple\" # TODO: adjust" )
  fi
}
