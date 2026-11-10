# shellcheck shell=bash
# shellcheck disable=SC2034,SC2153

ensure_this_file_sourced

ms_append_unique() {
  local value="$1" item
  for item in ${MS_VALUES[@]+"${MS_VALUES[@]}"}; do [[ "$item" != "$value" ]] || return 0; done
  MS_VALUES+=("$value")
}

ms_tool_selectors() {
  local tool="$1" i=0 j saved_layout="" current_layout="" alias
  MS_VALUES=()
  if ms_row_find tool "$tool"; then saved_layout="${MS_ROWS[MS_INDEX+1]}"; fi
  if [[ -f "$TOOLS_DIR/defs/$tool.sh" ]]; then
    load_defs "$TOOLS_DIR/defs" "$tool" || return 1
    current_layout="$INSTALL_LAYOUT"
    if [[ "$current_layout" != bash-builtin ]]; then
      ms_append_unique "$MS_BIN/$tool"
      for alias in ${BINARY_ALIASES[@]+"${BINARY_ALIASES[@]}"}; do ms_basename "$alias" && ms_append_unique "$MS_BIN/$alias" || return 1; done
    else ms_append_unique "$MS_PREFIX/.active/$tool"; fi
  fi
  if [[ "$saved_layout" == bash-builtin ]]; then ms_append_unique "$MS_PREFIX/.active/$tool"
  elif [[ -n "$saved_layout" ]]; then ms_append_unique "$MS_BIN/$tool"; fi
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[j]}" == "$tool" ]]; then
      case "${MS_ROWS[i]}" in
        selector) ms_append_unique "${MS_ROWS[j+1]}" ;;
        alias) ms_append_unique "$MS_BIN/${MS_ROWS[j+1]}" ;;
      esac
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
}

# Existing selectors need live C, or an already saved exact B receipt. This
# records evidence only in memory; it never changes membership by itself.
ms_inspect_selector() {
  local tool="$1" path="$2" i root literal version layout member foreign
  MS_SELECTOR_KIND=absent MS_SELECTOR_LITERAL="" MS_SELECTOR_ROOT=""
  for foreign in ${MS_FOREIGN_CLAIM_SELECTORS[@]+"${MS_FOREIGN_CLAIM_SELECTORS[@]}"}; do
    [[ "$path" != "$foreign" ]] || { ms_error "selector claimed by another location: $path"; return 1; }
  done
  if [[ "${path%/*}" == "$MS_PREFIX/.active" && ( -e "$MS_PREFIX/.active" || -L "$MS_PREFIX/.active" ) ]]; then
    remote_ssh_active_dir_valid || return 1
  fi
  [[ -e "$path" || -L "$path" ]] || return 0
  [[ -L "$path" ]] || { ms_error "protected selector: $path"; return 1; }
  remote_ssh_readlink_literal "$path" || return 1
  literal="$REMOTE_SSH_LITERAL_TARGET"
  if remote_ssh_release_for_link "$path" "$tool" >/dev/null; then
    root="$REMOTE_SSH_RELEASE_DIR"
    ms_release_save || return 1
  else
    ms_row_find selector "$tool" "$path" || { ms_error "unproved selector: $path"; return 1; }
    i=$MS_INDEX
    [[ "${MS_ROWS[i+2]}" == "$literal" ]] || return 1
    root="${MS_ROWS[i+3]}"
    ms_row_find release "$tool" "$root" || return 1
    i=$MS_INDEX version="${MS_ROWS[i+2]}" layout="${MS_ROWS[i+3]}" member="${MS_ROWS[i+4]}"
    remote_ssh_selector_repair_valid "$path" "$root" "$tool" "$version" "$layout" "$member" "$literal" || return 1
  fi
  ms_row_drop selector "$tool" "$path"
  ms_row_add selector "$tool" "$path" "$literal" "$root" || return 1
  MS_SELECTOR_KIND=link MS_SELECTOR_LITERAL="$literal" MS_SELECTOR_ROOT="$root"
}


