# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

ms_metadata_save() {
  local tool="$1" alias required
  # Current requirements may change; immutable per-release manifests retain
  # the old payload inventory independently. Retired tools keep saved metadata.
  ms_row_drop required "$tool"
  ms_row_drop tool "$tool"
  ms_row_add tool "$tool" "$INSTALL_LAYOUT" "$BINARY_PATH" || return 1
  for alias in ${BINARY_ALIASES[@]+"${BINARY_ALIASES[@]}"}; do
    ms_basename "$alias" || return 1
    ms_row_find alias "$tool" "$alias" || ms_row_add alias "$tool" "$alias"
  done
  for required in ${BUNDLE_REQUIRED_PATHS[@]+"${BUNDLE_REQUIRED_PATHS[@]}"}; do
    ms_row_find required "$tool" "$required" || ms_row_add required "$tool" "$required" any
  done
}

ms_release_save() {
  ms_row_drop release "$REMOTE_SSH_RELEASE_TOOL" "$REMOTE_SSH_RELEASE_DIR"
  ms_row_add release "$REMOTE_SSH_RELEASE_TOOL" "$REMOTE_SSH_RELEASE_DIR" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE"
}

ms_migration_preview() {
  local link tool root status alias declared foreign claimed
  [[ "$MS_ADOPTED" == 0 ]] || return 0
  # No mutation until all enumeration and readlink I/O has succeeded. In-memory
  # partial results are discarded by the caller on any nonzero return.
  ms_claims_collect && ms_inventory_live || return 1
  local -a links=("${MS_LIVE_LINKS[@]+"${MS_LIVE_LINKS[@]}"}") releases=("${MS_LIVE_RELEASES[@]+"${MS_LIVE_RELEASES[@]}"}")
  for link in ${links[@]+"${links[@]}"}; do
    if remote_ssh_release_for_link "$link" >/dev/null; then
      tool="$REMOTE_SSH_RELEASE_TOOL" root="$REMOTE_SSH_RELEASE_DIR" claimed=0
      for foreign in ${MS_FOREIGN_CLAIM_SELECTORS[@]+"${MS_FOREIGN_CLAIM_SELECTORS[@]}"}; do [[ "$link" != "$foreign" ]] || claimed=1; done
      for foreign in ${MS_FOREIGN_CLAIM_PATHS[@]+"${MS_FOREIGN_CLAIM_PATHS[@]}"}; do [[ "$root" != "$foreign" ]] || claimed=1; done
      ((claimed == 0)) || continue
      load_defs "$TOOLS_DIR/defs" "$tool" || return 1
      declared=0
      if [[ "$REMOTE_SSH_RELEASE_LAYOUT" == bash-builtin ]]; then
        [[ "$link" != "$MS_PREFIX/.active/$tool" ]] || declared=1
      elif [[ "${link%/*}" == "$MS_BIN" ]]; then
        [[ "${link##*/}" != "$tool" ]] || declared=1
        for alias in ${BINARY_ALIASES[@]+"${BINARY_ALIASES[@]}"}; do [[ "${link##*/}" != "$alias" ]] || declared=1; done
      fi
      ((declared)) || continue
      ms_metadata_save "$tool" && ms_release_save && ms_member_set "$tool" 1 || return 1
      remote_ssh_readlink_literal "$link" || return 1
      ms_row_drop selector "$tool" "$link"
      ms_row_add selector "$tool" "$link" "$REMOTE_SSH_LITERAL_TARGET" "$root" || return 1
    else
      status=$?
      ((status == 1)) || return 1
    fi
  done
  # Inactive releases are claims/evidence only, never new members.
  for root in ${releases[@]+"${releases[@]}"}; do
    claimed=0
    for foreign in ${MS_FOREIGN_CLAIM_PATHS[@]+"${MS_FOREIGN_CLAIM_PATHS[@]}"}; do [[ "$root" != "$foreign" ]] || claimed=1; done
    ((claimed == 0)) || continue
    if remote_ssh_release_validate "$root"; then
      ms_release_save || return 1
    fi
  done
  ms_rows_validate
}

# expected-tools is never consulted for membership. This bounded hint parser is
# optional and used only for the informational fzf migration warning.
ms_legacy_hints() {
  local file="$1" line
  [[ -e "$file" || -L "$file" ]] || return 0
  [[ -f "$file" && ! -L "$file" && -r "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in fzf) MS_FZF_HINT=1 ;; esac
  done <"$file"
}

ms_migration_commit() {
  ms_lock_holds "$MS_PREFIX" && [[ "$MS_ADOPTED" == 0 ]] || return 1
  ms_migration_preview || return 1
  MS_ADOPTED=1
  ms_state_commit
}
