# shellcheck shell=bash

ensure_this_file_sourced

install_tool_main() {
  local script_dir="$1" tool="$2" req_version="$3"

  local def_dir="${script_dir}/../defs"

  load_defs "$def_dir" "$tool" || exit 1
  check_req_tools || exit 1

  if [[ -n $req_version && $req_version != "$VERSION" ]]; then
    log_error "Tool '${tool}' uses an exact asset manifest and supports only VERSION=${VERSION}; requested '${req_version}'."
    exit 1
  fi

  local plat raw_os raw_arch libc
  plat="$(detect_platform)"
  IFS='|' read -r raw_os raw_arch <<<"$plat"
  libc="$(detect_libc "$raw_os")"

  local asset_name
  asset_name="$(select_asset "$raw_os" "$raw_arch" "$libc" "${ASSETS[@]}")" || {
    log_error "No matching asset for ${tool}: platform=${raw_os}/${raw_arch}/${libc}, os=${raw_os}, arch=${raw_arch}, libc=${libc}"
    printf 'Available assets:\n' >&2
    printf '  - %s\n' "${ASSETS[@]}" >&2
    exit 1
  }

  log_info "Installing: ${GH_REPO}, version=${VERSION}, raw=${raw_os}/${raw_arch}, libc=${libc}"

  download_and_extract "$GH_REPO" "$RELEASE_TAG" "$asset_name" "$BINARY_NAME" || exit 1

  install_binary "$TOOL_NAME" "$BINARY_NAME" "$VERSION" "$EXTRACT_DIR" "${BINARY_ALIASES[@]}" || exit 1
}
