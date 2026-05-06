# shellcheck shell=bash

ensure_this_file_sourced

stage_downloaded_asset() {
  local asset_name="$1" binary_name="$2"

  case "$asset_name" in
  *.tar.gz | *.tgz | *.zip)
    extract_archive_in_pwd "$asset_name"
    ;;
  *)
    chmod +x "$asset_name"
    if [[ $asset_name != "$binary_name" ]]; then
      cp "$asset_name" "$binary_name"
      chmod +x "$binary_name"
    fi
    ;;
  esac
}

download_and_extract() {
  local repo="$1" release_tag="$2" asset_name="$3" binary_name="$4"

  local url
  url="https://github.com/${repo}/releases/download/${release_tag}/${asset_name}"

  mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  log_info "Downloading: $url"

  # cd tylko w subshellu
  # po wyjściu z funkcji wracamy do poprzedniego katalogu
  # sprytne cd -
  (
    cd "$TMPDIR" || exit 1
    curl -fsSLo "$asset_name" "$url"
    stage_downloaded_asset "$asset_name" "$binary_name"
  ) || return 1

  # shellcheck disable=SC2034
  EXTRACT_DIR="$TMPDIR"

  log_debug "download_and_extract()"
  log_debug "  release_tag=$release_tag"
  log_debug "  asset_name=$asset_name"
  log_debug "  url=$url"
}
