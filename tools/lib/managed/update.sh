# shellcheck shell=bash
# shellcheck disable=SC2034,SC2015,SC2016

ensure_this_file_sourced

# A fetch may otherwise detach maintenance after its registered Git PID exits.
# Keep this operation's mutations inside that lease; never persist Git settings.
MS_GIT_MUTATION_FLAGS=(-c maintenance.auto=false -c gc.auto=0 -c core.fsmonitor=false -c core.untrackedCache=false)

# Guard queries must not refresh indexes/caches or start fsmonitor callbacks.
ms_git_read() {
  local checkout="$1"; shift
  GIT_OPTIONAL_LOCKS=0 git -c core.fsmonitor=false -c core.untrackedCache=false -c diff.autoRefreshIndex=false -C "$checkout" "$@"
}

ms_member_list() {
  local i=0
  MS_MEMBERS=() MS_MEMBER_EXECUTABLES=0
  while ((i < ${#MS_ROWS[@]})); do
    if [[ "${MS_ROWS[i]}" == member ]]; then MS_MEMBERS+=("${MS_ROWS[i+2]}"); fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  for i in ${MS_MEMBERS[@]+"${MS_MEMBERS[@]}"}; do
    ms_row_find tool "$i" || return 1
    [[ "${MS_ROWS[MS_INDEX+1]}" == bash-builtin ]] || MS_MEMBER_EXECUTABLES=1
  done
}

ms_update_preflight() {
  local checkout="$1"
  [[ -d "$checkout/.git" ]] && ms_git_read "$checkout" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { ms_error "not a Git checkout: $checkout"; return 1; }
  MS_UPSTREAM="$(ms_git_read "$checkout" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')" || return 1
  [[ "$MS_UPSTREAM" == */* && "$MS_UPSTREAM" != -* && "$MS_UPSTREAM" != *$'\n'* && "${MS_UPSTREAM#*/}" != -* ]] || return 1
  MS_OLD_HEAD="$(ms_git_read "$checkout" rev-parse --verify HEAD)" && ms_git_oid "$MS_OLD_HEAD"
}

ms_checkout_guard() {
  local checkout="$1" expected="$2" actual
  ms_physical_path "$REPO_DIR" && [[ "$MS_PATH" == "$checkout" && -d "$checkout/.git" ]] || return 1
  actual="$(ms_git_read "$checkout" rev-parse --verify HEAD)" && [[ "$actual" == "$expected" ]]
}
ms_reset_guard() {
  local checkout="$1" old="$2" target="$3" actual resolved
  ms_physical_path "$REPO_DIR" && [[ "$MS_PATH" == "$checkout" && -d "$checkout/.git" ]] || return 1
  actual="$(ms_git_read "$checkout" rev-parse --verify HEAD)" || return 1
  [[ "$actual" == "$old" || "$actual" == "$target" ]] || return 1
  resolved="$(ms_git_read "$checkout" rev-parse --verify "$target^{commit}")" && [[ "$resolved" == "$target" ]] && ms_reset_paths_valid "$checkout" "$target"
}


ms_git_inventory_producer() {
  local checkout="$1" kind="$2" target="$3" status
  case "$kind" in
    target) ms_git_read "$checkout" ls-tree -r -z --name-only "$target" -- ;;
    tracked) ms_git_read "$checkout" ls-files -z -- ;;
    other) ms_git_read "$checkout" ls-files --others -z -- ;;
    *) return 1 ;;
  esac
  status=$?; printf '\0%s\0' "$status"
}

