#!/usr/bin/env bash

source_tool_libs() {
  cd "$REPO_DIR" || return
  # shellcheck source=/dev/null
  . "$REPO_DIR/tools/lib/env.sh"
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/common.lib.sh"
}

source_tool_selector_libs() {
  source_tool_libs
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/install-tool/variants.sh"
}

with_each_tool_def() {
  local callback="$1"
  local def

  for def in "$REPO_DIR"/tools/defs/*.sh; do
    unset TOOL_NAME GH_REPO DEFAULT_VERSION TAG_PREFIX BINARY_NAME BINARY_ALIASES ASSET_PREFIX VARIANTS
    # shellcheck source=/dev/null
    . "$def"
    "$callback" "$def"
  done
}

variant_asset_name() {
  local rec="$1"
  local key rest raw_os raw_arch _libc template arch_kind os_kind arch os

  key="${rec%%|*}"
  rest="${rec#*|}"
  IFS=: read -r raw_os raw_arch _libc <<<"$key"
  IFS='|' read -r template arch_kind os_kind <<<"$rest"

  arch="$(map_arch "$arch_kind" "$raw_arch")"
  os="$(map_os "$os_kind" "$raw_os")"
  build_asset_name "$template" "$ASSET_PREFIX" "$DEFAULT_VERSION" "$arch" "$os"
}

selected_asset_name() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  local selected template arch_kind os_kind arch os

  selected="$(select_variant "$raw_os" "$raw_arch" "$libc" "${VARIANTS[@]}")"
  IFS='|' read -r template arch_kind os_kind <<<"$selected"

  arch="$(map_arch "$arch_kind" "$raw_arch")"
  os="$(map_os "$os_kind" "$raw_os")"
  build_asset_name "$template" "$ASSET_PREFIX" "$DEFAULT_VERSION" "$arch" "$os"
}
