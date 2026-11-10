# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

ms_uninstall_preflight() {
  local tool path root other i j kind literal required found terminal
  local -a paths=() prefix_entries=() roots=() saved_roots=()
  MS_PREFLIGHT=() MS_UNINSTALL_TOOLS=() MS_UNINSTALL_LINKS=() MS_UNINSTALL_ROOTS=() MS_UNINSTALL_PROTECTED=() MS_EXECUTABLES=0
  ms_inventory_live && ms_claims_collect || return 1
  [[ "$MS_ADOPTED" != 0 ]] || ms_migration_preview || return 1
  if [[ -d "$MS_PREFIX" ]]; then ms_inventory_children "$MS_PREFIX" || return 1; prefix_entries=("${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}"); fi
  for tool in "$@"; do
    if [[ -f "$TOOLS_DIR/defs/$tool.sh" ]]; then load_defs "$TOOLS_DIR/defs" "$tool" || return 1
      if ! ms_row_find tool "$tool"; then ms_metadata_save "$tool" || return 1; fi
    else ms_row_find tool "$tool" || return 1; fi
    terminal=0
    ms_tool_uninstall_terminal "$tool" && terminal=1
    ms_tool_selectors "$tool" || return 1
    paths=("${MS_VALUES[@]+"${MS_VALUES[@]}"}") roots=() saved_roots=()
    i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      if ((terminal == 0)) && [[ "${MS_ROWS[i]}" == release && "${MS_ROWS[j]}" == "$tool" ]]; then saved_roots+=("${MS_ROWS[j+1]}"); fi
      i=$((i + 2 + MS_ROWS[i+1]))
    done
    MS_VALUES=()
    for root in "${saved_roots[@]+"${saved_roots[@]}"}"; do
      if [[ -e "$root" || -L "$root" ]]; then
        ms_saved_release_validate "$tool" "$root" delete || { ms_error "required release lacks live deletion proof: $root"; return 1; }
      fi
      ms_append_unique "$root"
    done
    roots=("${MS_VALUES[@]+"${MS_VALUES[@]}"}")
    for root in ${prefix_entries[@]+"${prefix_entries[@]}"}; do
      [[ "${root##*/}" == "$tool-"* ]] || continue
      if remote_ssh_release_delete_valid "$root" "$tool" saved; then
        ms_release_save || return 1
        MS_VALUES=("${roots[@]+"${roots[@]}"}"); ms_append_unique "$root"; roots=("${MS_VALUES[@]}")
      else MS_UNINSTALL_PROTECTED+=("$root"); fi
    done
    # Include every proven own custom alias in the current bin/active inventory.
    for path in ${MS_LIVE_LINKS[@]+"${MS_LIVE_LINKS[@]}"}; do
      if remote_ssh_release_for_link "$path" "$tool" >/dev/null; then
        MS_VALUES=("${paths[@]+"${paths[@]}"}"); ms_append_unique "$path"; paths=("${MS_VALUES[@]}")
      else
        kind=$?; ((kind == 1)) || return 1
      fi
    done
    found=0
    ms_member_has "$tool" && found=1
    ((${#roots[@]} == 0)) || found=1
    # All required paths, including absences, are checked before deciding no-op.
    local -a tool_links=()
    for path in ${paths[@]+"${paths[@]}"}; do
      ms_inspect_selector "$tool" "$path" || return 1
      kind="$MS_SELECTOR_KIND" literal="$MS_SELECTOR_LITERAL" root="$MS_SELECTOR_ROOT"
      if [[ "$kind" == link ]]; then found=1
        MS_VALUES=("${roots[@]+"${roots[@]}"}"); ms_append_unique "$root"; roots=("${MS_VALUES[@]}")
      elif ((terminal == 0)) && ms_row_find selector "$tool" "$path"; then root="${MS_ROWS[MS_INDEX+3]}"; fi
      tool_links+=("$tool" "$path" "$kind" "$literal" "$root")
      MS_PREFLIGHT+=("$tool" "$path" "$kind" "$literal" "$root")
    done
    if ((found)); then
      ((${#roots[@]})) || { ms_error "member has no release receipts: $tool"; return 1; }
      for root in "${roots[@]}"; do
        for other in ${MS_FOREIGN_CLAIM_PATHS[@]+"${MS_FOREIGN_CLAIM_PATHS[@]}"}; do
          [[ "$root" != "$other" ]] || { ms_error "release claimed by another location: $root"; return 1; }
        done
        ms_row_find release "$tool" "$root" || return 1
        i=$MS_INDEX
        MS_UNINSTALL_ROOTS+=("$tool" "$root")
        MS_PREFLIGHT+=(release "$tool" "$root" "${MS_ROWS[i+2]}" "${MS_ROWS[i+3]}" "${MS_ROWS[i+4]}")
      done
      i=0
      while ((i < ${#MS_ROWS[@]})); do
        j=$((i + 2))
        if [[ "${MS_ROWS[i]}" == protected && "${MS_ROWS[j]}" == "$tool" ]]; then
          path="${MS_ROWS[j+1]}" required=0
          for root in "${roots[@]}"; do [[ "$root" != "$path" ]] || required=1; done
          if ((required == 0)) && [[ -e "$path" || -L "$path" ]]; then
            MS_VALUES=("${MS_UNINSTALL_PROTECTED[@]+"${MS_UNINSTALL_PROTECTED[@]}"}")
            ms_append_unique "$path"; MS_UNINSTALL_PROTECTED=("${MS_VALUES[@]}")
          fi
        fi
        i=$((i + 2 + MS_ROWS[i+1]))
      done
      MS_UNINSTALL_TOOLS+=("$tool")
      for ((i=0; i<${#tool_links[@]}; i+=5)); do
        [[ -n "${tool_links[i+4]}" ]] || tool_links[i+4]="${roots[0]}"
        [[ "${tool_links[i+1]%/*}" != "$MS_BIN" ]] || MS_EXECUTABLES=1
      done
      MS_UNINSTALL_LINKS+=("${tool_links[@]}")
    fi
  done
}

ms_uninstall_link_guard() {
  local tool="$1" path="$2" root="$3" literal="$4"
  ms_saved_release_validate "$tool" "$root" delete &&
    remote_ssh_selector_repair_valid "$path" "$root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal"
}

ms_uninstall_release_guard() {
  local tool="$1" root="$2" path target other
  ms_saved_release_validate "$tool" "$root" delete && ms_claims_collect && ms_inventory_live || return 1
  for other in ${MS_FOREIGN_CLAIM_PATHS[@]+"${MS_FOREIGN_CLAIM_PATHS[@]}"}; do [[ "$root" != "$other" ]] || return 1; done
  for path in ${MS_LIVE_LINKS[@]+"${MS_LIVE_LINKS[@]}"}; do
    if target="$(remote_ssh_link_target_path "$path")"; then
      case "$target" in "$root/"*) return 1 ;; esac
    else
      target=$?; ((target == 1)) || return 1
    fi
  done
}

ms_capture_removal_manifest() {
  local root="$1" entry rel kind
  ms_tree_inventory "$root" || return 1
  ms_row_drop manifest "$root"
  for entry in ${MS_TREE[@]+"${MS_TREE[@]}"}; do
    rel="${entry#"$root/"}"
    [[ "$rel" != .remote-ssh-release ]] || continue
    remote_ssh_relative_path_valid "$rel" || return 1
    if [[ -L "$entry" ]]; then continue
    elif [[ -d "$entry" ]]; then kind=dir
    elif [[ -f "$entry" ]]; then kind="file"
    else continue; fi
    ms_row_add manifest "$root" "$rel" "$kind" || return 1
  done
}

# Classification after a recorded failed recursive deletion grants NO deletion
# authority. It only allows retaining the member and protecting an entirely
# recognized ordinary remainder, so a later install/update can repair it.
ms_partial_release_recognized() {
  local tool="$1" root="$2" i member entry rel kind
  ms_saved_release_validate "$tool" "$root" identity || return 1
  member="$REMOTE_SSH_RELEASE_FILE"
  ms_row_find manifest "$root" "$member" || return 1
  [[ "${MS_ROWS[MS_INDEX+2]}" == file ]] || return 1
  ms_tree_inventory "$root" || return 1
  for entry in ${MS_TREE[@]+"${MS_TREE[@]}"}; do
    rel="${entry#"$root/"}"
    [[ "$rel" != .remote-ssh-release ]] || continue
    [[ ! -L "$entry" ]] || return 1
    ms_row_find manifest "$root" "$rel" || return 1
    i=$MS_INDEX kind="${MS_ROWS[i+2]}"
    remote_ssh_release_data_valid "$root" "$rel" || return 1
    if [[ "$kind" == dir ]]; then [[ -d "$entry" ]] || return 1; else [[ -f "$entry" ]] || return 1; fi
  done
  MS_PARTIAL_ROOTS+=("$root")
  return 0
}

ms_uninstall_one() {
  local tool="$1" i root path kind literal intent_kind
  ms_journal_item "$tool" running removing || return 1
  for ((i=0; i<${#MS_UNINSTALL_ROOTS[@]}; i+=2)); do
    [[ "${MS_UNINSTALL_ROOTS[i]}" == "$tool" ]] || continue
    root="${MS_UNINSTALL_ROOTS[i+1]}"
    if [[ -e "$root" || -L "$root" ]]; then
      ms_saved_release_validate "$tool" "$root" delete && ms_capture_removal_manifest "$root" || return 1
    fi
    ms_row_add remove-intent "$MS_BATCH" "$tool" release "$root" "" "$root" intended required || return 1
  done
  for ((i=0; i<${#MS_UNINSTALL_LINKS[@]}; i+=5)); do
    [[ "${MS_UNINSTALL_LINKS[i]}" == "$tool" ]] || continue
    path="${MS_UNINSTALL_LINKS[i+1]}" kind="${MS_UNINSTALL_LINKS[i+2]}" literal="${MS_UNINSTALL_LINKS[i+3]}" root="${MS_UNINSTALL_LINKS[i+4]}"
    intent_kind="$kind"
    ms_row_add remove-intent "$MS_BATCH" "$tool" "$intent_kind" "$path" "$literal" "$root" intended required || return 1
  done
  ms_state_commit || return 1
  for ((i=0; i<${#MS_UNINSTALL_LINKS[@]}; i+=5)); do
    [[ "${MS_UNINSTALL_LINKS[i]}" == "$tool" ]] || continue
    path="${MS_UNINSTALL_LINKS[i+1]}" kind="${MS_UNINSTALL_LINKS[i+2]}" literal="${MS_UNINSTALL_LINKS[i+3]}" root="${MS_UNINSTALL_LINKS[i+4]}"
    if [[ "$kind" == link ]]; then
      ms_selector_lock_required "$path" && ms_lock_mutate_guarded ms_uninstall_link_guard 4 "$tool" "$path" "$root" "$literal" rm -- "$path" || return 1
    else [[ ! -e "$path" && ! -L "$path" ]] || return 1; fi
    ms_row_find remove-intent "$MS_BATCH" "$tool" "$kind" || return 1
    # There may be multiple link intentions; match the path explicitly.
    ms_remove_mark_done "$tool" "$path" || return 1
  done
  for ((i=0; i<${#MS_UNINSTALL_ROOTS[@]}; i+=2)); do
    [[ "${MS_UNINSTALL_ROOTS[i]}" == "$tool" ]] || continue
    root="${MS_UNINSTALL_ROOTS[i+1]}"
    if [[ -e "$root" || -L "$root" ]]; then
      ms_lock_mutate_guarded ms_uninstall_release_guard 2 "$tool" "$root" rm -rf -- "$root" || return 1
    fi
    ms_remove_mark_done "$tool" "$root" || return 1
  done
  ms_inventory_live && ms_recover_uninstall "$tool" || return 1
  ms_row_find item "$MS_BATCH" "$tool" && [[ "${MS_ROWS[MS_INDEX+3]}" == completed ]] || return 1
  printf 'completed: %s\n' "$tool"
}

ms_remove_mark_done() {
  local tool="$1" path="$2" i=0 j
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == remove-intent && "${MS_ROWS[j]}" == "$MS_BATCH" && "${MS_ROWS[j+1]}" == "$tool" && "${MS_ROWS[j+3]}" == "$path" ]]; then
      MS_ROWS[j+6]="done"
      ms_state_commit
      return "$?"
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  return 1
}

ms_uninstall_batch() {
  local tool
  ms_journal_begin uninstall uninstall "$@" || return 1
  for tool in "$@"; do
    if ! ms_uninstall_one "$tool"; then
      printf 'Uninstall incomplete: %s\n' "$tool" >&2
      if ms_state_load; then ms_recovery_gate || :; ms_batch_report; fi
      return 1
    fi
  done
  ms_recovery_gate && ms_batch_report
}
