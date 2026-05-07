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
  . "$TOOLS_LIB_DIR/install-tool/assets.sh"
}

with_each_tool_def() {
  local callback="$1"
  local def
  local failed=0

  for def in "$REPO_DIR"/tools/defs/*.sh; do
    unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME BINARY_ALIASES ASSETS CHECKSUMS
    # shellcheck source=/dev/null
    . "$def"
    "$callback" "$def" || failed=1
  done

  return "$failed"
}

manifest_asset_key() {
  local rec="$1"
  echo "${rec%%|*}"
}

manifest_asset_name() {
  local rec="$1"
  echo "${rec#*|}"
}

selected_asset_name() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  select_asset "$raw_os" "$raw_arch" "$libc" "${ASSETS[@]}"
}
