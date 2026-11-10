# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

ms_saved_release_validate() {
  local tool="$1" root="$2" mode="$3" i version layout member
  ms_row_find release "$tool" "$root" || return 1
  i=$MS_INDEX version="${MS_ROWS[i+2]}" layout="${MS_ROWS[i+3]}" member="${MS_ROWS[i+4]}"
  if [[ "$mode" == delete ]]; then remote_ssh_release_delete_valid "$root" "$tool" saved || return 1
  else remote_ssh_release_identify "$root" "$tool" saved || return 1; fi
  [[ "$REMOTE_SSH_RELEASE_VERSION" == "$version" && "$REMOTE_SSH_RELEASE_LAYOUT" == "$layout" && "$REMOTE_SSH_RELEASE_FILE" == "$member" ]]
}

ms_manifest_health() {
  local root="$1" i=0 j path kind
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == manifest && "${MS_ROWS[j]}" == "$root" ]]; then
      path="${MS_ROWS[j+1]}" kind="${MS_ROWS[j+2]}"
      remote_ssh_release_data_valid "$root" "$path" || return 1
      if [[ "$kind" == file ]]; then [[ -f "$root/$path" ]] || return 1; else [[ -d "$root/$path" ]] || return 1; fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
}

ms_tool_health() {
  local tool="$1" root="$2" i j layout member selector required_kind required_path
  ms_row_find release "$tool" "$root" || return 1
  i=$MS_INDEX layout="${MS_ROWS[i+3]}" member="${MS_ROWS[i+4]}"
  remote_ssh_release_health "$root" "$tool" "$layout" "$member" && ms_manifest_health "$root" || return 1
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == required && "${MS_ROWS[j]}" == "$tool" ]]; then
      required_path="${MS_ROWS[j+1]}" required_kind="${MS_ROWS[j+2]}"
      remote_ssh_release_data_valid "$root" "$required_path" || return 1
      case "$required_kind" in
        dir) [[ -d "$root/$required_path" ]] || return 1 ;;
        file) [[ -f "$root/$required_path" ]] || return 1 ;;
      esac
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  if [[ "$layout" == bash-builtin ]]; then
    remote_ssh_active_dir_valid || return 1
    selector="$MS_PREFIX/.active/$tool"
    remote_ssh_readlink_literal "$selector" && [[ "$REMOTE_SSH_LITERAL_TARGET" == "$root/$member" ]] || return 1
  else
    selector="$MS_BIN/$tool"
    [[ -L "$selector" && "$(remote_ssh_link_target_path "$selector")" == "$root/$member" ]] || return 1
    i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      if [[ "${MS_ROWS[i]}" == alias && "${MS_ROWS[j]}" == "$tool" ]]; then
        selector="$MS_BIN/${MS_ROWS[j+1]}"
        [[ -L "$selector" && "$(remote_ssh_link_target_path "$selector")" == "$root/$member" ]] || return 1
      fi
      i=$((i + 2 + MS_ROWS[i+1]))
    done
  fi
}

