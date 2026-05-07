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
