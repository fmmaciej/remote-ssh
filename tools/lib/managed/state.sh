# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

ms_error() { printf 'Managed state: %s\n' "$*" >&2; return 1; }
ms_uint() { [[ "$1" =~ ^(0|[1-9][0-9]{0,8})$ ]]; }
ms_name() { [[ "$1" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.+-]*$ ]]; }
ms_git_oid() { [[ "$1" =~ ^([a-f0-9]{40}|[a-f0-9]{64})$ ]]; }
ms_version() { [[ -n "$1" && "$1" != *[!a-zA-Z0-9_.:+-]* ]]; }
ms_layout() { case "$1" in binary|bundle|bash-builtin) return 0 ;; *) return 1 ;; esac; }
ms_absolute() {
  [[ "$1" == /* && "$1" != *'//'* ]] || return 1
  case "/${1#/}/" in *'/./'*|*'/../'*) return 1 ;; esac
}
ms_basename() { [[ -n "$1" && "$1" != */* && "$1" != . && "$1" != .. ]]; }

# Resolve existing components before '..', preserving whitespace/newlines. An
# absent tail is resolved against its nearest real parent, without creating it.
ms_physical_path() {
  local path="$1" parent base value
  [[ "$path" == /* ]] || path="$PWD/$path"
  if [[ -d "$path" ]]; then
    value="$(cd -P -- "$path" && pwd -P && printf '\001')" || return 1
    MS_PATH="${value%$'\001'}" MS_PATH="${MS_PATH%$'\n'}"
    [[ "$MS_PATH" == / ]] || MS_PATH="${MS_PATH%/}"
    return 0
  fi
  [[ ! -e "$path" && ! -L "$path" ]] || return 1
  path="${path%/}" base="${path##*/}" parent="${path%/*}"
  [[ -n "$parent" ]] || parent=/
  [[ "$parent" != "$path" ]] || return 1
  ms_physical_path "$parent" || return 1
  case "$base" in
    .|'') ;;
    ..) MS_PATH="${MS_PATH%/*}"; [[ -n "$MS_PATH" ]] || MS_PATH=/ ;;
    *) MS_PATH="${MS_PATH%/}/$base" ;;
  esac
}

ms_pair_resolve() {
  ms_physical_path "$INSTALL_PREFIX" || return 1
  MS_PREFIX="$MS_PATH"
  ms_physical_path "$INSTALL_BIN_DIR" || return 1
  MS_BIN="$MS_PATH"
  MS_ROOT="${MS_PREFIX%/}/.remote-ssh-managed"
}

# Mode checks use portable ls and the shell's owner predicate (no stat dialect).
ms_private() {
  local path="$1" kind="$2" mode
  [[ ! -L "$path" && -O "$path" && -r "$path" ]] || return 1
  mode="$(LC_ALL=C ls -ldn -- "$path")" || return 1
  mode="${mode%% *}"
  case "$kind:$mode" in
    dir:drwx------) [[ -d "$path" && -x "$path" ]] ;;
    file:-rw-------) [[ -f "$path" ]] ;;
    *) return 1 ;;
  esac
}

ms_state_reset() {
  MS_GENERATION=0 MS_ADOPTED=0 MS_FZF_HINT=0 MS_ROWS=() MS_SLOT=""
}

# Rows are flattened arrays, never delimiter-joined strings or executable data.
# Every type has a fixed field count; counts in the wire format are checked too.
ms_row_arity() {
  case "$1" in
    protected) MS_ARITY=3 ;;
    member) MS_ARITY=1 ;; tool) MS_ARITY=3 ;;
    alias) MS_ARITY=2 ;; required|manifest) MS_ARITY=3 ;;
    release) MS_ARITY=5 ;; selector) MS_ARITY=4 ;;
    reuse-intent) MS_ARITY=6 ;;
    refresh-intent) MS_ARITY=6 ;;
    cli-intent) MS_ARITY=4 ;;
    batch) MS_ARITY=3 ;; item) MS_ARITY=7 ;;
    publication) MS_ARITY=8 ;; link-intent) MS_ARITY=8 ;;
    remove-intent) MS_ARITY=8 ;; result) MS_ARITY=4 ;;
    *) return 1 ;;
  esac
}

ms_row_add() {
  local type="$1"; shift
  ms_row_arity "$type" && [[ "$#" == "$MS_ARITY" ]] || return 1
  MS_ROWS+=("$type" "$MS_ARITY" "$@")
}

# Find first row with exact leading keys, returning its first field offset.
ms_row_find() {
  local type="$1" i=0 j match arg
  shift
  while ((i < ${#MS_ROWS[@]})); do
    match=1 j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == "$type" ]]; then
      for arg in "$@"; do
        [[ "${MS_ROWS[j]}" == "$arg" ]] || match=0
        j=$((j + 1))
      done
      if ((match)); then MS_INDEX=$((i + 2)); return 0; fi
    fi
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  return 1
}

ms_row_drop() {
  local type="$1" i=0 j match arg
  local -a kept=()
  shift
  while ((i < ${#MS_ROWS[@]})); do
    match=0 j=$((i + 2))
    if [[ "${MS_ROWS[i]}" == "$type" ]]; then
      match=1
      for arg in "$@"; do
        [[ "${MS_ROWS[j]}" == "$arg" ]] || match=0
        j=$((j + 1))
      done
    fi
    j=$((i + 2 + MS_ROWS[i+1]))
    if ((match == 0)); then
      while ((i < j)); do kept+=("${MS_ROWS[i]}"); i=$((i + 1)); done
    else i=$j; fi
  done
  MS_ROWS=("${kept[@]+"${kept[@]}"}")
}

ms_member_set() {
  ms_name "$1" || return 1
  ms_row_drop member "$1"
  [[ "$2" == 0 ]] || ms_row_add member "$1"
}
ms_member_has() { ms_row_find member "$1"; }

ms_release_path() {
  ms_absolute "$1" && [[ "${1%/*}" == "$MS_PREFIX" ]] && ms_basename "${1##*/}"
}
ms_selector_path() {
  ms_absolute "$1" && { [[ "${1%/*}" == "$MS_BIN" ]] || [[ "${1%/*}" == "$MS_PREFIX/.active" ]]; }
}

ms_row_validate() {
  local type="$1"; shift
  case "$type" in
    protected) ms_name "$1" && ms_release_path "$2" && [[ "$3" == pending || "$3" == partial ]] ;;
    member) ms_name "$1" ;;
    tool) ms_name "$1" && ms_layout "$2" && remote_ssh_relative_path_valid "$3" ;;
    alias) ms_name "$1" && ms_basename "$2" ;;
    required) ms_name "$1" && remote_ssh_relative_path_valid "$2" && [[ "$3" == file || "$3" == dir || "$3" == any ]] ;;
    manifest) ms_release_path "$1" && remote_ssh_relative_path_valid "$2" && [[ "$3" == file || "$3" == dir ]] ;;
    release) ms_name "$1" && ms_release_path "$2" && ms_version "$3" && ms_layout "$4" && remote_ssh_relative_path_valid "$5" && remote_ssh_release_name_matches_version "${2##*/}" "$1" "$3" ;;
    selector) ms_name "$1" && ms_selector_path "$2" && [[ -n "$3" ]] && ms_release_path "$4" ;;
    reuse-intent) ms_name "$1" && ms_name "$2" && ms_release_path "$3" && ms_version "$4" && ms_layout "$5" && remote_ssh_relative_path_valid "$6" ;;
    refresh-intent) ms_name "$1" && ms_absolute "$2" && [[ "$3" == */* && "$3" != -* && "$3" != *$'\n'* ]] && ms_git_oid "$4" && { [[ "$6" == planned && -z "$5" ]] || { ms_git_oid "$5" && [[ "$6" == fetched || "$6" == resetting || "$6" == reset-done ]]; }; } ;;
    cli-intent) ms_name "$1" && [[ "$2" == "$MS_BIN/remote-ssh" ]] && ms_absolute "$3" && [[ "$4" == intended || "$4" == "done" ]] ;;
    batch) ms_name "$1" && [[ "$2" == install || "$2" == uninstall || "$2" == update || "$2" == wrapper ]] && [[ "$3" == tools || "$3" == refresh || "$3" == refreshed || "$3" == settled ]] ;;
    item) ms_name "$1" && ms_name "$2" && [[ "$3" == install || "$3" == uninstall ]] && ms_item_status "$4" && [[ "$5" == 0 || "$5" == 1 ]] && [[ "$6" == queued || "$6" == staging || "$6" == publishing || "$6" == removing || "$6" == verifying || "$6" == settled ]] && ms_uint "$7" ;;
    publication) ms_name "$1" && ms_name "$2" && ms_release_path "$3" && ms_release_path "$4" && ms_version "$5" && ms_layout "$6" && remote_ssh_relative_path_valid "$7" && [[ "$8" == intended || "$8" == renamed ]] ;;
    link-intent) ms_name "$1" && ms_name "$2" && ms_selector_path "$3" && [[ "$4" == absent || "$4" == link ]] && { [[ "$4" == absent && -z "$5" ]] || [[ "$4" == link && -n "$5" ]]; } && ms_absolute "$6" && ms_release_path "$7" && [[ "$8" == intended || "$8" == "done" ]] ;;
    remove-intent) ms_name "$1" && ms_name "$2" && { { [[ "$3" == link ]] && ms_selector_path "$4" && [[ -n "$5" ]]; } || { [[ "$3" == absent && -z "$5" ]] && ms_selector_path "$4"; } || { [[ "$3" == release && "$4" == "$6" && -z "$5" ]] && ms_release_path "$4"; }; } && ms_release_path "$6" && [[ "$7" == intended || "$7" == "done" ]] && [[ "$8" == required || "$8" == optional ]] ;;
    result) ms_name "$1" && ms_name "$2" && [[ "$3" == install || "$3" == uninstall ]] && [[ "$4" == completed || "$4" == failed || "$4" == not-run ]] ;;
    *) return 1 ;;
  esac
}
ms_item_status() { case "$1" in queued|running|completed|failed|not-run) return 0 ;; *) return 1 ;; esac; }

ms_rows_validate() {
  local i=0 j n type key_count old_index batches=0
  while ((i < ${#MS_ROWS[@]})); do
    type="${MS_ROWS[i]}" n="${MS_ROWS[i+1]}"
    ms_row_arity "$type" && [[ "$n" == "$MS_ARITY" ]] || return 1
    ((i + n + 2 <= ${#MS_ROWS[@]})) || return 1
    ms_row_validate "$type" "${MS_ROWS[@]:i+2:n}" || return 1
    [[ "$type" != batch ]] || batches=$((batches + 1))
    ((batches <= 1)) || return 1
    case "$type" in
      member|tool|batch|cli-intent|refresh-intent) key_count=1 ;;
      release) key_count=2 ;;
      selector|alias|required|manifest|item|publication|result|protected|reuse-intent) key_count=2 ;;
      link-intent) key_count=3 ;;
      remove-intent) key_count=4 ;;
    esac
    ms_row_find "$type" "${MS_ROWS[@]:i+2:key_count}" || return 1
    old_index=$MS_INDEX
    [[ "$old_index" == "$((i + 2))" ]] || return 1
    i=$((i + n + 2))
  done
  # Cross-references keep malformed receipts from becoming authorization.
  i=0
  while ((i < ${#MS_ROWS[@]})); do
    type="${MS_ROWS[i]}" j=$((i + 2))
    case "$type" in
      member|alias|required) ms_row_find tool "${MS_ROWS[j]}" || return 1 ;;
      selector) ms_row_find release "${MS_ROWS[j]}" "${MS_ROWS[j+3]}" || return 1 ;;
      manifest)
        # A manifest may refer to a staged publication as well as a live claim.
        local found=0 k=0
        while ((k < ${#MS_ROWS[@]})); do
          if [[ "${MS_ROWS[k]}" == release && "${MS_ROWS[k+3]}" == "${MS_ROWS[j]}" ]] ||
            [[ "${MS_ROWS[k]}" == publication && "${MS_ROWS[k+5]}" == "${MS_ROWS[j]}" ]]; then found=1; fi
          k=$((k + 2 + MS_ROWS[k+1]))
        done
        ((found)) || return 1 ;;
      cli-intent|refresh-intent) ms_row_find batch "${MS_ROWS[j]}" || return 1 ;;
      item)
        ms_row_find batch "${MS_ROWS[j]}" || return 1
        local expected_member="${MS_ROWS[j+4]}" actual_member=0
        if [[ "${MS_ROWS[j+3]}" == completed ]]; then
          if [[ "${MS_ROWS[j+2]}" == install ]]; then expected_member=1; else expected_member=0; fi
        fi
        ms_member_has "${MS_ROWS[j+1]}" && actual_member=1
        [[ "$actual_member" == "$expected_member" ]] || return 1 ;;
      reuse-intent) ms_row_find item "${MS_ROWS[j]}" "${MS_ROWS[j+1]}" && ms_row_find release "${MS_ROWS[j+1]}" "${MS_ROWS[j+2]}" || return 1 ;;
      publication|link-intent|remove-intent)
        ms_row_find item "${MS_ROWS[j]}" "${MS_ROWS[j+1]}" || return 1
        if [[ "$type" == link-intent ]]; then
          ms_row_find publication "${MS_ROWS[j]}" "${MS_ROWS[j+1]}" || return 1
          old_index=$MS_INDEX
          [[ "${MS_ROWS[j+6]}" == "${MS_ROWS[old_index+3]}" && "${MS_ROWS[j+5]}" == "${MS_ROWS[old_index+3]}/${MS_ROWS[old_index+6]}" ]] || return 1
        elif [[ "$type" == remove-intent ]]; then
          ms_row_find release "${MS_ROWS[j+1]}" "${MS_ROWS[j+5]}" || return 1
        fi ;;

    esac
    i=$((i + 2 + MS_ROWS[i+1]))
  done
}

ms_state_emit() {
  local i=0 count=0
  while ((i < ${#MS_ROWS[@]})); do count=$((count + 1)); i=$((i + 2 + MS_ROWS[i+1])); done
  printf '%s\0' remote-ssh-managed 1 "$MS_PREFIX" "$MS_BIN" "$MS_GENERATION" "$MS_ADOPTED" "$MS_FZF_HINT" "$count"
  ((${#MS_ROWS[@]} == 0)) || printf '%s\0' "${MS_ROWS[@]}"
}

ms_state_parse_fd() {
  local magic schema prefix bin generation adopted hint count i j type n extra
  IFS= read -r -d '' magic && IFS= read -r -d '' schema &&
    IFS= read -r -d '' prefix && IFS= read -r -d '' bin &&
    IFS= read -r -d '' generation && IFS= read -r -d '' adopted &&
    IFS= read -r -d '' hint && IFS= read -r -d '' count || return 1
  [[ "$magic" == remote-ssh-managed && "$schema" == 1 && "$prefix" == "$MS_PREFIX" ]] || return 1
  [[ -z "${1:-}" || "$bin" == "$1" ]] || return 1
  ms_absolute "$bin" && ms_uint "$generation" && ms_uint "$count" &&
    [[ "$adopted" == 0 || "$adopted" == 1 ]] && [[ "$hint" == 0 || "$hint" == 1 ]] || return 1
  MS_BIN="$bin" MS_GENERATION="$generation" MS_ADOPTED="$adopted" MS_FZF_HINT="$hint" MS_ROWS=()
  for ((i=0; i<count; i++)); do
    IFS= read -r -d '' type && IFS= read -r -d '' n || return 1
    ms_row_arity "$type" && [[ "$n" == "$MS_ARITY" ]] || return 1
    MS_ROWS+=("$type" "$n")
    for ((j=0; j<n; j++)); do IFS= read -r -d '' extra || return 1; MS_ROWS+=("$extra"); done
  done
  extra=""
  if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
  ms_rows_validate
}

# Failure does not expose a partly parsed state as an empty valid set.
ms_state_parse() {
  ms_private "$1" file || return 1
  ms_state_parse_fd "${2:-}" <"$1"
}

ms_root_valid() {
  local value
  ms_private "$MS_ROOT" dir && ms_private "$MS_ROOT/format" file && ms_private "$MS_ROOT/locations" dir || return 1
  value="$(cat "$MS_ROOT/format" && printf '\001')" || return 1
  [[ "$value" == $'remote-ssh-managed\nschema=1\n\001' ]]
}

ms_slots_scan() {
  local requested="$MS_BIN" slot name matches=0
  MS_SLOT="" MS_SLOTS=()
  if [[ ! -e "$MS_ROOT" && ! -L "$MS_ROOT" ]]; then ms_state_reset; return 0; fi
  ms_root_valid || return 1
  ms_inventory_children "$MS_ROOT/locations" || return 1
  local -a slots=("${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}")
  for slot in ${slots[@]+"${slots[@]}"}; do
    name="${slot##*/}"
    case "$name" in .tmp-*) ms_private "$slot" dir || return 1; continue ;; esac
    ms_uint "$name" && ms_private "$slot" dir || return 1
    ms_state_parse "$slot/state" || return 1
    MS_SLOTS+=("$slot")
    if [[ "$MS_BIN" == "$requested" ]]; then matches=$((matches + 1)); MS_SLOT="$slot"; fi
  done
  ((matches <= 1)) || return 1
  MS_BIN="$requested"
  if ((matches)); then ms_state_parse "$MS_SLOT/state" "$requested"; else ms_state_reset; fi
}

