# shellcheck shell=bash

ensure_this_file_sourced

install_tool_binary_path_valid() {
  local LC_ALL=C
  remote_ssh_relative_path_valid "$1" || return 1
  [[ "$1" != *[[:cntrl:]]* ]]
}

install_tool_binary_name_valid() {
  [[ -n "$1" && "$1" != */* ]] && install_tool_binary_path_valid "$1"
}

load_defs() {
  local def_dir="$1" tool="$2"
  local def_file="$def_dir/${tool}.sh"

  [[ -f $def_file ]] || {
    log_error "Tool '$tool' not found in $def_dir"
    exit 1
  }

  unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME ASSETS CHECKSUMS BINARY_ALIASES
  unset INSTALL_LAYOUT BINARY_PATH BUNDLE_ROOTS LIBRARY_MEMBERS REMOTE_SSH_BINARY_PATH_EXPLICIT

  # shellcheck source=/dev/null
  . "$def_file"

  : "${TOOL_NAME:?}"
  : "${GH_REPO:?}"
  : "${RELEASE_TAG:?}"
  : "${VERSION:?}"
  : "${ASSETS:?}"

  BINARY_NAME="${BINARY_NAME:-$TOOL_NAME}"
  install_tool_binary_name_valid "$BINARY_NAME" || {
    local escaped_name
    printf -v escaped_name '%q' "$BINARY_NAME"
    log_error "Invalid BINARY_NAME: $escaped_name"
    return 1
  }
  INSTALL_LAYOUT="${INSTALL_LAYOUT:-binary}"
  # Keep the public default while distinguishing a definition's explicit path.
  # shellcheck disable=SC2034
  REMOTE_SSH_BINARY_PATH_EXPLICIT=0
  if [[ ${BINARY_PATH+x} ]]; then
    # shellcheck disable=SC2034
    REMOTE_SSH_BINARY_PATH_EXPLICIT=1
  fi
  BINARY_PATH="${BINARY_PATH-$BINARY_NAME}"
  case "$INSTALL_LAYOUT" in binary|bundle|bash-builtin) ;; *) log_error "Invalid INSTALL_LAYOUT: $INSTALL_LAYOUT"; return 1 ;; esac
  install_tool_binary_path_valid "$BINARY_PATH" || {
    local escaped_path
    printf -v escaped_path '%q' "$BINARY_PATH"
    log_error "Invalid BINARY_PATH: $escaped_path"
    return 1
  }

  if ! declare -p BINARY_ALIASES >/dev/null 2>&1; then
    BINARY_ALIASES=()
  fi
  if ! declare -p CHECKSUMS >/dev/null 2>&1; then
    CHECKSUMS=()
  fi
  if ! declare -p BUNDLE_ROOTS >/dev/null 2>&1; then
    BUNDLE_ROOTS=()
  fi
  if ! declare -p LIBRARY_MEMBERS >/dev/null 2>&1; then LIBRARY_MEMBERS=(); fi
  if [[ "$INSTALL_LAYOUT" == bash-builtin ]]; then
    [[ ${#BINARY_ALIASES[@]} == 0 && ${#LIBRARY_MEMBERS[@]} -gt 0 ]] || {
      log_error 'bash-builtin requires LIBRARY_MEMBERS and does not support executable aliases'
      return 1
    }
  fi
}

library_member_for_asset() {
  local record member found=""
  for record in ${LIBRARY_MEMBERS[@]+"${LIBRARY_MEMBERS[@]}"}; do
    [[ "${record%%|*}" == "$1" ]] || continue
    member="${record#*|}"
    install_tool_binary_path_valid "$member" && [[ -z "$found" ]] || return 1
    found="$member"
  done
  [[ -n "$found" ]] || { log_error "No library member declared for $1"; return 1; }
  printf '%s\n' "$found"
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
