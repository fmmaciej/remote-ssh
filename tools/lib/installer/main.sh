# shellcheck shell=bash

ensure_this_file_sourced

install_tool_main() {
  local script_dir="$1" tool="$2" req_version="$3"

  local def_dir="${script_dir}/../defs"

  load_defs "$def_dir" "$tool" || exit 1
  check_req_tools || exit 1

  local plat raw_os raw_arch libc
  plat="$(detect_platform)"
  IFS='|' read -r raw_os raw_arch <<<"$plat"
  libc="$(detect_libc "$raw_os")"

  local selected
  selected="$(select_variant "$raw_os" "$raw_arch" "$libc" "${VARIANTS[@]}")" || {
    log_error "No matching variant for ${tool}: ${raw_os}/${raw_arch}/${libc}"
    printf '  - %s\n' "${VARIANTS[@]}" >&2
    exit 1
  }
  apply_selected_variant "$selected"

  local version
  version="$(resolve_version "$req_version" "$DEFAULT_VERSION" "$GH_REPO" "$TAG_PREFIX")" || {
    log_error "Could not resolve version"
    exit 1
  }

  log_info "Installing: ${GH_REPO}, version=${version}, raw=${raw_os}/${raw_arch}, libc=${libc}"

  download_and_extract "$GH_REPO" "$TAG_PREFIX" "$version" \
    "$ASSET_PREFIX" "$ASSET_TEMPLATE" "$ARCH_KIND" "$OS_KIND" \
    "$raw_arch" "$raw_os" || exit 1

  install_binary "$TOOL_NAME" "$BINARY_NAME" "$version" "$EXTRACT_DIR" || exit 1
}