# Recovery never recursively deletes a release. A partial install may only
# restore selectors still pointing to the exact recorded new owned payload.
ms_recover_install() {
  local tool="$1" i j root="" version layout member path old_kind old_target new_target count=0
  if ms_row_find reuse-intent "$MS_BATCH" "$tool"; then ms_recover_reuse "$tool"; return "$?"; fi
  if ms_row_find publication "$MS_BATCH" "$tool"; then
    i=$MS_INDEX root="${MS_ROWS[i+3]}" version="${MS_ROWS[i+4]}" layout="${MS_ROWS[i+5]}" member="${MS_ROWS[i+6]}"
    if remote_ssh_release_identify "$root" "$tool" saved && [[ "$REMOTE_SSH_RELEASE_VERSION" == "$version" && "$REMOTE_SSH_RELEASE_LAYOUT" == "$layout" && "$REMOTE_SSH_RELEASE_FILE" == "$member" ]]; then
      ms_release_save || return 1
      if ms_tool_health "$tool" "$root"; then ms_recovered_selector_receipts "$tool" "$root" && ms_journal_complete "$tool"; return "$?"; fi
    fi
  fi
  # Without a publication intent a running staging operation has no permission
  # to publish. Complete inventory above established that there is no I/O gap.
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == link-intent && "${MS_ROWS[j]}" == "$MS_BATCH" && "${MS_ROWS[j+1]}" == "$tool" ]]; then
      count=$((count + 1))
      path="${MS_ROWS[j+2]}" old_kind="${MS_ROWS[j+3]}" old_target="${MS_ROWS[j+4]}" new_target="${MS_ROWS[j+5]}" root="${MS_ROWS[j+6]}"
      if [[ -L "$path" ]]; then
        remote_ssh_readlink_literal "$path" || return 1
        if [[ "$REMOTE_SSH_LITERAL_TARGET" == "$new_target" ]]; then
          ms_saved_release_validate "$tool" "$root" identity || return 1
          remote_ssh_selector_repair_valid "$path" "$root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$new_target" || return 1
          ms_selector_lock_required "$path" || return 1
          if [[ "$old_kind" == absent ]]; then ms_lock_mutate_guarded ms_rollback_guard 6 "$tool" "$path" "$root" "$new_target" "$old_kind" "$old_target" rm -- "$path" || return 1
          else
            # An old target must still have live B evidence from a saved selector.
            ms_old_selector_valid "$tool" "$path" "$old_target" || return 1
            ms_lock_mutate_guarded ms_rollback_guard 6 "$tool" "$path" "$root" "$new_target" "$old_kind" "$old_target" ln -sfn -- "$old_target" "$path" || return 1
          fi
        elif [[ "$old_kind" != link || "$REMOTE_SSH_LITERAL_TARGET" != "$old_target" ]]; then return 1; fi
      elif [[ -e "$path" || "$old_kind" != absent ]]; then return 1; fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  ms_journal_fail_tail "$tool"
}

