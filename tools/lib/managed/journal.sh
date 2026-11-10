# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

ms_journal_active() {
  local i=0
  while ((i < ${#MS_ROWS[@]})); do
    if [[ "${MS_ROWS[i]}" == batch ]]; then
      MS_BATCH="${MS_ROWS[i+2]}" MS_BATCH_COMMAND="${MS_ROWS[i+3]}" MS_BATCH_PHASE="${MS_ROWS[i+4]}"
      return 0
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  return 1
}

# Terminal history is not current required scope. A current item always wins
# over archived results; absence or an older completed result alone is not enough.
ms_tool_uninstall_terminal() {
  local tool="$1" i=0 j current="" archived=""
  ms_member_has "$tool" && return 1
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
  [[ "${current:-$archived}" == uninstall:completed ]]
}

# Normalize only in memory, under the same locks/gate as the definitive preflight.
# The next actual operation commits this together with its new journal.
ms_journal_prepare() {
  ms_lock_holds "$MS_PREFIX" && [[ "${MS_GATE_PASSED:-0}" == "$MS_GENERATION" ]] || return 1
  if ms_journal_active; then
    [[ "$MS_BATCH_PHASE" == settled ]] && ms_journal_archive || return 1
  fi
}

ms_journal_archive() {
  local i=0 j type
  local -a archived=()
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2)) type="${MS_ROWS[i]}"
    if [[ "$type" == item ]]; then
      [[ "${MS_ROWS[j+3]}" == completed || "${MS_ROWS[j+3]}" == failed || "${MS_ROWS[j+3]}" == not-run ]] || return 1
      archived+=("result" 4 "${MS_ROWS[j]}" "${MS_ROWS[j+1]}" "${MS_ROWS[j+2]}" "${MS_ROWS[j+3]}")
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  # Preserve failed publication/remove scope as protected evidence before retiring
  # the journal. It stays visible to prune even after an unrelated new batch.
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2)) type="${MS_ROWS[i]}"
    if [[ "$type" == publication ]]; then
      ms_row_find item "${MS_ROWS[j]}" "${MS_ROWS[j+1]}" || return 1
      if [[ "${MS_ROWS[MS_INDEX+3]}" == completed ]]; then
        i=$((i + 2 + MS_ROWS[i+1])); continue
      fi
      ms_row_find protected "${MS_ROWS[j+1]}" "${MS_ROWS[j+2]}" || archived+=(protected 3 "${MS_ROWS[j+1]}" "${MS_ROWS[j+2]}" pending)
      ms_row_find protected "${MS_ROWS[j+1]}" "${MS_ROWS[j+3]}" || archived+=(protected 3 "${MS_ROWS[j+1]}" "${MS_ROWS[j+3]}" pending)
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  MS_ROWS+=("${archived[@]+"${archived[@]}"}")
  # Retire successful uninstall claims after preserving its result and before
  # admitting a new batch. Failure scope stays as claims for subsequent repair.
  i=0
  local -a removed=()
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == item && "${MS_ROWS[j+2]}" == uninstall && "${MS_ROWS[j+3]}" == completed ]]; then removed+=("${MS_ROWS[j+1]}"); fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  local tool root
  for tool in ${removed[@]+"${removed[@]}"}; do
    while ms_row_find release "$tool"; do
      root="${MS_ROWS[MS_INDEX+1]}"
      ms_row_drop manifest "$root"
      ms_row_drop release "$tool" "$root"
    done
    ms_row_drop selector "$tool"
  done
  for type in batch item publication link-intent remove-intent cli-intent refresh-intent reuse-intent; do ms_row_drop "$type"; done
}

# All entry points must pass the same prior-journal gate. Never overwrite an
# unresolved receipt merely because the next requested command is unrelated.
ms_journal_begin() {
  local command="$1" action="$2" tool order=0 before
  shift 2
  ms_lock_holds "$MS_PREFIX" && [[ "${MS_GATE_PASSED:-0}" == "$MS_GENERATION" ]] || return 1
  # Callers must prepare BEFORE gathering definitive new receipts/preflight.
  if ms_journal_active; then return 1; fi
  MS_BATCH="b$$-$RANDOM$RANDOM"
  ms_row_add batch "$MS_BATCH" "$command" tools || return 1
  for tool in "$@"; do
    before=0
    ms_member_has "$tool" && before=1
    ms_row_add item "$MS_BATCH" "$tool" "$action" queued "$before" queued "$order" || return 1
    order=$((order + 1))
  done
  ms_state_commit
}

ms_journal_item() {
  local tool="$1" status="$2" phase="$3" i
  ms_row_find item "$MS_BATCH" "$tool" || return 1
  i=$MS_INDEX
  MS_ROWS[i+3]="$status" MS_ROWS[i+5]="$phase"
  ms_state_commit
}

# Membership and completion are serialized in the same atomic generation.
ms_journal_complete() {
  local tool="$1" i action
  ms_row_find item "$MS_BATCH" "$tool" || return 1
  i=$MS_INDEX action="${MS_ROWS[i+2]}"
  if [[ "$action" == install ]]; then ms_member_set "$tool" 1; else ms_member_set "$tool" 0; fi
  ms_row_find item "$MS_BATCH" "$tool" || return 1
  i=$MS_INDEX MS_ROWS[i+3]=completed MS_ROWS[i+5]=settled
  ms_state_commit
}

ms_journal_fail_tail() {
  local tool="$1" i=0 j
  while ((i < ${#MS_ROWS[@]})); do
    j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == item && "${MS_ROWS[j]}" == "$MS_BATCH" ]]; then
      if [[ "${MS_ROWS[j+1]}" == "$tool" ]]; then MS_ROWS[j+3]=failed MS_ROWS[j+5]=settled
      elif [[ "${MS_ROWS[j+3]}" == queued ]]; then MS_ROWS[j+3]=not-run MS_ROWS[j+5]=settled; fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  ms_state_commit
}
