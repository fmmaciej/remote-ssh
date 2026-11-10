# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced
MS_LOCK_ROOTS=() MS_LOCK_TOKENS=() MS_LOCK_TICKETS=()

ms_pid_live() {
  local message
  if message="$(LC_ALL=C kill -0 "$1" 2>&1)"; then return 0; fi
  case "$message" in *'No such process'*|*'no such process'*) return 1 ;; *) return 0 ;; esac
}

ms_lock_storage_valid() {
  local value
  ms_private "$1/.remote-ssh-lock" dir && ms_private "$1/.remote-ssh-lock/format" file || return 1
  value="$(cat "$1/.remote-ssh-lock/format" && printf '\001')" || return 1
  [[ "$value" == $'remote-ssh-bakery\nschema=1\n\001' ]]
}

ms_lock_storage_init() {
  local root="$1" temp start=$SECONDS
  if [[ ! -e "$root/.remote-ssh-lock" && ! -L "$root/.remote-ssh-lock" ]]; then
    temp="$(umask 077; mktemp -d "$root/.remote-ssh-lock-init-XXXXXXXX")" || return 1
    (umask 077; printf 'remote-ssh-bakery\nschema=1\n' >"$temp/format") || return 1
    # Concurrent initializers are harmless; never rename into an existing dir.
    if ! (umask 077; mkdir "$root/.remote-ssh-lock") 2>/dev/null; then
      while ! ms_lock_storage_valid "$root"; do
        ((SECONDS - start < 3)) || return 1
        sleep 1
      done
      rm -- "$temp/format" && rmdir -- "$temp" || return 1
    else
      chmod 700 "$root/.remote-ssh-lock" && mv -- "$temp/format" "$root/.remote-ssh-lock/format" && rmdir -- "$temp" || return 1
    fi
  fi
  ms_lock_storage_valid "$root"
}

ms_ticket_read() {
  local path="$1" token pid number extra
  ms_private "$path/ticket" file || return 1
  {
    IFS= read -r -d '' token && IFS= read -r -d '' pid && IFS= read -r -d '' number || return 1
    extra=""
    if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
  } <"$path/ticket"
  [[ "$token" == "${path##*/}" && "$token" == "p$pid-"* ]] && ms_uint "$pid" && [[ "$pid" != 0 ]] && ms_uint "$number" && [[ "$number" != 0 ]] || return 1
  MS_TICKET_NUMBER="$number"
}

ms_lock_scan() {
  local root="$1" entry token pid live
  MS_SCAN_TOKENS=() MS_SCAN_NUMBERS=() MS_SCAN_CHOOSING=0
  ms_lock_storage_valid "$root" && ms_inventory_children "$root/.remote-ssh-lock" || return 1
  local -a entries=("${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}")
  for entry in ${entries[@]+"${entries[@]}"}; do
    token="${entry##*/}"
    [[ "$token" != format ]] || continue
    [[ "$token" =~ ^p([1-9][0-9]*)-[0-9]+$ ]] || return 1
    pid="${token#p}" pid="${pid%%-*}"
    if [[ ! -e "$entry" && ! -L "$entry" ]]; then continue; fi
    if ! ms_private "$entry" dir; then
      [[ ! -e "$entry" && ! -L "$entry" ]] && continue
      return 1
    fi
    live=0
    ms_pid_live "$pid" && live=1
    if [[ -e "$entry/inflight" || -L "$entry/inflight" ]]; then
      if ! ms_inflight_read "$entry"; then
        if [[ ! -e "$entry/inflight" && ! -L "$entry/inflight" ]]; then
          ((live)) || continue
        else return 1; fi
      else
        ms_pid_live "$MS_INFLIGHT_PID" && live=1
      fi
    fi
    ((live)) || continue
    # A peer can exit between enumeration and inspection. Only disappearance is
    # benign; invalid/replaced live records fail closed.
    if [[ ! -e "$entry" && ! -L "$entry" ]]; then continue; fi
    ms_private "$entry" dir || return 1
    if [[ ! -e "$entry/ticket" && ! -L "$entry/ticket" ]]; then
      MS_SCAN_CHOOSING=1
      MS_SCAN_TOKENS+=("$token") MS_SCAN_NUMBERS+=(0)
    else
      if ! ms_ticket_read "$entry"; then
        [[ ! -e "$entry" && ! -L "$entry" ]] && continue
        return 1
      fi
      MS_SCAN_TOKENS+=("$token") MS_SCAN_NUMBERS+=("$MS_TICKET_NUMBER")
    fi
  done
}

