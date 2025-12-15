# shellcheck shell=bash

ensure_this_file_sourced

download_and_extract() {
  local repo="$1" tag_prefix="$2" version="$3"
  local asset_prefix="$4" asset_template="$5"
  local arch_kind="$6" os_kind="$7"
  local raw_arch="$8" raw_os="$9"

  local arch os archive_name tag_for_url url

  arch="$(map_arch "$arch_kind" "$raw_arch")" || return 1
  os="$(map_os "$os_kind" "$raw_os")" || return 1

  archive_name="$(build_asset_name "$asset_template" "$asset_prefix" "$version" "$arch" "$os")" || return 1
  tag_for_url="${tag_prefix}${version}"
  url="https://github.com/${repo}/releases/download/${tag_for_url}/${archive_name}"

  mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  log_info "Downloading: $url"

  # cd tylko w subshellu
  # po wyjściu z funkcji wracamy do poprzedniego katalogu
  # sprytne cd -
  (
    cd "$TMPDIR" || exit 1
    curl -fsSLO "$url"
    extract_archive_in_pwd "$archive_name"
  ) || return 1

  # shellcheck disable=SC2034
  EXTRACT_DIR="$TMPDIR"

  log_debug "download_and_extract()"
  log_debug "  version=$version"
  log_debug "  arch=$arch"
  log_debug "  os=$os"
  log_debug "  asset_template=$asset_template"
  log_debug "  archive_name=$archive_name"
  log_debug "  url=$url"
}