ms_git_inventory() {
  local checkout="$1" kind="$2" target="$3" entry status extra trailer=0
  local -a found=()
  MS_GIT_PATHS=()
  while IFS= read -r -d '' entry; do
    if [[ -z "$entry" ]]; then
      IFS= read -r -d '' status && [[ "$status" == 0 ]] || return 1
      extra=""
      if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
      trailer=1; break
    fi
    entry="${entry%/}"
    [[ -n "$entry" && "$entry" != /* ]] || return 1
    case "/$entry/" in *'/../'*|*'/./'*|*'//'*) return 1 ;; esac
    found+=("$checkout/$entry")
  done < <(ms_git_inventory_producer "$checkout" "$kind" "$target")
  ((trailer)) || return 1
  MS_GIT_PATHS=("${found[@]+"${found[@]}"}")
}

ms_paths_overlap() {
  case "$1/" in "$2/"*) return 0 ;; esac
  case "$2/" in "$1/"*) return 0 ;; esac
  return 1
}

# reset --hard may remove an untracked obstruction. Keep that outside its
# authority, and never let tracked checkout content replace state, tickets or
# release claims when an override shares the checkout's physical root.
ms_reset_paths_valid() {
  local checkout="$1" target="$2" path protected root
  local -a targets=() tracked=() others=() owned=("$MS_ROOT" "$MS_PREFIX/.active")
  ms_claims_collect || return 1
  owned+=("${MS_CLAIM_PATHS[@]+"${MS_CLAIM_PATHS[@]}"}" "${MS_CLAIM_SELECTORS[@]+"${MS_CLAIM_SELECTORS[@]}"}")
  for root in "${MS_LOCK_ROOTS[@]}"; do owned+=("$root/.remote-ssh-lock"); done
  ms_git_inventory "$checkout" target "$target" || return 1
  targets=("${MS_GIT_PATHS[@]+"${MS_GIT_PATHS[@]}"}")
  ms_git_inventory "$checkout" tracked "$target" || return 1
  tracked=("${MS_GIT_PATHS[@]+"${MS_GIT_PATHS[@]}"}")
  ms_git_inventory "$checkout" other "$target" || return 1
  others=("${MS_GIT_PATHS[@]+"${MS_GIT_PATHS[@]}"}")
  for path in "${targets[@]+"${targets[@]}"}" "${tracked[@]+"${tracked[@]}"}"; do
    for protected in "${owned[@]}"; do
      if ms_paths_overlap "$path" "$protected"; then ms_error "checkout path overlaps managed data: $path"; return 1; fi
    done
  done
  for path in ${targets[@]+"${targets[@]}"}; do
    for protected in ${others[@]+"${others[@]}"}; do
      if ms_paths_overlap "$path" "$protected"; then ms_error "checkout would overwrite an untracked path: $protected"; return 1; fi
    done
  done
}

ms_checkout_matches_target() {
  local checkout="$1" target="$2" actual
  actual="$(ms_git_read "$checkout" rev-parse --verify HEAD)" && [[ "$actual" == "$target" ]] &&
    ms_git_read "$checkout" diff --quiet --no-ext-diff --no-textconv "$target" -- &&
    ms_git_read "$checkout" diff --cached --quiet --no-ext-diff --no-textconv "$target" --
}

ms_refresh_checkpoint() {
  local phase="$1" target="${2:-}" i
  ms_row_find refresh-intent "$MS_BATCH" || return 1
  i=$MS_INDEX MS_ROWS[i+4]="$target" MS_ROWS[i+5]="$phase"
  ms_state_commit
}

# Used by the common prior-journal gate, never by prune/report. A failed fetch
# or pre-reset checkpoint can settle not-run. An uncertain reset is only retried
# by update against the same frozen target and checkout, under checkout lock.
ms_refresh_recover() {
  local i checkout old target phase tool
  ms_row_find refresh-intent "$MS_BATCH" || return 1
  i=$MS_INDEX checkout="${MS_ROWS[i+1]}" old="${MS_ROWS[i+3]}" target="${MS_ROWS[i+4]}" phase="${MS_ROWS[i+5]}"
  ms_physical_path "$REPO_DIR" && [[ "$checkout" == "$MS_PATH" ]] && ms_lock_holds "$checkout" || return 1
  case "$phase" in
    planned|fetched) ;;
    resetting|reset-done)
      if ! ms_checkout_matches_target "$checkout" "$target"; then
        [[ "${MS_RECOVERY_COMMAND:-}" == update ]] || return 1
        ms_lock_mutate_guarded ms_reset_guard 3 "$checkout" "$old" "$target" git "${MS_GIT_MUTATION_FLAGS[@]}" -C "$checkout" reset --hard "$target" || return 1
        ms_checkout_matches_target "$checkout" "$target" || return 1
      fi ;;
    *) return 1 ;;
  esac
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    if [[ "${MS_ROWS[i]}" == item && "${MS_ROWS[i+2]}" == "$MS_BATCH" ]]; then
      [[ "${MS_ROWS[i+5]}" == queued ]] || return 1
      MS_ROWS[i+5]=not-run MS_ROWS[i+7]=settled
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  ms_row_find batch "$MS_BATCH" || return 1
  MS_ROWS[MS_INDEX+2]=settled
  ms_state_commit
}


ms_maintained_preflight() {
  local tool path MS_ALLOW_UNSUPPORTED=1
  local -a known=() retired=() paths=()
  ms_member_list || return 1
  for tool in ${MS_MEMBERS[@]+"${MS_MEMBERS[@]}"}; do
    if [[ -f "$TOOLS_DIR/defs/$tool.sh" ]]; then known+=("$tool"); else retired+=("$tool"); fi
  done
  ms_install_preflight ${known[@]+"${known[@]}"} || return 1
  for tool in ${retired[@]+"${retired[@]}"}; do
    ms_tool_selectors "$tool" || return 1
    paths=("${MS_VALUES[@]+"${MS_VALUES[@]}"}")
    for path in ${paths[@]+"${paths[@]}"}; do
      [[ "${path%/*}" != "$MS_BIN" ]] || MS_EXECUTABLES=1
      ms_inspect_selector "$tool" "$path" || return 1
    done
  done
}

ms_update_run() {
  local repo="$1" checkout upstream initial_upstream remote branch target code attempt acquired=0 i
  command -v git >/dev/null 2>&1 || { printf 'git is required for update.\n' >&2; return 127; }
  ms_physical_path "$repo" || return 1
  checkout="$MS_PATH"
  ms_update_preflight "$checkout" && ms_state_load || return 1
  initial_upstream="$MS_UPSTREAM"
  MS_RECOVERY_COMMAND=update
  for attempt in 1 2 3; do
    ms_state_load || return 1
    [[ "$MS_ADOPTED" != 0 ]] || ms_migration_preview || return 1
    ms_maintained_preflight && ms_lock_plan update "$MS_EXECUTABLES" || return 1
    ms_create_roots "$MS_EXECUTABLES" && ms_lock_acquire "${MS_REQUIRED_LOCKS[@]}" && ms_state_load || return 1
    ms_recovery_gate && ms_journal_prepare || return 1
    [[ "$MS_ADOPTED" != 0 ]] || ms_migration_preview || return 1
    ms_maintained_preflight && ms_lock_plan update "$MS_EXECUTABLES" || return 1
    if ms_lock_set_matches; then acquired=1; break; fi
    ms_lock_release_all || return 1
  done
  ((acquired)) || return 1
  ms_update_preflight "$checkout" && [[ "$MS_UPSTREAM" == "$initial_upstream" ]] || return 1
  if [[ "$MS_ADOPTED" == 0 ]]; then
    ms_legacy_hints "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" && ms_migration_commit || return 1
  fi
  ms_recovery_gate && ms_journal_prepare && ms_member_list || return 1
  MS_OPERATION=update MS_PUBLISH_CLI=0
  ms_journal_begin update install ${MS_MEMBERS[@]+"${MS_MEMBERS[@]}"} || return 1
  upstream="$MS_UPSTREAM" remote="${MS_UPSTREAM%%/*}" branch="${MS_UPSTREAM#*/}"
  ms_row_add refresh-intent "$MS_BATCH" "$checkout" "$upstream" "$MS_OLD_HEAD" "" planned || return 1
  ms_row_find batch "$MS_BATCH" || return 1
  MS_ROWS[MS_INDEX+2]=refresh
  ms_state_commit || return 1
  printf '[*] Fetching %s/%s\n' "$remote" "$branch"
  if ms_lock_mutate_guarded ms_checkout_guard 2 "$checkout" "$MS_OLD_HEAD" git "${MS_GIT_MUTATION_FLAGS[@]}" -C "$checkout" fetch "$remote" "$branch"; then :
  else code=$?; printf 'Project refresh failed during fetch; tools not run.\n' >&2; ms_state_load && ms_recovery_gate || :; return "$code"; fi
  target="$(ms_git_read "$checkout" rev-parse --verify "$upstream^{commit}")" && ms_git_oid "$target" || return 1
  ms_refresh_checkpoint fetched "$target" || return 1
  if ! ms_reset_guard "$checkout" "$MS_OLD_HEAD" "$target"; then
    printf 'Protected checkout paths; reset was not started and tools were not run.\n' >&2
    ms_state_load && ms_recovery_gate || :
    return 1
  fi
  ms_refresh_checkpoint resetting "$target" || return 1
  printf '[*] Resetting tracked files to %s (%s)\n' "$upstream" "$target"
  if ms_lock_mutate_guarded ms_reset_guard 3 "$checkout" "$MS_OLD_HEAD" "$target" git "${MS_GIT_MUTATION_FLAGS[@]}" -C "$checkout" reset --hard "$target"; then :
  else code=$?; printf 'Project reset incomplete; managed tools retained, tools not run.\n' >&2; return "$code"; fi
  ms_checkout_matches_target "$checkout" "$target" && ms_refresh_checkpoint reset-done "$target" || return 1
  ms_row_find batch "$MS_BATCH" || return 1
  MS_ROWS[MS_INDEX+2]=refreshed
  ms_state_commit || return 1
  local -a continuation=("$MS_PREFIX" "$MS_BIN" "$MS_GENERATION" "$MS_BATCH" "${#MS_LOCK_ROOTS[@]}")
  for ((i=0; i<${#MS_LOCK_ROOTS[@]}; i++)); do continuation+=("${MS_LOCK_ROOTS[i]}" "${MS_LOCK_TOKENS[i]}" "${MS_LOCK_TICKETS[i]}"); done
  export INSTALL_PREFIX INSTALL_BIN_DIR
  # Same owner PID and tickets, fresh private code; no hidden public CLI flag.
  exec "$BASH" "$checkout/tools/lib/managed/continue-update.sh" "${continuation[@]}"
}

ms_continue_update_run() {
  local expected_prefix="$1" expected_bin="$2" generation="$3" batch="$4" count="$5" root token ticket i j phase checkout target tool platform os arch libc code
  shift 5
  ms_uint "$generation" && ms_uint "$count" && (($# == count * 3 && count > 0)) || return 1
  ms_state_load && [[ "$MS_PREFIX" == "$expected_prefix" && "$MS_BIN" == "$expected_bin" && "$MS_GENERATION" == "$generation" ]] || return 1
  MS_LOCK_OWNER="$$" MS_LOCK_SUBSHELL="$BASH_SUBSHELL" MS_LOCK_ROOTS=() MS_LOCK_TOKENS=() MS_LOCK_TICKETS=()
  for ((i=0; i<count; i++)); do
    root="$1" token="$2" ticket="$3"; shift 3
    ms_physical_path "$root" && [[ "$root" == "$MS_PATH" && "$token" == "p$$-"* ]] && ms_ticket_read "$root/.remote-ssh-lock/$token" && [[ "$MS_TICKET_NUMBER" == "$ticket" ]] || return 1
    MS_LOCK_ROOTS+=("$root") MS_LOCK_TOKENS+=("$token") MS_LOCK_TICKETS+=("$ticket")
  done
  ms_lock_install_traps
  ms_journal_active && [[ "$MS_BATCH" == "$batch" && "$MS_BATCH_COMMAND" == update && "$MS_BATCH_PHASE" == refreshed ]] || return 1
  ms_row_find refresh-intent "$batch" || return 1
  j=$MS_INDEX checkout="${MS_ROWS[j+1]}" target="${MS_ROWS[j+4]}" phase="${MS_ROWS[j+5]}"
  [[ "$phase" == reset-done ]] && ms_lock_holds "$checkout" && ms_checkout_matches_target "$checkout" "$target" || return 1
  printf 'Project refreshed. Repairing the managed set from fresh code.\n'
  # Existing informational cache semantics remain best-effort. The registered
  # foreground child covers all of this helper's ordinary utility calls.
  ms_lock_mutate "$BASH" -c '. "$1/tools/lib/env.sh"; . "$TOOLS_LIB_DIR/commands.lib.sh"; remote_ssh_cmd_update_check_cache_mark_current "$1"' _ "$checkout" || :
  ms_member_list || return 1
  local -a members=("${MS_MEMBERS[@]+"${MS_MEMBERS[@]}"}") known=()
  for tool in ${members[@]+"${members[@]}"}; do [[ ! -f "$TOOLS_DIR/defs/$tool.sh" ]] || known+=("$tool"); done
  local MS_ALLOW_UNSUPPORTED=1
  ms_install_preflight ${known[@]+"${known[@]}"} || return 1
  ms_member_list && ms_lock_plan update "$MS_EXECUTABLES" || return 1
  if ! ms_lock_set_matches; then
    ms_lock_release_all && ms_lock_acquire "${MS_REQUIRED_LOCKS[@]}" && ms_state_load && [[ "$MS_GENERATION" == "$generation" ]] || return 1
    ms_install_preflight ${known[@]+"${known[@]}"} || return 1
  fi
  ms_row_find batch "$batch" || return 1
  MS_ROWS[MS_INDEX+2]=tools
  ms_state_commit || return 1
  platform="$(default_platform)" && IFS=: read -r os arch libc <<<"$platform" || return 1
  for tool in ${members[@]+"${members[@]}"}; do
    if [[ ! -f "$TOOLS_DIR/defs/$tool.sh" ]]; then
      printf 'retired: %s; management retained.\n' "$tool" >&2
      ms_journal_fail_tail "$tool" && ms_recovery_gate || :
      ms_batch_report; return 1
    fi
    if ! default_tool_supported_on_platform "$tool" "$os" "$arch" "$libc"; then
      printf 'unsupported: %s; management retained.\n' "$tool" >&2
      ms_journal_fail_tail "$tool" && ms_recovery_gate || :
      ms_batch_report; return 1
    fi
    if ! ms_install_one "$tool"; then
      code=1
      printf 'Project refreshed; tool repair incomplete: %s\n' "$tool" >&2
      if ms_state_load; then
        ms_journal_active || return 1
        if ms_row_find item "$MS_BATCH" "$tool" && [[ "${MS_ROWS[MS_INDEX+3]}" == queued ]]; then ms_journal_fail_tail "$tool" || :; fi
        ms_recovery_gate || :
      fi
      ms_batch_report; return "$code"
    fi
  done
  ms_recovery_gate && ms_batch_report || return 1
  if ((${#members[@]} == 0)); then printf 'No managed tools; project-only update completed.\n'; else printf 'Project and managed tools updated.\n'; fi
}