ms_state_load() {
  if ! ms_pair_resolve || ! ms_slots_scan; then ms_error 'invalid or unreadable location inventory'; return 1; fi
}

ms_state_commit() {
  local slot temp expected_prefix="$MS_PREFIX" expected_bin="$MS_BIN" next=$((MS_GENERATION + 1)) i=0
  ms_lock_holds "$MS_PREFIX" || return 1
  ms_rows_validate || return 1
  [[ -d "$INSTALL_PREFIX" ]] || return 1
  ms_pair_resolve && [[ "$MS_PREFIX" == "$expected_prefix" && "$MS_BIN" == "$expected_bin" ]] || return 1
  if [[ ! -e "$MS_ROOT" && ! -L "$MS_ROOT" ]]; then
    (umask 077; mkdir "$MS_ROOT" && mkdir "$MS_ROOT/locations" && printf 'remote-ssh-managed\nschema=1\n' >"$MS_ROOT/format") || return 1
  fi
  ms_root_valid || return 1
  # Re-read every slot under the prefix lock before any publication. A copied
  # pair or corrupt other slot is never silently bypassed by a cached MS_SLOT.
  (local expected_slot="$MS_SLOT" expected_generation="$MS_GENERATION"
    ms_slots_scan && [[ "$MS_SLOT" == "$expected_slot" && "$MS_GENERATION" == "$expected_generation" ]]) || return 1
  if [[ -z "$MS_SLOT" ]]; then
    while [[ -e "$MS_ROOT/locations/$i" || -L "$MS_ROOT/locations/$i" ]]; do i=$((i + 1)); done
    temp="$(umask 077; mktemp -d "$MS_ROOT/locations/.tmp-XXXXXXXX")" || return 1
    MS_GENERATION="$next"
    (umask 077; ms_state_emit >"$temp/state") || return 1
    (ms_state_parse "$temp/state" "$MS_BIN") || return 1
    slot="$MS_ROOT/locations/$i"
    [[ ! -e "$slot" && ! -L "$slot" ]] && ms_lock_mutate_guarded ms_new_slot_guard 1 "$slot" mv -- "$temp" "$slot" || return 1
    MS_SLOT="$slot"
  else
    ms_private "$MS_SLOT" dir && ms_private "$MS_SLOT/state" file || return 1
    # The writer holds the prefix lock; verify the prior on-disk generation.
    (ms_state_parse "$MS_SLOT/state" "$MS_BIN" && [[ "$MS_GENERATION" == "$((next - 1))" ]]) || return 1
    temp="$(umask 077; mktemp "$MS_SLOT/.state-XXXXXXXX")" || return 1
    MS_GENERATION="$next"
    ms_state_emit >"$temp" && (ms_state_parse "$temp" "$MS_BIN") || return 1
    ms_private "$MS_SLOT/state" file && ms_lock_mutate_guarded ms_state_replace_guard 2 "$MS_SLOT/state" "$((next - 1))" mv -f -- "$temp" "$MS_SLOT/state" || return 1
  fi
}


ms_new_slot_guard() {
  ms_root_valid && [[ "${1%/*}" == "$MS_ROOT/locations" && ! -e "$1" && ! -L "$1" ]]
}
ms_state_replace_guard() {
  local expected="$2"
  ms_root_valid && ms_private "$MS_SLOT" dir && ms_state_parse "$1" "$MS_BIN" && [[ "$MS_GENERATION" == "$expected" ]]
}