ms_old_selector_valid() {
  local tool="$1" path="$2" target="$3" i root resolved
  ms_row_find selector "$tool" "$path" || return 1
  i=$MS_INDEX
  [[ "${MS_ROWS[i+2]}" == "$target" ]] || return 1
  root="${MS_ROWS[i+3]}"
  ms_saved_release_validate "$tool" "$root" identity && remote_ssh_release_member_valid "$root" "$REMOTE_SSH_RELEASE_FILE" 1 || return 1
  resolved="$target"
  [[ "$resolved" == /* ]] || resolved="${path%/*}/$resolved"
  ms_physical_path "${resolved%/*}" || return 1
  [[ "$MS_PATH/${resolved##*/}" == "$root/$REMOTE_SSH_RELEASE_FILE" ]]
}

ms_selector_lock_required() {
  if [[ "${1%/*}" == "$MS_BIN" ]]; then ms_lock_holds "$MS_BIN"; else ms_lock_holds "$MS_PREFIX" && remote_ssh_active_dir_valid; fi
}

# A completed-on-disk uninstall is recognized only from durable per-path
# intentions, a complete rescan, and absence of substitutions. Partial removal
# retains membership and receipts; unresolved objects block every new batch.
ms_recover_uninstall() {
  local tool="$1" i=0 j path kind root literal remaining=0 intentions=0 scope=0 entry
  MS_PARTIAL_ROOTS=()
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == remove-intent && "${MS_ROWS[j]}" == "$MS_BATCH" && "${MS_ROWS[j+1]}" == "$tool" ]]; then
      intentions=$((intentions + 1)) kind="${MS_ROWS[j+2]}" path="${MS_ROWS[j+3]}" literal="${MS_ROWS[j+4]}" root="${MS_ROWS[j+5]}"
      if [[ -e "$path" || -L "$path" ]]; then
        [[ "$kind" != absent ]] || return 1
        if [[ "$kind" == release ]]; then
          if ! ms_saved_release_validate "$tool" "$root" delete; then
            declare -F ms_partial_release_recognized >/dev/null && ms_partial_release_recognized "$tool" "$root" || return 1
          fi
        else
          ms_saved_release_validate "$tool" "$root" identity && remote_ssh_selector_repair_valid "$path" "$root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal" || return 1
        fi
        remaining=1
      fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  ((intentions)) || return 1
  # Required saved main names/aliases must have an explicit link-or-absence
  # intention, even when migration originally saw only an alias.
  local -a required_selectors=()
  ms_row_find tool "$tool" || return 1
  if [[ "${MS_ROWS[MS_INDEX+1]}" == bash-builtin ]]; then
    required_selectors+=("$MS_PREFIX/.active/$tool")
  else
    required_selectors+=("$MS_BIN/$tool")
    i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      if [[ "${MS_ROWS[i]}" == alias && "${MS_ROWS[j]}" == "$tool" ]]; then required_selectors+=("$MS_BIN/${MS_ROWS[j+1]}"); fi
      i=$((i + 2 + MS_ROWS[i+1]))
    done
  fi
  for path in "${required_selectors[@]}"; do
    scope=0 i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      if [[ "${MS_ROWS[i]}" == remove-intent && "${MS_ROWS[j]}" == "$MS_BATCH" && "${MS_ROWS[j+1]}" == "$tool" && "${MS_ROWS[j+3]}" == "$path" ]]; then scope=1; fi
      i=$((i + 2 + MS_ROWS[i+1]))
    done
    ((scope)) || return 1
  done
  # Every recorded release/selector for the tool must be covered by an intent.
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ ( "${MS_ROWS[i]}" == release || "${MS_ROWS[i]}" == selector ) && "${MS_ROWS[j]}" == "$tool" ]]; then
      path="${MS_ROWS[j+1]}" scope=0
      local k=0
      while ((k < ${#MS_ROWS[@]})); do
        if [[ "${MS_ROWS[k]}" == remove-intent && "${MS_ROWS[k+2]}" == "$MS_BATCH" && "${MS_ROWS[k+3]}" == "$tool" && "${MS_ROWS[k+5]}" == "$path" ]]; then scope=1; fi
        k=$((k + 2 + MS_ROWS[k+1]))
      done
      ((scope)) || return 1
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  # A newly discovered own release is an unresolved change, not silent success.
  for entry in ${MS_LIVE_RELEASES[@]+"${MS_LIVE_RELEASES[@]}"}; do
    if remote_ssh_release_delete_valid "$entry" "$tool" saved; then
      ms_row_find release "$tool" "$entry" || return 1
    fi
  done
  for root in ${MS_PARTIAL_ROOTS[@]+"${MS_PARTIAL_ROOTS[@]}"}; do
    ms_row_drop protected "$tool" "$root"
    ms_row_add protected "$tool" "$root" partial || return 1
  done
  if ((remaining)); then ms_journal_fail_tail "$tool"
  else
    # Receipts remain as tombstone evidence until the journal is archived.
    ms_journal_complete "$tool"
  fi
}

ms_recovery_gate() {
  local i j tool action status
  ms_lock_holds "$MS_PREFIX" || return 1
  if ! ms_journal_active; then MS_GATE_PASSED="$MS_GENERATION"; return 0; fi
  if [[ "$MS_BATCH_PHASE" == settled ]]; then MS_GATE_PASSED="$MS_GENERATION"; return 0; fi
  if [[ "$MS_BATCH_PHASE" != tools ]]; then
    declare -F ms_refresh_recover >/dev/null && ms_refresh_recover || return 1
    MS_GATE_PASSED="$MS_GENERATION"
    return 0
  fi
  ms_inventory_live || return 1
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == cli-intent && "${MS_ROWS[j]}" == "$MS_BATCH" ]]; then
      if [[ -e "${MS_ROWS[j+1]}" || -L "${MS_ROWS[j+1]}" ]]; then
        remote_ssh_readlink_literal "${MS_ROWS[j+1]}" && [[ "$REMOTE_SSH_LITERAL_TARGET" == "${MS_ROWS[j+2]}" ]] || return 1
      fi
      MS_ROWS[j+3]="done"
    fi
    if [[ "${MS_ROWS[i]}" == item && "${MS_ROWS[j]}" == "$MS_BATCH" ]]; then
      tool="${MS_ROWS[j+1]}" action="${MS_ROWS[j+2]}" status="${MS_ROWS[j+3]}"
      case "$status" in
        running)
          if [[ "$action" == install ]]; then ms_recover_install "$tool" || return 1
          else ms_recover_uninstall "$tool" || return 1; fi
          # Rows may have moved after a membership/claim change.
          i=0; continue ;;
        queued) MS_ROWS[j+3]=not-run MS_ROWS[j+5]=settled ;;
      esac
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  ms_row_find batch "$MS_BATCH" || return 1
  MS_ROWS[MS_INDEX+2]=settled
  ms_state_commit || return 1
  MS_GATE_PASSED="$MS_GENERATION"
}


ms_rollback_guard() {
  local tool="$1" path="$2" root="$3" literal="$4" old_kind="$5" old_target="$6"
  ms_saved_release_validate "$tool" "$root" identity &&
    remote_ssh_selector_repair_valid "$path" "$root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal" || return 1
  [[ "$old_kind" == absent ]] || ms_old_selector_valid "$tool" "$path" "$old_target"
}
