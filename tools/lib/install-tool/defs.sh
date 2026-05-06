# shellcheck shell=bash

ensure_this_file_sourced

load_defs() {
  local def_dir="$1" tool="$2"
  local def_file="$def_dir/${tool}.sh"

  [[ -f $def_file ]] || {
    log_error "Tool '$tool' not found in $def_dir"
    exit 1
  }

  unset ASSETS BINARY_ALIASES

  # shellcheck source=/dev/null
  . "$def_file"

  : "${TOOL_NAME:?}"
  : "${GH_REPO:?}"
  : "${RELEASE_TAG:?}"
  : "${VERSION:?}"
  : "${ASSETS:?}"

  BINARY_NAME="${BINARY_NAME:-$TOOL_NAME}"

  if ! declare -p BINARY_ALIASES >/dev/null 2>&1; then
    BINARY_ALIASES=()
  fi
}
