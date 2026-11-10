# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

# One producer emits an impossible empty filename plus an explicit final status.
# The consumer waits for EOF too, so partial output or a failed find is an error.
# No temporary files, pipeline subshells, or lost process-substitution statuses.
ms_inventory_children() {
  local root="$1" entry status trailer=0 extra
  local -a entries=()
  MS_INVENTORY=()
  [[ -d "$root" && ! -L "$root" && -r "$root" && -x "$root" ]] || return 1
  while IFS= read -r -d '' entry; do
    if [[ -z "$entry" ]]; then
      IFS= read -r -d '' status || return 1
      [[ "$status" == 0 ]] || return 1
      trailer=1
      extra=""
      if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
      break
    fi
    [[ "${entry%/*}" == "$root" ]] || return 1
    entries+=("$entry")
  done < <(find "$root" -mindepth 1 -maxdepth 1 -print0; status=$?; printf '\0%s\0' "$status")
  ((trailer == 1)) || return 1
  MS_INVENTORY=("${entries[@]+"${entries[@]}"}")
}

ms_inventory_live() {
  MS_LIVE_LINKS=() MS_LIVE_RELEASES=()
  local entry
  if [[ -e "$MS_BIN" || -L "$MS_BIN" ]]; then
    ms_inventory_children "$MS_BIN" || return 1
    for entry in ${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}; do
      [[ ! -L "$entry" ]] || MS_LIVE_LINKS+=("$entry")
    done
  fi
  if [[ -e "$MS_PREFIX" || -L "$MS_PREFIX" ]]; then
    ms_inventory_children "$MS_PREFIX" || return 1
    for entry in ${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}; do
      [[ ! -d "$entry" || -L "$entry" ]] || MS_LIVE_RELEASES+=("$entry")
    done
  fi
  if [[ -e "$MS_PREFIX/.active" || -L "$MS_PREFIX/.active" ]]; then
    remote_ssh_active_dir_valid || return 1
    ms_inventory_children "$MS_PREFIX/.active" || return 1
    for entry in ${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}; do
      [[ ! -L "$entry" ]] || MS_LIVE_LINKS+=("$entry")
    done
  fi
}

# Prefix lock is held for mutating consumers. Prune only reads these claims;
# it never runs journal recovery or removes another slot's evidence.
ms_claims_collect() {
  local slot i j requested="$MS_BIN" mode="${1:-all}" claim batch tool
  MS_CLAIM_PATHS=() MS_CLAIM_SELECTORS=() MS_FOREIGN_CLAIM_PATHS=() MS_FOREIGN_CLAIM_SELECTORS=()
  [[ -e "$MS_ROOT" || -L "$MS_ROOT" ]] || return 0
  ms_root_valid && ms_inventory_children "$MS_ROOT/locations" || return 1
  local -a seen_bins=() slots=("${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}") saved=("${MS_ROWS[@]+"${MS_ROWS[@]}"}")
  local generation="$MS_GENERATION" adopted="$MS_ADOPTED" hint="$MS_FZF_HINT"
  for slot in ${slots[@]+"${slots[@]}"}; do
    case "${slot##*/}" in .tmp-*) ms_private "$slot" dir || return 1; continue ;; esac
    ms_uint "${slot##*/}" && ms_private "$slot" dir && ms_state_parse "$slot/state" || return 1
    local seen
    for seen in ${seen_bins[@]+"${seen_bins[@]}"}; do [[ "$seen" != "$MS_BIN" ]] || return 1; done
    seen_bins+=("$MS_BIN")
    i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      claim=1
      if [[ "$mode" == prune && "$MS_BIN" == "$requested" ]]; then
        case "${MS_ROWS[i]}" in
          reuse-intent|publication|link-intent|remove-intent)
            batch="${MS_ROWS[j]}" tool="${MS_ROWS[j+1]}"
            ms_row_find item "$batch" "$tool" || return 1
            [[ "${MS_ROWS[MS_INDEX+3]}" != completed ]] || claim=0 ;;
        esac
      fi
      if ((claim == 0)); then i=$((i + 2 + MS_ROWS[i+1])); continue; fi
      case "${MS_ROWS[i]}" in
        reuse-intent)
          MS_CLAIM_PATHS+=("${MS_ROWS[j+2]}")
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+2]}") ;;
        cli-intent)
          MS_CLAIM_SELECTORS+=("${MS_ROWS[j+1]}")
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_SELECTORS+=("${MS_ROWS[j+1]}") ;;
        protected)
          MS_CLAIM_PATHS+=("${MS_ROWS[j+1]}")
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+1]}") ;;
        release)
          if [[ "$mode" != prune || "$MS_BIN" != "$requested" ]]; then MS_CLAIM_PATHS+=("${MS_ROWS[j+1]}"); fi
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+1]}") ;;
        selector)
          MS_CLAIM_SELECTORS+=("${MS_ROWS[j+1]}")
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_SELECTORS+=("${MS_ROWS[j+1]}") ;;
        publication)
          MS_CLAIM_PATHS+=("${MS_ROWS[j+2]}" "${MS_ROWS[j+3]}")
          [[ "$MS_BIN" == "$requested" ]] || MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+2]}" "${MS_ROWS[j+3]}") ;;
        link-intent)
          MS_CLAIM_PATHS+=("${MS_ROWS[j+6]}"); MS_CLAIM_SELECTORS+=("${MS_ROWS[j+2]}")
          if [[ "$MS_BIN" != "$requested" ]]; then
            MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+6]}") MS_FOREIGN_CLAIM_SELECTORS+=("${MS_ROWS[j+2]}")
          fi ;;
        remove-intent)
          MS_CLAIM_PATHS+=("${MS_ROWS[j+5]}")
          if [[ "$MS_BIN" != "$requested" ]]; then
            MS_FOREIGN_CLAIM_PATHS+=("${MS_ROWS[j+5]}")
            [[ "${MS_ROWS[j+2]}" == release ]] || MS_FOREIGN_CLAIM_SELECTORS+=("${MS_ROWS[j+3]}")
          fi ;;
      esac
      i=$((i + 2 + MS_ROWS[i+1]))
    done
  done
  MS_BIN="$requested" MS_GENERATION="$generation" MS_ADOPTED="$adopted" MS_FZF_HINT="$hint" MS_ROWS=("${saved[@]+"${saved[@]}"}")
}

ms_claimed_path() {
  local path
  for path in ${MS_CLAIM_PATHS[@]+"${MS_CLAIM_PATHS[@]}"}; do [[ "$path" != "$1" ]] || return 0; done
  return 1
}

# Read-only reports use an optimistic generation/ticket fence. A writer or a
# changing record causes a retry diagnostic; the report never creates storage.
ms_report_begin() {
  ms_state_load || return 1
  MS_REPORT_SLOT="$MS_SLOT" MS_REPORT_GENERATION="$MS_GENERATION"
  if ! ms_lock_read_idle "$MS_PREFIX" || ! ms_lock_read_idle "$MS_BIN"; then ms_error 'writer active; retry report'; return 1; fi
}
ms_report_end() {
  local generation="$MS_REPORT_GENERATION" slot="$MS_REPORT_SLOT"
  ms_lock_read_idle "$MS_PREFIX" && ms_lock_read_idle "$MS_BIN" && ms_state_load &&
    [[ "$generation" == "$MS_GENERATION" && "$slot" == "$MS_SLOT" ]] || ms_error 'location changed; retry report'
}