ms_lock_holds() {
  local i
  [[ "${MS_LOCK_OWNER:-}" == "$$" && "${MS_LOCK_SUBSHELL:-}" == "$BASH_SUBSHELL" ]] || return 1
  for ((i=0; i<${#MS_LOCK_ROOTS[@]}; i++)); do
    if [[ "${MS_LOCK_ROOTS[i]}" == "$1" ]]; then
      ms_ticket_read "$1/.remote-ssh-lock/${MS_LOCK_TOKENS[i]}" && [[ "$MS_TICKET_NUMBER" == "${MS_LOCK_TICKETS[i]}" ]]
      return "$?"
    fi
  done
  return 1
}

ms_lock_release_all() {
  local i root token
  [[ "${MS_LOCK_OWNER:-}" == "$$" && "${MS_LOCK_SUBSHELL:-}" == "$BASH_SUBSHELL" ]] || return 0
  for ((i=${#MS_LOCK_ROOTS[@]}-1; i>=0; i--)); do
    root="${MS_LOCK_ROOTS[i]}" token="${MS_LOCK_TOKENS[i]}"
    if [[ -e "$root/.remote-ssh-lock/$token/inflight" || -L "$root/.remote-ssh-lock/$token/inflight" ]]; then
      ms_inflight_read "$root/.remote-ssh-lock/$token" || return 1
      if ms_pid_live "$MS_INFLIGHT_PID"; then continue; fi
      rm -- "$root/.remote-ssh-lock/$token/inflight" || return 1
    fi
    if [[ -e "$root/.remote-ssh-lock/$token/armed" || -L "$root/.remote-ssh-lock/$token/armed" ]]; then
      ms_private "$root/.remote-ssh-lock/$token/armed" file && rm -- "$root/.remote-ssh-lock/$token/armed" || return 1
    fi
    if [[ "${MS_LOCK_TICKETS[i]}" == 0 && "$token" == "p$$-"* ]] &&
      ms_private "$root/.remote-ssh-lock/$token" dir &&
      [[ ! -e "$root/.remote-ssh-lock/$token/ticket" && ! -L "$root/.remote-ssh-lock/$token/ticket" ]]; then
      # A failed publication may leave our private sibling file. Do not touch
      # anything whose exact name, owner and private mode are not ours.
      if [[ -e "$root/.remote-ssh-lock/$token/.ticket" || -L "$root/.remote-ssh-lock/$token/.ticket" ]]; then
        ms_private "$root/.remote-ssh-lock/$token/.ticket" file && rm -- "$root/.remote-ssh-lock/$token/.ticket" || return 1
      fi
      rmdir -- "$root/.remote-ssh-lock/$token" || return 1
    elif ms_ticket_read "$root/.remote-ssh-lock/$token" && [[ "$MS_TICKET_NUMBER" == "${MS_LOCK_TICKETS[i]}" ]]; then
      rm -- "$root/.remote-ssh-lock/$token/ticket" && rmdir -- "$root/.remote-ssh-lock/$token" || return 1
    fi
  done
  MS_LOCK_ROOTS=() MS_LOCK_TOKENS=() MS_LOCK_TICKETS=()
}

ms_lock_acquire_one() {
  local root="$1" token ticket=1 temp i busy start=$SECONDS timeout="${MS_LOCK_TIMEOUT:-15}"
  ms_uint "$timeout" && ms_lock_storage_init "$root" || return 1
  token="p$$-$RANDOM$RANDOM"
  (umask 077; mkdir "$root/.remote-ssh-lock/$token") || return 1
  # Register even choosing ownership for reliable cleanup on error/signal.
  MS_LOCK_ROOTS+=("$root") MS_LOCK_TOKENS+=("$token") MS_LOCK_TICKETS+=(0)
  ms_lock_scan "$root" || return 1
  for i in ${MS_SCAN_NUMBERS[@]+"${MS_SCAN_NUMBERS[@]}"}; do ((i < ticket)) || ticket=$((i + 1)); done
  temp="$root/.remote-ssh-lock/$token/.ticket"
  (umask 077; printf '%s\0' "$token" "$$" "$ticket" >"$temp") && mv -- "$temp" "$root/.remote-ssh-lock/$token/ticket" || return 1
  MS_LOCK_TICKETS[${#MS_LOCK_TICKETS[@]}-1]="$ticket"
  while :; do
    ms_lock_scan "$root" || return 1
    busy=0
    for ((i=0; i<${#MS_SCAN_TOKENS[@]}; i++)); do
      [[ "${MS_SCAN_TOKENS[i]}" != "$token" ]] || continue
      if [[ "${MS_SCAN_NUMBERS[i]}" == 0 ]] || ((MS_SCAN_NUMBERS[i] < ticket)) ||
        { [[ "${MS_SCAN_NUMBERS[i]}" == "$ticket" && "${MS_SCAN_TOKENS[i]}" < "$token" ]]; }; then busy=1; fi
    done
    ((busy)) || return 0
    ((SECONDS - start < timeout)) || return 1
    sleep 1
  done
}

ms_lock_acquire() {
  local root existing inserted LC_ALL=C
  local -a sorted=() next=()
  ((${#MS_LOCK_ROOTS[@]} == 0)) || return 1
  # Physical roots sorted in one stable order; a shared prefix/bin is acquired once.
  for root in "$@"; do
    ms_physical_path "$root" || return 1
    root="$MS_PATH"
    [[ -d "$root" && ! -L "$root" ]] || return 1
    next=() inserted=0
    for existing in ${sorted[@]+"${sorted[@]}"}; do
      [[ "$root" != "$existing" ]] || inserted=1
      if ((inserted == 0)) && [[ "$root" < "$existing" ]]; then next+=("$root"); inserted=1; fi
      next+=("$existing")
    done
    ((inserted)) || next+=("$root")
    sorted=("${next[@]}")
  done
  MS_LOCK_OWNER="$$" MS_LOCK_SUBSHELL="$BASH_SUBSHELL"
  ms_lock_install_traps
  for root in ${sorted[@]+"${sorted[@]}"}; do
    if ! ms_lock_acquire_one "$root"; then ms_lock_release_all; return 1; fi
  done
}

ms_lock_read_idle() {
  [[ -e "$1/.remote-ssh-lock" || -L "$1/.remote-ssh-lock" ]] || return 0
  ms_lock_scan "$1" && ((${#MS_SCAN_TOKENS[@]} == 0))
}

# Read-only planning includes prior journal selectors. Call again after acquire;
# if roots differ, release and restart without any lifecycle mutation.
ms_lock_plan() {
  local command="$1" executable="$2" i j journal_active=1
  MS_REQUIRED_LOCKS=("$MS_PREFIX")
  if [[ "$command" != prune ]]; then
    if ms_journal_active && [[ "$MS_BATCH_PHASE" == settled ]]; then journal_active=0; fi
    i=0
    while ((i < ${#MS_ROWS[@]})); do
      j=$((i + 2))
      if ((journal_active)); then
      case "${MS_ROWS[i]}" in
        refresh-intent)
          ms_physical_path "$REPO_DIR" || return 1
          [[ "${MS_ROWS[j+1]}" == "$MS_PATH" ]] || return 1
          MS_REQUIRED_LOCKS+=("$MS_PATH") ;;
        cli-intent) executable=1 ;;
        link-intent|remove-intent)
          [[ "${MS_ROWS[j+2]%/*}" != "$MS_BIN" && "${MS_ROWS[j+3]%/*}" != "$MS_BIN" ]] || executable=1 ;;
      esac
      fi
      i=$((i + 2 + MS_ROWS[i+1]))
    done
    [[ "$executable" == 0 ]] || MS_REQUIRED_LOCKS+=("$MS_BIN")
    [[ "$command" != update ]] || MS_REQUIRED_LOCKS+=("$REPO_DIR")
  fi
}

# A utility is a process too. Publish its PID before allowing any syscall so a
# killed shell cannot release roots while its delayed mv/ln/rm remains alive.
# The child execs the utility in that same PID; it never publishes independently.
ms_inflight_read() {
  local dir="$1" token pid extra
  ms_private "$dir/inflight" file || return 1
  {
    IFS= read -r -d '' token && IFS= read -r -d '' pid || return 1
    extra=""
    if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
  } <"$dir/inflight"
  [[ "$token" == "${dir##*/}" ]] && ms_uint "$pid" && [[ "$pid" != 0 ]] || return 1
  MS_INFLIGHT_PID="$pid"
}

ms_lock_mutate() {
  local root i dir gate child status=0 owner="$$" value
  ((${#MS_LOCK_ROOTS[@]} > 0)) || return 1
  for root in "${MS_LOCK_ROOTS[@]}"; do ms_lock_holds "$root" || return 1; done
  dir="${MS_LOCK_ROOTS[0]}/.remote-ssh-lock/${MS_LOCK_TOKENS[0]}" gate="$RANDOM$RANDOM"
  [[ ! -e "$dir/armed" && ! -L "$dir/armed" ]] || return 1
  (
    while :; do
      # No syscall is allowed before all roots have the in-flight claim.
      ms_pid_live "$owner" || exit 1
      if [[ -e "$dir/armed" || -L "$dir/armed" ]]; then
        ms_private "$dir/armed" file || exit 1
        value="$(cat "$dir/armed" && printf '\001')" || exit 1
        [[ "$value" == "$gate"$'\001' ]] || exit 1
        break
      fi
      sleep 0.05
    done
    if [[ "${MS_MUTATION_CHECK_COUNT:-0}" != 0 ]]; then
      "${MS_MUTATION_CHECK[@]}" || exit 1
    fi
    exec "$@"
  ) &
  child=$!
  for ((i=0; i<${#MS_LOCK_ROOTS[@]}; i++)); do
    dir="${MS_LOCK_ROOTS[i]}/.remote-ssh-lock/${MS_LOCK_TOKENS[i]}"
    if [[ -e "$dir/inflight" || -L "$dir/inflight" ]]; then
      kill -TERM "$child" 2>/dev/null || :
      wait "$child" || :
      return 1
    fi
    (umask 077; printf '%s\0' "${MS_LOCK_TOKENS[i]}" "$child" >"$dir/inflight") || {
      kill -TERM "$child" 2>/dev/null || :
      wait "$child" || :
      return 1
    }
  done
  dir="${MS_LOCK_ROOTS[0]}/.remote-ssh-lock/${MS_LOCK_TOKENS[0]}"
  (umask 077; printf '%s' "$gate" >"$dir/armed") || return 1
  wait "$child" || status=$?
  # These exact private bookkeeping files cannot affect another participant.
  for ((i=0; i<${#MS_LOCK_ROOTS[@]}; i++)); do
    dir="${MS_LOCK_ROOTS[i]}/.remote-ssh-lock/${MS_LOCK_TOKENS[i]}"
    ms_inflight_read "$dir" && [[ "$MS_INFLIGHT_PID" == "$child" ]] && rm -- "$dir/inflight" || return 1
  done
  ms_private "${MS_LOCK_ROOTS[0]}/.remote-ssh-lock/${MS_LOCK_TOKENS[0]}/armed" file &&
    rm -- "${MS_LOCK_ROOTS[0]}/.remote-ssh-lock/${MS_LOCK_TOKENS[0]}/armed" || return 1
  return "$status"
}


# Revalidate live proof in the registered child immediately before exec. The
# explicit arity preserves arbitrary path bytes, including a literal "--".
ms_lock_mutate_guarded() {
  local guard="$1" count="$2" MS_MUTATION_CHECK_COUNT
  shift 2
  ms_uint "$count" && ((count <= $#)) || return 1
  local -a MS_MUTATION_CHECK=("$guard")
  while ((count)); do MS_MUTATION_CHECK+=("$1"); shift; count=$((count - 1)); done
  MS_MUTATION_CHECK_COUNT="${#MS_MUTATION_CHECK[@]}"
  ms_lock_mutate "$@"
}

ms_lock_install_traps() {
  trap 'ms_lock_release_all' EXIT
  trap 'ms_lock_release_all; exit 129' HUP
  trap 'ms_lock_release_all; exit 130' INT
  trap 'ms_lock_release_all; exit 143' TERM
}
