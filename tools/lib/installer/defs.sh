# shellcheck shell=bash

ensure_this_file_sourced

load_defs() {
  local def_dir="$1" tool="$2"
  local def_file="$def_dir/${tool}.sh"

  [[ -f "$def_file" ]] || { log_error "Tool '$tool' not found in $def_dir"; exit 1; }

  # shellcheck source=/dev/null
  . "$def_file"

  : "${TOOL_NAME:?}"
  : "${GH_REPO:?}"
  : "${DEFAULT_VERSION:?}"
  : "${VARIANTS:?}"

  BINARY_NAME="${BINARY_NAME:-$TOOL_NAME}"
  TAG_PREFIX="${TAG_PREFIX:-}"
}
