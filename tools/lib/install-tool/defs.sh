# shellcheck shell=bash

ensure_this_file_sourced

load_defs() {
  local def_dir="$1" tool="$2"
  local def_file="$def_dir/${tool}.sh"

  [[ -f $def_file ]] || {
    log_error "Tool '$tool' not found in $def_dir"
    exit 1
  }

  unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME ASSETS CHECKSUMS BINARY_ALIASES
  unset INSTALL_LAYOUT BINARY_PATH BUNDLE_ROOTS

  # shellcheck source=/dev/null
  . "$def_file"

  : "${TOOL_NAME:?}"
  : "${GH_REPO:?}"
  : "${RELEASE_TAG:?}"
  : "${VERSION:?}"
  : "${ASSETS:?}"

  BINARY_NAME="${BINARY_NAME:-$TOOL_NAME}"
  INSTALL_LAYOUT="${INSTALL_LAYOUT:-binary}"
  BINARY_PATH="${BINARY_PATH:-$BINARY_NAME}"
  case "$INSTALL_LAYOUT" in binary|bundle) ;; *) log_error "Invalid INSTALL_LAYOUT: $INSTALL_LAYOUT"; return 1 ;; esac
  remote_ssh_relative_path_valid "$BINARY_PATH" || return 1

  if ! declare -p BINARY_ALIASES >/dev/null 2>&1; then
    BINARY_ALIASES=()
  fi
  if ! declare -p CHECKSUMS >/dev/null 2>&1; then
    CHECKSUMS=()
  fi
  if ! declare -p BUNDLE_ROOTS >/dev/null 2>&1; then
    BUNDLE_ROOTS=()
  fi
}

bundle_root_for_asset() {
  local asset="$1" record root
  for record in ${BUNDLE_ROOTS[@]+"${BUNDLE_ROOTS[@]}"}; do
    [[ "${record%%|*}" == "$asset" ]] || continue
    root="${record#*|}"
    remote_ssh_relative_path_valid "$root" || return 1
    printf '%s\n' "$root"
    return 0
  done
  log_error "No bundle root declared for $asset"
  return 1
}