ms_select_install_asset() {
  local tool="$1" platform os arch libc
  load_defs "$TOOLS_DIR/defs" "$tool" || return 2
  [[ "$TOOL_NAME" == "$tool" ]] && ms_version "$VERSION" || return 2
  platform="$(default_platform)" && IFS=: read -r os arch libc <<<"$platform" || return 2
  MS_SELECTED_ASSET="$(select_asset "$os" "$arch" "$libc" ${ASSETS[@]+"${ASSETS[@]}"})" || return 1
  case "$INSTALL_LAYOUT" in
    bundle)
      SELECTED_BUNDLE_ROOT="$(bundle_root_for_asset "$MS_SELECTED_ASSET")" || return 2
      MS_SELECTED_MEMBER="$BINARY_PATH" ;;
    bash-builtin)
      SELECTED_LIBRARY_MEMBER="$(library_member_for_asset "$MS_SELECTED_ASSET")" || return 2
      asset_checksum "$MS_SELECTED_ASSET" ${CHECKSUMS[@]+"${CHECKSUMS[@]}"} >/dev/null || { ms_error 'library asset requires its pinned checksum'; return 2; }
      MS_SELECTED_MEMBER="$SELECTED_LIBRARY_MEMBER" ;;
    *) MS_SELECTED_MEMBER="$BINARY_NAME" ;;
  esac
}

# Full selection preflight before consent and again after prior-journal recovery.
# Snapshot is a NUL-safe flat array, compared field-for-field by the facade.
ms_install_preflight() {
  local tool path i j other status
  MS_PREFLIGHT=() MS_EXECUTABLES=0
  ms_inventory_live && ms_claims_collect || return 1
  [[ "$MS_ADOPTED" != 0 ]] || ms_migration_preview || return 1
  local -a paths=() seen=()
  for tool in "$@"; do
    [[ -f "$TOOLS_DIR/defs/$tool.sh" ]] || return 1
    if ms_select_install_asset "$tool"; then :
    else
      status=$?
      [[ "${MS_ALLOW_UNSUPPORTED:-0}" == 1 && "$status" == 1 ]] || return 1
    fi
    ms_metadata_save "$tool" || return 1
    MS_PREFLIGHT+=(definition "$tool" "$VERSION" "$INSTALL_LAYOUT" "$BINARY_PATH")
    ms_tool_selectors "$tool" || return 1
    paths=("${MS_VALUES[@]}")
    for path in "${paths[@]}"; do
      [[ "$path" != "$MS_BIN/remote-ssh" ]] || { ms_error "tool selector conflicts with management CLI: $path"; return 1; }
      for other in ${seen[@]+"${seen[@]}"}; do [[ "$path" != "$other" ]] || { ms_error "duplicate selector in selection: $path"; return 1; }; done
      seen+=("$path")
      [[ "${path%/*}" != "$MS_BIN" ]] || MS_EXECUTABLES=1
      ms_inspect_selector "$tool" "$path" || return 1
      MS_PREFLIGHT+=("$tool" "$path" "$MS_SELECTOR_KIND" "$MS_SELECTOR_LITERAL" "$MS_SELECTOR_ROOT")
    done
  done
}

