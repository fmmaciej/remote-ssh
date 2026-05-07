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

asset_checksum() {
  local asset_name="$1"
  shift

  local rec
  for rec in "$@"; do
    [[ ${rec%%|*} == "$asset_name" ]] || continue
    echo "${rec#*|}"
    return 0
  done

  return 1
}

compute_sha256() {
  local file="$1"

  if have sha256sum; then
    sha256sum "$file" | sed 's/[[:space:]].*$//'
    return 0
  fi

  if have shasum; then
    shasum -a 256 "$file" | sed 's/[[:space:]].*$//'
    return 0
  fi

  return 1
}

verify_asset_checksum() {
  local asset_name="$1" expected="$2"
  local got

  got="$(compute_sha256 "$asset_name")" || {
    log_error "Cannot verify checksum for ${asset_name}: missing sha256sum or shasum."
    return 1
  }

  if [[ $got != "$expected" ]]; then
    log_error "Checksum mismatch for ${asset_name}"
    log_error "  expected: ${expected}"
    log_error "  got:      ${got}"
    return 1
  fi

  log_info "Checksum OK: ${asset_name}"
}

download_and_extract() {
  local repo="$1" release_tag="$2" asset_name="$3" binary_name="$4"
  shift 4

  local url checksum
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
    if checksum="$(asset_checksum "$asset_name" "$@")"; then
      verify_asset_checksum "$asset_name" "$checksum"
    fi
    stage_downloaded_asset "$asset_name" "$binary_name"
  ) || return 1

  # shellcheck disable=SC2034
  EXTRACT_DIR="$TMPDIR"

  log_debug "download_and_extract()"
  log_debug "  release_tag=$release_tag"
  log_debug "  asset_name=$asset_name"
  log_debug "  url=$url"
}
