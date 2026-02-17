# shellcheck shell=bash

ensure_this_file_sourced

# echo: "VERSION"
resolve_version() {
  local req_version="$1" default_version="$2" repo="$3" tag_prefix="$4"

  if [[ -z "$req_version" ]]; then
    echo "$default_version"
    return 0
  fi

  if [[ "$req_version" != "latest" ]]; then
    echo "$req_version"
    return 0
  fi

  local tag
  tag="$(get_latest_github_tag "$repo")" || return 1
  [[ -n "$tag" ]] || return 1

  if [[ -n "$tag_prefix" && "$tag" == "${tag_prefix}"* ]]; then
    echo "${tag#"$tag_prefix"}"
  else
    echo "$tag"
  fi
}