ms_snapshot_equal() {
  local i
  ((${#MS_APPROVED[@]} == ${#MS_PREFLIGHT[@]})) || return 1
  for ((i=0; i<${#MS_APPROVED[@]}; i++)); do [[ "${MS_APPROVED[i]}" == "${MS_PREFLIGHT[i]}" ]] || return 1; done
}

ms_set_effective_pair() {
  INSTALL_PREFIX="$MS_PREFIX" INSTALL_BIN_DIR="$MS_BIN"
  export INSTALL_PREFIX INSTALL_BIN_DIR
}

ms_create_roots() {
  local prefix="$MS_PREFIX" bin="$MS_BIN" create_bin="$1"
  mkdir -p -- "$prefix" || return 1
  [[ "$create_bin" == 0 ]] || mkdir -p -- "$bin" || return 1
  ms_pair_resolve && [[ "$prefix" == "$MS_PREFIX" && "$bin" == "$MS_BIN" ]] || return 1
  ms_set_effective_pair
}

ms_tree_inventory() {
  local root="$1" entry status extra trailer=0
  MS_TREE=()
  local -a found=()
  [[ -d "$root" && ! -L "$root" && -O "$root" ]] || return 1
  while IFS= read -r -d '' entry; do
    if [[ -z "$entry" ]]; then
      IFS= read -r -d '' status && [[ "$status" == 0 ]] || return 1
      extra=""
      if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
      trailer=1; break
    fi
    [[ "$entry" == "$root/"* ]] || return 1
    found+=("$entry")
  done < <(find "$root" -mindepth 1 -print0; status=$?; printf '\0%s\0' "$status")
  ((trailer)) || return 1
  MS_TREE=("${found[@]+"${found[@]}"}")
}

ms_stage_manifest() {
  local stage="$1" final="$2" entry rel kind
  ms_tree_inventory "$stage" || return 1
  ms_row_drop manifest "$final"
  for entry in ${MS_TREE[@]+"${MS_TREE[@]}"}; do
    rel="${entry#"$stage/"}"
    [[ "$rel" != .remote-ssh-release ]] || continue
    remote_ssh_relative_path_valid "$rel" && [[ ! -L "$entry" && -r "$entry" ]] || return 1
    if [[ -d "$entry" ]]; then kind=dir; elif [[ -f "$entry" ]]; then kind="file"; else return 1; fi
    ms_row_add manifest "$final" "$rel" "$kind" || return 1
  done
}

# Runs only in a staging child. Its download EXIT trap cannot replace the
# owning process's ticket cleanup. It has no permission to publish links/state.
ms_stage_build() (
  local stage="$1" asset="$2" member="$3" source rel reason
  download_and_extract "$GH_REPO" "$RELEASE_TAG" "$asset" "$BINARY_NAME" ${CHECKSUMS[@]+"${CHECKSUMS[@]}"} || return 1
  if [[ "$INSTALL_LAYOUT" == bundle ]]; then
    source="$EXTRACT_DIR/$SELECTED_BUNDLE_ROOT" rel="$BINARY_PATH"
  elif [[ "$INSTALL_LAYOUT" == bash-builtin ]]; then
    source="$EXTRACT_DIR" rel="$SELECTED_LIBRARY_MEMBER"
  else
    source="$EXTRACT_DIR"
    if [[ "$REMOTE_SSH_BINARY_PATH_EXPLICIT" == 1 ]]; then rel="$BINARY_PATH"
    else rel="$(find_binary_path_by_name "$source" "$BINARY_NAME")" || return 1; fi
  fi
  if [[ "$INSTALL_LAYOUT" == bash-builtin ]]; then
    install_binary_check_path "$source" "$rel" library || return 1
    cp -R "$source/." "$stage/" && install_library_probe "$stage/$rel" "$TOOL_NAME" &&
      remote_ssh_library_release_write "$stage" "$TOOL_NAME" "$VERSION" "$member" || return 1
  else
    reason="$(install_binary_check_path "$source" "$rel")" || { log_error "Invalid candidate: $reason"; return 1; }
    if [[ "$INSTALL_LAYOUT" == bundle ]]; then cp -R "$source/." "$stage/" || return 1
    else cp -- "$source/$rel" "$stage/$member" || return 1; fi
    remote_ssh_release_write "$stage" "$TOOL_NAME" "$VERSION" "$INSTALL_LAYOUT" "$member" || return 1
  fi
)

ms_stage_guard() {
  local tool="$1" stage="$2" final="$3" version="$4" layout="$5" member="$6" value expected i=0 j path kind
  [[ "${stage%/*}" == "$MS_PREFIX" && -d "$stage" && ! -L "$stage" && -O "$stage" &&
    ! -e "$final" && ! -L "$final" ]] || return 1
  [[ -f "$stage/.remote-ssh-release" && ! -L "$stage/.remote-ssh-release" && -r "$stage/.remote-ssh-release" && -O "$stage/.remote-ssh-release" ]] || return 1
  value="$(command -p cat "$stage/.remote-ssh-release" && printf '\001')" || return 1
  if [[ "$layout" == bash-builtin ]]; then
    printf -v expected 'format=2\ntool=%s\nversion=%s\nlayout=bash-builtin\nlibrary=%s\n\001' "$tool" "$version" "$member"
  else printf -v expected 'format=1\ntool=%s\nversion=%s\nlayout=%s\nexecutable=%s\n\001' "$tool" "$version" "$layout" "$member"; fi
  [[ "$value" == "$expected" ]] && remote_ssh_release_member_valid "$stage" "$member" || return 1
  if [[ "$layout" == bash-builtin ]]; then [[ -r "$stage/$member" ]] || return 1; else [[ -x "$stage/$member" ]] || return 1; fi
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == manifest && "${MS_ROWS[j]}" == "$final" ]]; then
      path="${MS_ROWS[j+1]}" kind="${MS_ROWS[j+2]}"
      remote_ssh_release_data_valid "$stage" "$path" || return 1
      if [[ "$kind" == dir ]]; then [[ -d "$stage/$path" ]] || return 1; else [[ -f "$stage/$path" ]] || return 1; fi
    elif [[ "${MS_ROWS[i]}" == required && "${MS_ROWS[j]}" == "$tool" ]]; then
      remote_ssh_release_data_valid "$stage" "${MS_ROWS[j+1]}" || return 1
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
}

ms_absent_guard() { [[ ! -e "$1" && ! -L "$1" && -d "${1%/*}" && ! -L "${1%/*}" ]]; }

ms_link_publish_guard() {
  local tool="$1" path="$2" kind="$3" literal="$4" old_root="$5" new_root="$6"
  ms_saved_release_validate "$tool" "$new_root" delete || return 1
  if [[ "$kind" == absent ]]; then ms_absent_guard "$path"
  else
    ms_saved_release_validate "$tool" "$old_root" identity &&
      remote_ssh_selector_repair_valid "$path" "$old_root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal"
  fi
}

ms_install_one() {
  local tool="$1" asset member root="" stage final path i j kind literal old_root
  local -a paths=()
  load_defs "$TOOLS_DIR/defs" "$tool" || return 1
  ms_select_install_asset "$tool" || return 1
  asset="$MS_SELECTED_ASSET" member="$MS_SELECTED_MEMBER"
  ms_metadata_save "$tool" || return 1
  ms_journal_item "$tool" running staging || return 1
  ms_tool_selectors "$tool" || return 1
  paths=("${MS_VALUES[@]}")
  path="$MS_BIN/$tool"
  [[ "$INSTALL_LAYOUT" != bash-builtin ]] || path="$MS_PREFIX/.active/$tool"
  if remote_ssh_release_for_link "$path" "$tool" >/dev/null &&
    [[ "$REMOTE_SSH_RELEASE_VERSION" == "$VERSION" && "$REMOTE_SSH_RELEASE_LAYOUT" == "$INSTALL_LAYOUT" && "$REMOTE_SSH_RELEASE_FILE" == "$member" ]]; then
    root="$REMOTE_SSH_RELEASE_DIR"
    ms_release_save || return 1
    if ms_tool_health "$tool" "$root"; then
      ms_row_add reuse-intent "$MS_BATCH" "$tool" "$root" "$VERSION" "$INSTALL_LAYOUT" "$member" && ms_state_commit || return 1
      ms_journal_complete "$tool" || return 1
      printf 'completed: %s (reused pinned release)\n' "$tool"
      return 0
    fi
  fi
  final="$(choose_release_dir "$tool" "$VERSION" "$MS_PREFIX/$tool-$VERSION")" || return 1
  stage="$MS_PREFIX/.$tool-$VERSION.tmp.$$-$RANDOM"
  # Save complete old selector states and allowed publication scope first.
  ms_row_add publication "$MS_BATCH" "$tool" "$stage" "$final" "$VERSION" "$INSTALL_LAYOUT" "$member" intended || return 1
  for path in "${paths[@]}"; do
    ms_inspect_selector "$tool" "$path" || return 1
    ms_row_add link-intent "$MS_BATCH" "$tool" "$path" "$MS_SELECTOR_KIND" "$MS_SELECTOR_LITERAL" "$final/$member" "$final" intended || return 1
  done
  ms_state_commit || return 1
  ms_lock_mutate_guarded ms_absent_guard 1 "$stage" mkdir -m 700 -- "$stage" || return 1
  ms_stage_build "$stage" "$asset" "$member" && ms_stage_manifest "$stage" "$final" || return 1
  ms_stage_guard "$tool" "$stage" "$final" "$VERSION" "$INSTALL_LAYOUT" "$member" || return 1
  ms_journal_item "$tool" running publishing || return 1
  ms_lock_mutate_guarded ms_stage_guard 6 "$tool" "$stage" "$final" "$VERSION" "$INSTALL_LAYOUT" "$member" mv -- "$stage" "$final" || return 1
  remote_ssh_release_delete_valid "$final" "$tool" && ms_release_save || return 1
  ms_row_find publication "$MS_BATCH" "$tool" || return 1
  MS_ROWS[MS_INDEX+7]=renamed
  ms_state_commit || return 1
  for path in "${paths[@]}"; do
    ms_row_find link-intent "$MS_BATCH" "$tool" "$path" || return 1
    i=$MS_INDEX kind="${MS_ROWS[i+3]}" literal="${MS_ROWS[i+4]}" old_root=""
    if [[ "$kind" == link ]]; then
      ms_row_find selector "$tool" "$path" || return 1
      old_root="${MS_ROWS[MS_INDEX+3]}"
    fi
    if [[ "${path%/*}" == "$MS_PREFIX/.active" && ! -e "$MS_PREFIX/.active" && ! -L "$MS_PREFIX/.active" ]]; then
      ms_lock_mutate_guarded ms_absent_guard 1 "$MS_PREFIX/.active" mkdir -- "$MS_PREFIX/.active" || return 1
    fi
    ms_selector_lock_required "$path" || return 1
    if [[ "$kind" == absent ]]; then
      ms_lock_mutate_guarded ms_link_publish_guard 6 "$tool" "$path" "$kind" "$literal" "$old_root" "$final" ln -s -- "$final/$member" "$path" || return 1
    else
      ms_lock_mutate_guarded ms_link_publish_guard 6 "$tool" "$path" "$kind" "$literal" "$old_root" "$final" ln -sfn -- "$final/$member" "$path" || return 1
    fi
    remote_ssh_readlink_literal "$path" && [[ "$REMOTE_SSH_LITERAL_TARGET" == "$final/$member" ]] || return 1
    ms_row_find link-intent "$MS_BATCH" "$tool" "$path" || return 1
    MS_ROWS[MS_INDEX+7]="done"
    ms_state_commit || return 1
  done
  ms_tool_health "$tool" "$final" || return 1
  # Save new selector receipts only after all aliases are healthy. Until then
  # old exact receipts remain available for safe rollback after a crash.
  for path in "${paths[@]}"; do
    ms_row_drop selector "$tool" "$path"
    ms_row_add selector "$tool" "$path" "$final/$member" "$final" || return 1
  done
  ms_journal_complete "$tool" || return 1
  printf 'completed: %s\n' "$tool"
}

ms_batch_report() {
  local i=0 j
  ms_journal_active || return 0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    [[ "${MS_ROWS[i]}" != item ]] || printf '%s: %s\n' "${MS_ROWS[j+3]}" "${MS_ROWS[j+1]}"
    i=$((i + 2 + MS_ROWS[i+1]))
  done
}

ms_install_batch() {
  local tool
  ms_journal_begin "${MS_OPERATION:-install}" install "$@" || return 1
  if [[ "${MS_PUBLISH_CLI:-0}" == 1 ]]; then ms_cli_publish || return 1; fi
  for tool in "$@"; do
    if ! ms_install_one "$tool"; then
      printf 'Installation incomplete: %s\n' "$tool" >&2
      # Reload after any uncertain state write before attempting normalization.
      if ms_state_load; then
        ms_journal_active || return 1
        if ms_row_find item "$MS_BATCH" "$tool" && [[ "${MS_ROWS[MS_INDEX+3]}" == queued ]]; then ms_journal_fail_tail "$tool" || :; fi
        ms_recovery_gate || :; ms_batch_report
      fi
      return 1
    fi
  done
  ms_recovery_gate && ms_batch_report
}


ms_lock_set_matches() {
  local root item found count=0
  local -a seen=()
  for root in "${MS_REQUIRED_LOCKS[@]}"; do
    ms_physical_path "$root" || return 1
    root="$MS_PATH" found=0
    for item in ${seen[@]+"${seen[@]}"}; do [[ "$root" != "$item" ]] || found=1; done
    if ((found == 0)); then ms_lock_holds "$root" || return 1; seen+=("$root"); count=$((count + 1)); fi
  done
  [[ "$count" == "${#MS_LOCK_ROOTS[@]}" ]]
}

ms_cli_guard() {
  [[ -f "$INSTALL_CLI_SOURCE" && ! -L "$INSTALL_CLI_SOURCE" && -O "$INSTALL_CLI_SOURCE" ]] && install_cli_check_destination
}
ms_cli_publish() {
  ms_cli_guard || return 1
  if [[ ! -L "$MS_BIN/remote-ssh" || ! -x "$INSTALL_CLI_SOURCE" ]]; then
    ms_row_add cli-intent "$MS_BATCH" "$MS_BIN/remote-ssh" "$INSTALL_CLI_SOURCE" intended && ms_state_commit || return 1
    ms_lock_holds "$MS_BIN" || return 1
    if [[ ! -x "$INSTALL_CLI_SOURCE" ]]; then
      ms_lock_mutate_guarded ms_cli_guard 0 chmod +x "$INSTALL_CLI_SOURCE" || return 1
    fi
    if [[ ! -L "$MS_BIN/remote-ssh" ]]; then
      ms_lock_mutate_guarded ms_cli_guard 0 ln -s -- "$INSTALL_CLI_SOURCE" "$MS_BIN/" || return 1
    fi
    remote_ssh_readlink_literal "$MS_BIN/remote-ssh" && [[ "$REMOTE_SSH_LITERAL_TARGET" == "$INSTALL_CLI_SOURCE" ]] || return 1
    ms_row_find cli-intent "$MS_BATCH" || return 1
    MS_ROWS[MS_INDEX+3]="done"
    ms_state_commit || return 1
  fi
}

ms_print_selection() {
  local title="$1"; shift
  printf '%s\n' "$title"
  (($#)) && printf '  %s\n' "$@"
  return 0
}
ms_confirm() {
  local action="$1" answer
  if [[ ! -t 0 ]]; then printf '%s requires TTY confirmation; use --yes for non-interactive operation.\n' "$action" >&2; return 1; fi
  printf '%s selected tools? [y/N] ' "$action"
  IFS= read -r answer || return 1
  case "$answer" in y|Y|yes|YES) return 0 ;; *) printf 'Aborted.\n' >&2; return 1 ;; esac
}


# Validate exact publication targets, then store their new receipts atomically
# with recovered completion. Losing a payload after recovery must remain B
# repairable just as after an uninterrupted install.
ms_recovered_selector_receipts() {
  local tool="$1" root="$2" i=0 j path literal saved_root
  local -a receipts=()
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == link-intent && "${MS_ROWS[j]}" == "$MS_BATCH" && "${MS_ROWS[j+1]}" == "$tool" ]]; then
      path="${MS_ROWS[j+2]}" literal="${MS_ROWS[j+5]}" saved_root="${MS_ROWS[j+6]}"
      [[ "$saved_root" == "$root" ]] && remote_ssh_readlink_literal "$path" && [[ "$REMOTE_SSH_LITERAL_TARGET" == "$literal" ]] || return 1
      receipts+=("$path" "$literal" "$root")
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  for ((i=0; i<${#receipts[@]}; i+=3)); do
    ms_row_drop selector "$tool" "${receipts[i]}"
    ms_row_add selector "$tool" "${receipts[i]}" "${receipts[i+1]}" "${receipts[i+2]}" || return 1
  done
}

ms_recover_reuse() {
  local tool="$1" i root version layout member path literal saved_root
  ms_row_find reuse-intent "$MS_BATCH" "$tool" || return 1
  i=$MS_INDEX root="${MS_ROWS[i+2]}" version="${MS_ROWS[i+3]}" layout="${MS_ROWS[i+4]}" member="${MS_ROWS[i+5]}"
  ms_saved_release_validate "$tool" "$root" identity && [[ "$REMOTE_SSH_RELEASE_VERSION" == "$version" && "$REMOTE_SSH_RELEASE_LAYOUT" == "$layout" && "$REMOTE_SSH_RELEASE_FILE" == "$member" ]] || return 1
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    if [[ "${MS_ROWS[i]}" == selector && "${MS_ROWS[i+2]}" == "$tool" ]]; then
      path="${MS_ROWS[i+3]}" literal="${MS_ROWS[i+4]}" saved_root="${MS_ROWS[i+5]}"
      if [[ -e "$path" || -L "$path" ]]; then
        ms_saved_release_validate "$tool" "$saved_root" identity && remote_ssh_selector_repair_valid "$path" "$saved_root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal" || return 1
      fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  if ms_tool_health "$tool" "$root"; then ms_journal_complete "$tool"; else ms_journal_fail_tail "$tool"; fi
}
