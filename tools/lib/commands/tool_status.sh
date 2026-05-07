# shellcheck shell=bash
# shellcheck disable=SC2034,SC2153

ensure_this_file_sourced

remote_ssh_tool_status_print_path_value() {
  local value="$1"

  if [[ -n "$value" ]]; then
    printf '%s\n' "$value"
  else
    printf '[missing]\n'
  fi
}

remote_ssh_tool_status_read_link_target() {
  local path="$1"

  if [[ -L "$path" ]]; then
    readlink "$path"
  else
    printf '%s\n' "$path"
  fi
}

remote_ssh_tool_status_target_matches_version() {
  local target="$1" tool="$2" version="$3"

  case "$target" in
    "$INSTALL_PREFIX/${tool}-${version}/"* | "$INSTALL_PREFIX/${tool}-${version}".*/*)
      return 0
      ;;
  esac

  return 1
}

remote_ssh_tool_status_load() {
  local tool="$1" def_dir="$2"
  local alias_name alias_path

  load_defs "$def_dir" "$tool"

  REMOTE_SSH_TOOL_STATUS_TOOL_NAME="$TOOL_NAME"
  REMOTE_SSH_TOOL_STATUS_EXPECTED="VERSION=${VERSION} ${GH_REPO}@${RELEASE_TAG}"
  REMOTE_SSH_TOOL_STATUS_LOCAL_BIN="${INSTALL_BIN_DIR}/${TOOL_NAME}"
  REMOTE_SSH_TOOL_STATUS_PATH_BIN="$(command -v "$TOOL_NAME" 2>/dev/null || true)"
  REMOTE_SSH_TOOL_STATUS_TARGET="[missing]"
  REMOTE_SSH_TOOL_STATUS_STATUS="missing"
  REMOTE_SSH_TOOL_STATUS_PROBLEM=1
  REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS=()

  if [[ -x "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN" ]]; then
    REMOTE_SSH_TOOL_STATUS_TARGET="$(
      remote_ssh_tool_status_read_link_target "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN"
    )"
    if ! [[ -L "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN" ]]; then
      REMOTE_SSH_TOOL_STATUS_STATUS="unmanaged-local"
    elif ! remote_ssh_tool_status_target_matches_version \
      "$REMOTE_SSH_TOOL_STATUS_TARGET" \
      "$TOOL_NAME" \
      "$VERSION"; then
      REMOTE_SSH_TOOL_STATUS_STATUS="stale-local"
    elif [[ "$REMOTE_SSH_TOOL_STATUS_PATH_BIN" == "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN" ]]; then
      REMOTE_SSH_TOOL_STATUS_STATUS="ok"
      REMOTE_SSH_TOOL_STATUS_PROBLEM=0
    elif [[ -n "$REMOTE_SSH_TOOL_STATUS_PATH_BIN" ]]; then
      REMOTE_SSH_TOOL_STATUS_STATUS="path-shadowed"
    else
      REMOTE_SSH_TOOL_STATUS_STATUS="local-not-in-path"
    fi
  elif [[ -n "$REMOTE_SSH_TOOL_STATUS_PATH_BIN" ]]; then
    REMOTE_SSH_TOOL_STATUS_STATUS="external-only"
  fi

  if ((${#BINARY_ALIASES[@]} > 0)); then
    for alias_name in "${BINARY_ALIASES[@]}"; do
      alias_path="$(command -v "$alias_name" 2>/dev/null || true)"
      REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS+=("${alias_name}|${alias_path}")
    done
  fi
}
