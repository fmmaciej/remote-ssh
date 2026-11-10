# shellcheck shell=bash
# shellcheck disable=SC2034,SC2153

ensure_this_file_sourced

ms_status_add() {
  local value="$1" item
  for item in ${MS_STATUS_TAGS[@]+"${MS_STATUS_TAGS[@]}"}; do [[ "$item" != "$value" ]] || return 0; done
  MS_STATUS_TAGS+=("$value")
  [[ "${2:-1}" == 0 ]] || MS_STATUS_PROBLEM=1
}

# Last actual result is diagnostic data. A current item supersedes archived
# history; failed/pending scope remains visible without inventing membership.
ms_status_last_operation() {
  local tool="$1" i=0 j current="" archived=""
  MS_STATUS_OPERATION="" MS_STATUS_OUTCOME=""
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[j+1]:-}" == "$tool" ]]; then
      case "${MS_ROWS[i]}" in
        item) current="${MS_ROWS[j+2]}:${MS_ROWS[j+3]}" ;;
        result) archived="${MS_ROWS[j+2]}:${MS_ROWS[j+3]}" ;;
      esac
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  MS_STATUS_OPERATION="${current:-$archived}"
  MS_STATUS_OUTCOME="${MS_STATUS_OPERATION#*:}"
}

ms_report_model() {
  local entry tool i=0 item inserted
  MS_CATALOG=() MS_NAMES=() MS_REPORT_LEGACY_HINTS=0
  MS_REPORT_PLATFORM="$(default_platform)" || return 1
  ms_inventory_children "$TOOLS_DIR/defs" && ms_inventory_live && ms_claims_collect || return 1
  # Inventory calls above reuse their output array; capture the catalog afresh.
  ms_inventory_children "$TOOLS_DIR/defs" || return 1
  for entry in ${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}; do
    [[ "$entry" == *.sh ]] || continue
    [[ -f "$entry" && ! -L "$entry" && -r "$entry" ]] || return 1
    tool="${entry##*/}" tool="${tool%.sh}"
    ms_name "$tool" || return 1
    MS_CATALOG+=("$tool")
  done
  if [[ "$MS_ADOPTED" == 0 ]]; then
    if [[ -e "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" || -L "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" ]]; then MS_REPORT_LEGACY_HINTS=1; fi
    ms_legacy_hints "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" && ms_migration_preview || return 1
  fi
  MS_VALUES=("${MS_CATALOG[@]+"${MS_CATALOG[@]}"}")
  while ((i < ${#MS_ROWS[@]})); do
    if [[ "${MS_ROWS[i]}" == member ]]; then ms_append_unique "${MS_ROWS[i+2]}"
    elif [[ "${MS_ROWS[i]}" == tool ]]; then
      ms_status_last_operation "${MS_ROWS[i+2]}"
      case "$MS_STATUS_OUTCOME" in failed|not-run|running|queued) ms_append_unique "${MS_ROWS[i+2]}" ;; esac
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  local -a sorted=() next=()
  local LC_ALL=C
  for tool in ${MS_VALUES[@]+"${MS_VALUES[@]}"}; do
    next=() inserted=0
    for item in ${sorted[@]+"${sorted[@]}"}; do
      if ((inserted == 0)) && [[ "$tool" < "$item" ]]; then next+=("$tool"); inserted=1; fi
      next+=("$item")
    done
    ((inserted)) || next+=("$tool")
    sorted=("${next[@]}")
  done
  MS_NAMES=("${sorted[@]+"${sorted[@]}"}")
}

ms_status_known() { [[ -f "$TOOLS_DIR/defs/$1.sh" ]] || ms_row_find tool "$1"; }

ms_status_load() {
  local tool="$1" mode="$2" i j path root="" literal="" expected_version="" expected_layout="" expected_member="" status owned winner kind saved_literal saved_root alias_name terminal=0
  local -a paths=()
  MS_STATUS_TAGS=() MS_STATUS_ALIASES=() MS_STATUS_PROBLEM=0 MS_STATUS_SUPPORT=retired MS_STATUS_EXPECTED='[no current definition]'
  MS_STATUS_TOOL="$tool" MS_STATUS_MEMBERSHIP=unmanaged MS_STATUS_ROOT="" MS_STATUS_VERSION='[missing]' MS_STATUS_LAYOUT='[unknown]' MS_STATUS_TARGET='[missing]' MS_STATUS_PATH='[missing]'
  if ms_member_has "$tool"; then
    if [[ "$MS_ADOPTED" == 0 ]]; then MS_STATUS_MEMBERSHIP=adoption-pending; ms_status_add adoption-pending 0
    else MS_STATUS_MEMBERSHIP=managed; fi
  fi
  if [[ -f "$TOOLS_DIR/defs/$tool.sh" ]]; then
    load_defs "$TOOLS_DIR/defs" "$tool" || return 2
    expected_version="$VERSION" expected_layout="$INSTALL_LAYOUT" MS_STATUS_EXPECTED="VERSION=$VERSION $GH_REPO@$RELEASE_TAG"
    if ms_select_install_asset "$tool"; then MS_STATUS_SUPPORT=supported; expected_member="$MS_SELECTED_MEMBER"
    else status=$?; ((status == 1)) || return 2; MS_STATUS_SUPPORT=unsupported; ms_status_add unsupported; fi
    ms_metadata_save "$tool" || return 2
  else ms_status_add retired; fi
  ms_status_last_operation "$tool"
  ms_tool_uninstall_terminal "$tool" && terminal=1
  case "$MS_STATUS_OUTCOME" in
    failed|not-run) ms_status_add "$MS_STATUS_OUTCOME" ;;
    queued|running) ms_status_add pending ;;
  esac
  ms_tool_selectors "$tool" || return 2
  paths=("${MS_VALUES[@]+"${MS_VALUES[@]}"}")
  if ms_row_find tool "$tool"; then MS_STATUS_LAYOUT="${MS_ROWS[MS_INDEX+1]}"; fi
  MS_STATUS_LOCAL="$MS_BIN/$tool"
  [[ "$MS_STATUS_LAYOUT" != bash-builtin ]] || MS_STATUS_LOCAL="$MS_PREFIX/.active/$tool"
  # Prefer a real active receipt, then the saved primary/alias receipt. No
  # health failure is allowed to erase automatic membership.
  for path in ${paths[@]+"${paths[@]}"}; do
    if remote_ssh_release_for_link "$path" "$tool" >/dev/null; then root="$REMOTE_SSH_RELEASE_DIR"; ms_release_save || return 2; break
    else status=$?; ((status == 1)) || return 2; fi
  done
  if [[ -z "$root" && "$terminal" == 0 ]]; then
    if ms_row_find selector "$tool" "$MS_STATUS_LOCAL"; then root="${MS_ROWS[MS_INDEX+3]}"
    else
      for path in ${paths[@]+"${paths[@]}"}; do
        if ((terminal == 0)) && ms_row_find selector "$tool" "$path"; then root="${MS_ROWS[MS_INDEX+3]}"; break; fi
      done
    fi
  fi
  if [[ -n "$root" ]] && ms_row_find release "$tool" "$root"; then
    i=$MS_INDEX MS_STATUS_VERSION="${MS_ROWS[i+2]}" MS_STATUS_LAYOUT="${MS_ROWS[i+3]}" MS_STATUS_ROOT="$root"
    [[ -z "$expected_version" || "$expected_version" == "$MS_STATUS_VERSION" ]] || ms_status_add stale
    [[ -z "$expected_layout" || "$expected_layout" == "$MS_STATUS_LAYOUT" ]] || ms_status_add broken
    [[ -z "$expected_member" || "$expected_member" == "${MS_ROWS[i+4]}" ]] || ms_status_add broken
  fi
  for path in ${paths[@]+"${paths[@]}"}; do
    owned=0 literal='[missing]' status=ok
    if [[ -L "$path" ]]; then
      remote_ssh_readlink_literal "$path" || return 2
      literal="$REMOTE_SSH_LITERAL_TARGET"
      if [[ ! -e "$path" ]]; then ms_status_add missing; ms_status_add broken; fi
      if remote_ssh_release_for_link "$path" "$tool" >/dev/null; then
        owned=1
        if [[ -n "$root" && "$root" != "$REMOTE_SSH_RELEASE_DIR" ]]; then status=broken; ms_status_add broken; fi
      else
        j=$?; ((j == 1)) || return 2
        if ms_row_find selector "$tool" "$path"; then
          i=$MS_INDEX saved_literal="${MS_ROWS[i+2]}" saved_root="${MS_ROWS[i+3]}"
          if [[ "$literal" == "$saved_literal" ]] && ms_saved_release_validate "$tool" "$saved_root" identity &&
            remote_ssh_selector_repair_valid "$path" "$saved_root" "$tool" "$REMOTE_SSH_RELEASE_VERSION" "$REMOTE_SSH_RELEASE_LAYOUT" "$REMOTE_SSH_RELEASE_FILE" "$literal"; then owned=1; fi
        fi
      fi
      if ((owned == 0)); then status=protected; ms_status_add protected; ms_status_add broken; fi
    elif [[ -e "$path" ]]; then status=unmanaged-local; ms_status_add unmanaged-local; ms_status_add protected
    else
      status=missing
      if [[ "$mode" == check || "$MS_STATUS_MEMBERSHIP" != unmanaged || -n "$root" ]]; then
        ms_status_add missing
        [[ "$path" == "$MS_STATUS_LOCAL" ]] || ms_status_add broken
      fi
    fi
    winner='[library; no executable PATH required]'
    if [[ "${path%/*}" == "$MS_BIN" ]]; then
      alias_name="${path##*/}"
      winner="$(command -v "$alias_name" 2>/dev/null || :)"
      kind="$(type -t "$alias_name" 2>/dev/null || :)"
      if ((owned)) && [[ -x "$path" ]]; then
        if [[ "$kind" == file && -n "$winner" && "$winner" -ef "$path" ]]; then :
        elif [[ -n "$winner" ]]; then status="path-shadowed"; ms_status_add path-shadowed
        else status=local-not-in-path; ms_status_add local-not-in-path; fi
      elif [[ "$mode" == check && -n "$winner" && ! -e "$path" && ! -L "$path" ]]; then
        status=external-only; ms_status_add external-only
      fi
      [[ -n "$winner" ]] || winner='[missing]'
    fi
    if [[ "$path" == "$MS_STATUS_LOCAL" ]]; then MS_STATUS_TARGET="$literal" MS_STATUS_PATH="$winner"
    else MS_STATUS_ALIASES+=("${path##*/}" "$status" "$literal" "$winner"); fi
  done
  if [[ -n "$root" ]]; then
    if ms_tool_health "$tool" "$root"; then
      ms_status_add installed 0
      ((MS_STATUS_PROBLEM)) || ms_status_add ok 0
    else ms_status_add broken; fi
  elif [[ "$mode" == list && "$MS_STATUS_MEMBERSHIP" == unmanaged && "$MS_STATUS_SUPPORT" == supported && ${#MS_STATUS_TAGS[@]} == 0 ]]; then ms_status_add available 0
  elif [[ "$mode" == check ]]; then ms_status_add missing; fi
  MS_STATUS_TEXT=""
  for status in ${MS_STATUS_TAGS[@]+"${MS_STATUS_TAGS[@]}"}; do MS_STATUS_TEXT="${MS_STATUS_TEXT:+$MS_STATUS_TEXT }$status"; done
  [[ -n "$MS_STATUS_TEXT" ]] || MS_STATUS_TEXT=available
  [[ "$MS_STATUS_SUPPORT" != unsupported ]] || MS_STATUS_TEXT="$MS_STATUS_TEXT platform=$MS_REPORT_PLATFORM"
  [[ -z "$MS_STATUS_OPERATION" ]] || MS_STATUS_TEXT="$MS_STATUS_TEXT last=$MS_STATUS_OPERATION"
}
