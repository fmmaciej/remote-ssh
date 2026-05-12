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

remote_ssh_tool_status_classify_bin() {
  local expected_tool="$1" version="$2" local_bin="$3" path_bin="$4"

  REMOTE_SSH_TOOL_STATUS_ITEM_TARGET="[missing]"
  REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="missing"
  REMOTE_SSH_TOOL_STATUS_ITEM_PROBLEM=1

  if [[ -x "$local_bin" ]]; then
    REMOTE_SSH_TOOL_STATUS_ITEM_TARGET="$(
      remote_ssh_tool_status_read_link_target "$local_bin"
    )"
    if ! [[ -L "$local_bin" ]]; then
      REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="unmanaged-local"
    elif ! remote_ssh_tool_status_target_matches_version \
      "$REMOTE_SSH_TOOL_STATUS_ITEM_TARGET" \
      "$expected_tool" \
      "$version"; then
      REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="stale-local"
    elif [[ "$path_bin" == "$local_bin" ]]; then
      REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="ok"
      REMOTE_SSH_TOOL_STATUS_ITEM_PROBLEM=0
    elif [[ -n "$path_bin" ]]; then
      REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="path-shadowed"
    else
      REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="local-not-in-path"
    fi
  elif [[ -n "$path_bin" ]]; then
    REMOTE_SSH_TOOL_STATUS_ITEM_STATUS="external-only"
  fi
}

remote_ssh_tool_status_load() {
  local tool="$1" def_dir="$2"
  local alias_name alias_local_bin alias_path alias_target alias_status

  load_defs "$def_dir" "$tool"

  REMOTE_SSH_TOOL_STATUS_TOOL_NAME="$TOOL_NAME"
  REMOTE_SSH_TOOL_STATUS_EXPECTED="VERSION=${VERSION} ${GH_REPO}@${RELEASE_TAG}"
  REMOTE_SSH_TOOL_STATUS_LOCAL_BIN="${INSTALL_BIN_DIR}/${TOOL_NAME}"
  REMOTE_SSH_TOOL_STATUS_PATH_BIN="$(command -v "$TOOL_NAME" 2>/dev/null || true)"
  REMOTE_SSH_TOOL_STATUS_TARGET="[missing]"
  REMOTE_SSH_TOOL_STATUS_STATUS="missing"
  REMOTE_SSH_TOOL_STATUS_PROBLEM=1
  REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS=()
  REMOTE_SSH_TOOL_STATUS_STATUSES=()

  remote_ssh_tool_status_classify_bin \
    "$TOOL_NAME" \
    "$VERSION" \
    "$REMOTE_SSH_TOOL_STATUS_LOCAL_BIN" \
    "$REMOTE_SSH_TOOL_STATUS_PATH_BIN"
  REMOTE_SSH_TOOL_STATUS_TARGET="$REMOTE_SSH_TOOL_STATUS_ITEM_TARGET"
  REMOTE_SSH_TOOL_STATUS_STATUS="$REMOTE_SSH_TOOL_STATUS_ITEM_STATUS"
  REMOTE_SSH_TOOL_STATUS_PROBLEM="$REMOTE_SSH_TOOL_STATUS_ITEM_PROBLEM"
  REMOTE_SSH_TOOL_STATUS_STATUSES+=("$REMOTE_SSH_TOOL_STATUS_STATUS")

  if ((${#BINARY_ALIASES[@]} > 0)); then
    for alias_name in "${BINARY_ALIASES[@]}"; do
      alias_local_bin="${INSTALL_BIN_DIR}/${alias_name}"
      alias_path="$(command -v "$alias_name" 2>/dev/null || true)"
      remote_ssh_tool_status_classify_bin \
        "$TOOL_NAME" \
        "$VERSION" \
        "$alias_local_bin" \
        "$alias_path"
      alias_target="$REMOTE_SSH_TOOL_STATUS_ITEM_TARGET"
      alias_status="$REMOTE_SSH_TOOL_STATUS_ITEM_STATUS"
      REMOTE_SSH_TOOL_STATUS_ALIAS_RECORDS+=(
        "${alias_name}|${alias_path}|${alias_target}|${alias_status}"
      )
      REMOTE_SSH_TOOL_STATUS_STATUSES+=("$alias_status")
      if [[ "$alias_status" != "ok" ]]; then
        REMOTE_SSH_TOOL_STATUS_PROBLEM=1
      fi
    done
  fi
}
