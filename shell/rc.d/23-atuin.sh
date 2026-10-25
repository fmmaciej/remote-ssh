# shellcheck shell=bash

# Bash uses bash-preexec if available.
# Zsh uses native Atuin integration.
# Atuin owns persistent history only after its integration initializes.

remote_atuin_auto_import_once() {
    local state_home marker_dir marker_file

    if [[ "${REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT:-1}" != "1" ]]; then
        return 0
    fi

    state_home="${XDG_STATE_HOME:-$HOME/.local/state}"
    marker_dir="${state_home}/remote-ssh"
    marker_file="${marker_dir}/atuin-import-auto.done"

    [[ -f "$marker_file" ]] && return 0

    mkdir -p "$marker_dir" || return 0
    command atuin import auto >/dev/null 2>&1 || return 0
    : > "$marker_file"
}

case $- in
    *i*) ;;
    *) return 0 ;;
esac


remote_atuin_contains() {
    local wanted="$1" item
    shift
    for item; do [[ "$item" != "$wanted" ]] || return 0; done
    return 1
}

remote_atuin_command_context() {
    local depth="${#BASH_LINENO[@]}" root_line
    (( depth > 0 )) || return 1
    root_line="${BASH_LINENO[depth-1]}"
    case "$root_line" in ''|*[!0-9]*|0) return 1 ;; esac
    # The outer interactive call site advances even if history and prompt hooks
    # are disabled. Nested functions/sources keep their caller's input line.
    printf -v "$1" '%s' "$root_line"
}

# The numeric token and mode are private; all other prompt code stays literal.
# shellcheck disable=SC2016,SC2089
remote_atuin_prompt_statement() {
    printf -v "$3" '"${__rs_ap[%s]:-__rs_astale}" "$?" %s %s "${__rs_as:=%s}" "$_"\n' "$1" "$1" "$2" "$1"
}

# shellcheck disable=SC2016
remote_atuin_prompt_vendor_first() {
    local first vendor='__bp_precmd_invoke_cmd "$_"'
    for first in "${!PROMPT_COMMAND[@]}"; do
        case "${PROMPT_COMMAND[first]}" in "$vendor"|"$vendor"$'\n'*) return 0 ;; esac
        return 1
    done
    return 1
}

remote_atuin_remove_pipeline_hook() {
    local hook
    local -a kept=()
    for hook in ${precmd_functions[@]+"${precmd_functions[@]}"}; do
        [[ "$hook" == remote_atuin_restore_prompt_pipeline ]] || kept+=("$hook")
    done
    precmd_functions=(${kept[@]+"${kept[@]}"})
}

remote_atuin_restore_prompt_pipeline() {
    # Remove the temporary global registration before user hooks can edit their
    # array. A local copy of precmd_functions would swallow those user edits.
    remote_atuin_remove_pipeline_hook
    if [[ "${__rs_prompt_captured:-0}" == 1 ]]; then
        # Dynamically scoped to the entrypoint still delegating this prompt.
        # A leftover registration after an interruption only removes itself.
        # shellcheck disable=SC2034
        BP_PIPESTATUS=("${__rs_prompt_pipeline[@]}")
    fi
}

# Compatibility entrypoint for live and cached statements in existing shells.
# The array capture MUST be first; restoring $? cannot restore PIPESTATUS.
# shellcheck disable=SC2016
__rs_astale() {
    local -a __rs_prompt_pipeline=("${PIPESTATUS[@]}")
    # shellcheck disable=SC2034
    local __rs_prompt_captured=1
    # All locals visible through Bash's dynamic scope use private names: user
    # callbacks must still read and update their own global status/force/etc.
    local __rs_prompt_status="$1" __rs_prompt_last="${!#}" __rs_prompt_statement
    local __rs_prompt_replacement='' __rs_prompt_had_vendor=0 __rs_prompt_force=''
    if remote_atuin_prompt_vendor_first; then __rs_prompt_had_vendor=1; fi
    if [[ "$2" == "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" && "${__rs_as:-}" == "$2" &&
        "${__rs_ap[$2]:-}" == __rs_astale ]]; then
        remote_atuin_finish_detached_history "$__rs_prompt_status"
    else
        remote_atuin_prompt_statement "$2" "$3" __rs_prompt_statement
        if [[ "$3" == 1 ]]; then __rs_prompt_replacement='__bp_precmd_invoke_cmd "$_"'$'\n'; fi
        remote_atuin_remove_prompt_prologue "$__rs_prompt_statement" "$__rs_prompt_replacement"
        if [[ "${__rs_as:-}" == "$2" ]]; then unset __rs_as; fi
        # Preserve a newer token in the same input. If its own boundary was
        # lost, a later replay expires it just as the ordinary cleanup guard
        # would; stale code must not suppress dispatch indefinitely.
        remote_atuin_validate_pending_history
    fi
    # Only a replaced vendor statement delegates here. A prepended boundary
    # finishes our entry without moving callbacks ahead of the user's prefix.
    if [[ "$3" == 1 && "$__rs_prompt_had_vendor" == 0 && -z "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" &&
        "${__bp_inside_precmd:-0}" == 0 ]] &&
        declare -F __bp_precmd_invoke_cmd >/dev/null && declare -F __bp_set_ret_value >/dev/null; then
        if remote_atuin_prompt_vendor_first; then __rs_prompt_force=force; fi
        remote_atuin_remove_pipeline_hook
        precmd_functions=(remote_atuin_restore_prompt_pipeline ${precmd_functions[@]+"${precmd_functions[@]}"})
        if __bp_set_ret_value "$__rs_prompt_status" "$__rs_prompt_last"; then
            __bp_precmd_invoke_cmd "$__rs_prompt_force" "$__rs_prompt_last"
        else
            __bp_precmd_invoke_cmd "$__rs_prompt_force" "$__rs_prompt_last"
        fi
        remote_atuin_remove_pipeline_hook
    fi
    return "$__rs_prompt_status"
}

# Modern Bash restores command metadata before each PROMPT_COMMAND array entry.
# Give a prepended boundary its own entry rather than changing the inputs of a
# later wrapper or prefix. Shift only the occupied prefix needed to free index 0.
remote_atuin_install_separate_prompt_boundary() {
    local flags="$1" value="$2" count=0 index
    if [[ "$flags" == *a* ]]; then
        while [[ "${PROMPT_COMMAND[count]+x}" ]]; do ((count += 1)); done
        REMOTE_SSH_ATUIN_PENDING_LAYOUT="$count"
        for ((index=count; index>0; index--)); do
            PROMPT_COMMAND[index]="${PROMPT_COMMAND[index-1]}"
        done
        PROMPT_COMMAND[0]="$REMOTE_SSH_ATUIN_PENDING_PROLOGUE"
    else
        REMOTE_SSH_ATUIN_PENDING_LAYOUT=scalar
        PROMPT_COMMAND=("$REMOTE_SSH_ATUIN_PENDING_PROLOGUE" "$value")
    fi
}

remote_atuin_remove_separate_prompt_boundary() {
    local prologue="$1" flags="$2" layout="${REMOTE_SSH_ATUIN_PENDING_LAYOUT:-}"
    local count index value
    [[ -n "$layout" && "$prologue" == "${REMOTE_SSH_ATUIN_PENDING_PROLOGUE:-}" &&
        "$flags" == *a* && "${PROMPT_COMMAND[0]:-}" == "$prologue" ]] || return 0
    case "$layout" in scalar*) count=1 ;; *) count="$layout" ;; esac
    unset 'PROMPT_COMMAND[0]'
    for ((index=0; index<count; index++)); do
        if [[ "${PROMPT_COMMAND[index+1]+x}" ]]; then
            PROMPT_COMMAND[index]="${PROMPT_COMMAND[index+1]}"
        else
            unset 'PROMPT_COMMAND[index]'
        fi
    done
    unset 'PROMPT_COMMAND[count]'
    # An added array entry is a user edit: retain it rather than forcing a
    # scalar. Otherwise restore its type with the current export flag, including
    # an export/unexport performed by the user while the boundary was pending.
    if [[ "$layout" == scalar* && ( "${!PROMPT_COMMAND[*]}" == 0 || ${#PROMPT_COMMAND[@]} == 0 ) ]]; then
        value="${PROMPT_COMMAND[0]:-}"
        unset PROMPT_COMMAND
        # shellcheck disable=SC2178
        PROMPT_COMMAND="$value"
        [[ "$flags" != *x* ]] || export PROMPT_COMMAND
    fi
}

# Restore the original scalar/array layout when removing an owned boundary.
# shellcheck disable=SC2016,SC2178
remote_atuin_install_prompt_prologue() {
    local declaration flags first=0 value replaced=0 vendor='__bp_precmd_invoke_cmd "$_"'
    declaration="$(declare -p PROMPT_COMMAND 2>/dev/null)" || return 1
    flags="${declaration#declare -}"; flags="${flags%% *}"
    [[ "$flags" != *r* ]] || return 1
    if [[ "$flags" == *a* ]]; then
        for first in "${!PROMPT_COMMAND[@]}"; do break; done
    fi
    value="${PROMPT_COMMAND[first]}"
    REMOTE_SSH_ATUIN_PENDING_REPLACED=
    case "$value" in
        "$vendor") REMOTE_SSH_ATUIN_PENDING_REPLACED="$vendor"; value=; replaced=1 ;;
        "$vendor"$'\n'*) REMOTE_SSH_ATUIN_PENDING_REPLACED="$vendor"$'\n'; value="${value#"$vendor"$'\n'}"; replaced=1 ;;
    esac
    # Keep serialized code short: bash-preexec's Bash 3.2 sanitizer is expensive
    # with long generated statements. __rs_ap marks the live entrypoint;
    # __rs_as authenticates its invocation before status capture.
    REMOTE_SSH_ATUIN_PROMPT_SERIAL=$((${REMOTE_SSH_ATUIN_PROMPT_SERIAL:-0} + 1))
    REMOTE_SSH_ATUIN_PENDING_TOKEN="$REMOTE_SSH_ATUIN_PROMPT_SERIAL"
    # shellcheck disable=SC2034
    __rs_ap[REMOTE_SSH_ATUIN_PENDING_TOKEN]=__rs_astale
    remote_atuin_prompt_statement "$REMOTE_SSH_ATUIN_PENDING_TOKEN" "$replaced" REMOTE_SSH_ATUIN_PENDING_PROLOGUE
    if [[ "$replaced" == 0 ]] && (( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1) )); then
        remote_atuin_install_separate_prompt_boundary "$flags" "$value"
    elif [[ "$flags" == *a* ]]; then
        PROMPT_COMMAND[first]="$REMOTE_SSH_ATUIN_PENDING_PROLOGUE$value"
    else
        PROMPT_COMMAND="$REMOTE_SSH_ATUIN_PENDING_PROLOGUE$value"
    fi
}

# Only the exact generated statement is removed, without evaluating prompt code.
# shellcheck disable=SC2016,SC2090,SC2178
remote_atuin_remove_prompt_prologue() {
    local declaration flags first=0 index value vendor='__bp_precmd_invoke_cmd "$_"'
    local prologue="${1-${REMOTE_SSH_ATUIN_PENDING_PROLOGUE:-}}" statement
    local replacement="${2-${REMOTE_SSH_ATUIN_PENDING_REPLACED:-}}"
    [[ -n "$prologue" ]] || return 0
    statement="${prologue%$'\n'}"
    declaration="$(declare -p PROMPT_COMMAND 2>/dev/null)" || return 0
    flags="${declaration#declare -}"; flags="${flags%% *}"
    [[ "$flags" != *r* ]] || return 0
    if [[ -n "${REMOTE_SSH_ATUIN_PENDING_LAYOUT:-}" ]]; then
        remote_atuin_remove_separate_prompt_boundary "$prologue" "$flags"
        declaration="$(declare -p PROMPT_COMMAND 2>/dev/null)" || return 0
        flags="${declaration#declare -}"; flags="${flags%% *}"
    fi
    if [[ "$flags" == *a* ]]; then
        for first in "${!PROMPT_COMMAND[@]}"; do break; done
    fi
    # bash-preexec may already have reinstated its normal prologue around ours.
    case "${PROMPT_COMMAND[first]:-}" in
        "$vendor"|"$vendor"$'\n'*) replacement= ;;
    esac
    if [[ "$flags" == *a* ]]; then
        for index in "${!PROMPT_COMMAND[@]}"; do
            value="${PROMPT_COMMAND[index]}"
            # Bash 3.2 retains quotes around a quoted replacement literally.
            value="${value//"$prologue"/$replacement}"
            case "$value" in
                "$statement") value="$replacement" ;;
                *$'\n'"$statement") value="${value%"$statement"}$replacement" ;;
            esac
            PROMPT_COMMAND[index]="$value"
        done
    else
        value="${PROMPT_COMMAND//"$prologue"/$replacement}"
        case "$value" in
            "$statement") value="$replacement" ;;
            *$'\n'"$statement") value="${value%"$statement"}$replacement" ;;
        esac
        PROMPT_COMMAND="$value"
    fi
}

remote_atuin_clear_pending_history() {
    local hook
    local -a kept=()
    remote_atuin_remove_prompt_prologue
    remote_atuin_remove_pipeline_hook
    if [[ -n "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" ]]; then unset '__rs_ap[REMOTE_SSH_ATUIN_PENDING_TOKEN]'; fi
    unset REMOTE_SSH_ATUIN_PENDING_ID REMOTE_SSH_ATUIN_PENDING_TIME REMOTE_SSH_ATUIN_PENDING_CONTEXT \
        REMOTE_SSH_ATUIN_PENDING_TOKEN REMOTE_SSH_ATUIN_PENDING_PROLOGUE REMOTE_SSH_ATUIN_PENDING_REPLACED \
        REMOTE_SSH_ATUIN_PENDING_LAYOUT __rs_as
    for hook in ${precmd_functions[@]+"${precmd_functions[@]}"}; do
        [[ "$hook" == remote_atuin_finish_detached_history ]] || kept+=("$hook")
    done
    precmd_functions=(${kept[@]+"${kept[@]}"})
}

remote_atuin_validate_pending_history() {
    local context
    [[ -n "${REMOTE_SSH_ATUIN_PENDING_ID:-}" ]] || return 0
    if ! remote_atuin_command_context context || [[ "$context" != "${REMOTE_SSH_ATUIN_PENDING_CONTEXT:-}" ]]; then
        remote_atuin_clear_pending_history
    fi
}

remote_atuin_prompt_configured() {
    local item
    for item in ${PROMPT_COMMAND[@]+"${PROMPT_COMMAND[@]}"}; do
        item="${item//[[:space:];]/}"
        case "$item" in ''|__bp_interactive_mode) ;; *) return 0 ;; esac
    done
    return 1
}

remote_atuin_finish_detached_history() {
    # A vendor callback supplies $?, while the boundary supplies an argument
    # after its authentication condition. Capture before selecting that value.
    # shellcheck disable=SC2319
    local status=$? id pending_time live_id live_time live_time_set
    status="${1-$status}"
    if [[ -n "${__rs_as:-}" && "$__rs_as" != "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" ]]; then
        unset __rs_as
        return 0
    fi
    # Without the matching first-prompt registration this is only a cleanup
    # guard: an arbitrary wrapper's line number cannot authorize completion.
    if [[ -z "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" ||
        "${__rs_as:-}" != "$REMOTE_SSH_ATUIN_PENDING_TOKEN" ]]; then
        remote_atuin_clear_pending_history
        return 0
    fi
    remote_atuin_validate_pending_history
    id="${REMOTE_SSH_ATUIN_PENDING_ID:-}"
    pending_time="${REMOTE_SSH_ATUIN_PENDING_TIME:-}"
    # Consume before calling external code; failure must not retry an old ID.
    remote_atuin_clear_pending_history
    [[ -n "$id" ]] || return 0
    if ! declare -F __atuin_precmd >/dev/null || ! declare -F __atuin_set_ret_value >/dev/null ||
        ! remote_atuin_available; then
        return 0
    fi
    live_id="${ATUIN_HISTORY_ID:-}"
    live_time="${__atuin_preexec_time:-}"; live_time_set="${__atuin_preexec_time+x}"
    ATUIN_HISTORY_ID="$id"
    __atuin_preexec_time="$pending_time"
    # Both branches preserve the incoming status without triggering errexit.
    if __atuin_set_ret_value "$status"; then
        __atuin_precmd || true
    else
        __atuin_precmd || true
    fi
    ATUIN_HISTORY_ID="$live_id"
    if [[ -n "$live_time_set" ]]; then __atuin_preexec_time="$live_time"; else unset __atuin_preexec_time; fi
}

remote_atuin_detach_history() {
    local id="${ATUIN_HISTORY_ID:-}" pending_time="${__atuin_preexec_time:-}" context
    remote_atuin_validate_pending_history
    [[ "${REMOTE_SSH_ATUIN_INITIALIZED:-0}" == 1 && "${REMOTE_SSH_ATUIN_ACTIVE:-0}" == 1 ]] || return 0
    ATUIN_HISTORY_ID=
    unset __atuin_preexec_time
    case "$id" in ''|__bash_preexec_failure__) return 0 ;; esac
    # Real prompt completion supplies the command's exit status and end time.
    # Without that infrastructure or the backend, discard the local association.
    [[ -n "${bash_preexec_imported:-}" ]] && remote_atuin_prompt_configured || return 0
    declare -F __bp_invoke_precmd_functions >/dev/null || return 0
    declare -F __bp_set_ret_value >/dev/null || return 0
    declare -F __atuin_precmd >/dev/null || return 0
    declare -F __atuin_set_ret_value >/dev/null || return 0
    remote_atuin_available || return 0
    [[ -z "${REMOTE_SSH_ATUIN_PENDING_ID:-}" ]] || return 0
    remote_atuin_command_context context || return 0
    REMOTE_SSH_ATUIN_PENDING_ID="$id"
    REMOTE_SSH_ATUIN_PENDING_TIME="$pending_time"
    REMOTE_SSH_ATUIN_PENDING_CONTEXT="$context"
    remote_atuin_install_prompt_prologue || { remote_atuin_clear_pending_history; return 0; }
    remote_atuin_contains remote_atuin_finish_detached_history ${precmd_functions[@]+"${precmd_functions[@]}"} ||
        precmd_functions+=(remote_atuin_finish_detached_history)
}

remote_atuin_remove_hooks() {
    local hook
    local -a kept=()
    remote_atuin_detach_history
    for hook in ${preexec_functions[@]+"${preexec_functions[@]}"}; do
        remote_atuin_contains "$hook" ${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]+"${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]}"} || kept+=("$hook")
    done
    preexec_functions=(${kept[@]+"${kept[@]}"})
    kept=()
    for hook in ${precmd_functions[@]+"${precmd_functions[@]}"}; do
        remote_atuin_contains "$hook" ${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]+"${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]}"} || kept+=("$hook")
    done
    precmd_functions=(${kept[@]+"${kept[@]}"})
    kept=()
    for hook in ${BLE_ONLOAD[@]+"${BLE_ONLOAD[@]}"}; do
        remote_atuin_contains "$hook" ${REMOTE_SSH_ATUIN_BLE_HOOKS[@]+"${REMOTE_SSH_ATUIN_BLE_HOOKS[@]}"} || kept+=("$hook")
    done
    BLE_ONLOAD=(${kept[@]+"${kept[@]}"})
    remote_atuin_restore_bindings
    REMOTE_SSH_ATUIN_ACTIVE=0
}

remote_atuin_binding() {
    local map="$1" key="$2" line
    if [[ "${REMOTE_SSH_ATUIN_BIND_X:-0}" == 1 ]]; then
        while IFS= read -r line; do
            case "$line" in "\"$key\" "*) printf 'shell|%s\n' "$line"; return 0 ;; esac
        done < <(bind -m "$map" -X 2>/dev/null)
    fi
    while IFS= read -r line; do
        case "$line" in "\"$key\":"*) printf 'readline|%s\n' "$line"; return 0 ;; esac
    done < <(bind -m "$map" -p 2>/dev/null)
    while IFS= read -r line; do
        case "$line" in "\"$key\":"*) printf 'macro|%s\n' "$line"; return 0 ;; esac
    done < <(bind -m "$map" -s 2>/dev/null)
    # Bash 3.2 cannot distinguish an unbound key from an unreadable bind -x.
    if [[ "${REMOTE_SSH_ATUIN_BIND_X:-0}" == 1 ]]; then
        printf 'unbound|\n'
    else
        printf 'unknown|\n'
    fi
}

remote_atuin_apply_binding() {
    local map="$1" key="$2" binding="$3"
    case "$binding" in
        shell\|*) bind -m "$map" -x "${binding#*|}" ;;
        readline\|*|macro\|*) bind -m "$map" "${binding#*|}" ;;
        unbound\|) bind -m "$map" -r "$key" ;;
        *) return 1 ;;
    esac
}

remote_atuin_save_bindings() {
    local map key binding
    if [[ -z "${REMOTE_SSH_ATUIN_BIND_X+x}" ]]; then
        REMOTE_SSH_ATUIN_BIND_X=0
        if bind -X >/dev/null 2>&1; then REMOTE_SSH_ATUIN_BIND_X=1; fi
    fi
    REMOTE_SSH_ATUIN_BINDINGS_BEFORE=()
    REMOTE_SSH_ATUIN_BINDINGS_SAFE=1
    for map in emacs vi-insert vi-command; do
        for key in '\e[A' '\eOA' k; do
            [[ "$key" != k || "$map" == vi-command ]] || continue
            binding="$(remote_atuin_binding "$map" "$key")"
            [[ "$binding" != 'unknown|' ]] || REMOTE_SSH_ATUIN_BINDINGS_SAFE=0
            REMOTE_SSH_ATUIN_BINDINGS_BEFORE+=("$map|$key|$binding")
        done
    done
}

remote_atuin_record_bindings() {
    local entry map key
    REMOTE_SSH_ATUIN_BINDINGS_AFTER=()
    for entry in ${REMOTE_SSH_ATUIN_BINDINGS_BEFORE[@]+"${REMOTE_SSH_ATUIN_BINDINGS_BEFORE[@]}"}; do
        map="${entry%%|*}"; entry="${entry#*|}"; key="${entry%%|*}"
        REMOTE_SSH_ATUIN_BINDINGS_AFTER+=("$(remote_atuin_binding "$map" "$key")")
    done
}

remote_atuin_restore_bindings() {
    local i entry map key previous current
    for i in "${!REMOTE_SSH_ATUIN_BINDINGS_BEFORE[@]}"; do
        entry="${REMOTE_SSH_ATUIN_BINDINGS_BEFORE[$i]}"
        map="${entry%%|*}"; entry="${entry#*|}"
        key="${entry%%|*}"; previous="${entry#*|}"
        current="$(remote_atuin_binding "$map" "$key")"
        # Restore only actual takeovers; keep user edits, including unbinding.
        [[ "$previous" != 'unknown|' && "$previous" != "${REMOTE_SSH_ATUIN_BINDINGS_AFTER[$i]:-}" ]] || continue
        [[ "$current" == "${REMOTE_SSH_ATUIN_BINDINGS_AFTER[$i]:-}" ]] || continue
        remote_atuin_apply_binding "$map" "$key" "$previous" 2>/dev/null || true
    done
    REMOTE_SSH_ATUIN_BINDINGS_BEFORE=()
    REMOTE_SSH_ATUIN_BINDINGS_AFTER=()
}

remote_atuin_available() {
    local executable
    # Match `command atuin` initialization, ignoring aliases and functions.
    executable="$(builtin type -P atuin)" || return 1
    [[ -f "$executable" && -x "$executable" ]] && return 0
    # A removed executable can remain hashed in this interactive shell. Clear
    # only that entry, in the parent shell, before trying the remaining PATH.
    hash -d atuin 2>/dev/null || true
    executable="$(builtin type -P atuin)" || return 1
    [[ -f "$executable" && -x "$executable" ]]
}

remote_atuin_reattach() {
    local hook i entry map key
    # Keep the upstream guard and helpers intact; do not replay its initializer.
    for hook in ${REMOTE_SSH_ATUIN_FUNCTIONS[@]+"${REMOTE_SSH_ATUIN_FUNCTIONS[@]}"} \
        ${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]+"${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]}"} \
        ${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]+"${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]}"} \
        ${REMOTE_SSH_ATUIN_BLE_HOOKS[@]+"${REMOTE_SSH_ATUIN_BLE_HOOKS[@]}"}; do
        declare -F "$hook" >/dev/null || return 1
    done
    remote_atuin_save_bindings
    if [[ "$REMOTE_SSH_ATUIN_BINDINGS_SAFE" == 1 ]]; then
        for i in "${!REMOTE_SSH_ATUIN_BINDINGS_INSTALLED[@]}"; do
            entry="${REMOTE_SSH_ATUIN_BINDINGS_BEFORE[$i]}"
            map="${entry%%|*}"; entry="${entry#*|}"; key="${entry%%|*}"
            if ! remote_atuin_apply_binding "$map" "$key" "${REMOTE_SSH_ATUIN_BINDINGS_INSTALLED[$i]}"; then
                remote_atuin_record_bindings
                remote_atuin_restore_bindings
                return 1
            fi
        done
    fi
    remote_atuin_record_bindings
    for hook in ${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]+"${REMOTE_SSH_ATUIN_PREEXEC_HOOKS[@]}"}; do
        remote_atuin_contains "$hook" ${preexec_functions[@]+"${preexec_functions[@]}"} || preexec_functions+=("$hook")
    done
    for hook in ${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]+"${REMOTE_SSH_ATUIN_PRECMD_HOOKS[@]}"}; do
        remote_atuin_contains "$hook" ${precmd_functions[@]+"${precmd_functions[@]}"} || precmd_functions+=("$hook")
    done
    for hook in ${REMOTE_SSH_ATUIN_BLE_HOOKS[@]+"${REMOTE_SSH_ATUIN_BLE_HOOKS[@]}"}; do
        remote_atuin_contains "$hook" ${BLE_ONLOAD[@]+"${BLE_ONLOAD[@]}"} || BLE_ONLOAD+=("$hook")
    done
}

remote_atuin_bash_init() {
    # An already-open shell may reload while an older pending statement still
    # maps directly to the vendor dispatcher. Keep its serialized format usable.
    if [[ -n "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" && -n "${REMOTE_SSH_ATUIN_PENDING_ID:-}" ]]; then
        __rs_ap[REMOTE_SSH_ATUIN_PENDING_TOKEN]=__rs_astale
    fi
    remote_atuin_validate_pending_history
    local init hook i entry previous
    local -a before_exec=(${preexec_functions[@]+"${preexec_functions[@]}"})
    local -a before_cmd=(${precmd_functions[@]+"${precmd_functions[@]}"})
    local -a before_ble=(${BLE_ONLOAD[@]+"${BLE_ONLOAD[@]}"})
    local -a before_functions=() init_args=(bash --disable-ctrl-r)
    if [[ "${REMOTE_SSH_ENABLE_ATUIN:-1}" != 1 || -z "${bash_preexec_imported:-}" ]] ||
        ! remote_atuin_available; then
        remote_atuin_remove_hooks
        declare -F remote_history_use_bash >/dev/null && remote_history_use_bash
        return 0
    fi
    if [[ "${REMOTE_SSH_ATUIN_ACTIVE:-0}" != 1 && "${REMOTE_SSH_ATUIN_INITIALIZED:-0}" == 1 ]]; then
        remote_atuin_reattach || return 1
        REMOTE_SSH_ATUIN_ACTIVE=1
    elif [[ "${REMOTE_SSH_ATUIN_ACTIVE:-0}" != 1 ]]; then
        # An independently initialized integration belongs to the user.
        [[ "${__atuin_initialized:-}" != true ]] || return 1
        remote_atuin_save_bindings
        [[ "$REMOTE_SSH_ATUIN_BINDINGS_SAFE" == 1 ]] || init_args+=(--disable-up-arrow)
        init="$(command atuin init "${init_args[@]}")" || return 1
        [[ -n "$init" ]] || return 1
        while IFS= read -r hook; do before_functions+=("$hook"); done < <(compgen -A function)
        if ! eval "$init"; then
            # Preserve provenance for 20-fzf.sh: this guard is not external.
            # shellcheck disable=SC2034
            if [[ "${__atuin_initialized:-}" == true ]]; then REMOTE_SSH_ATUIN_FAILED_INIT_GUARD=1; fi
            remote_atuin_record_bindings
            remote_atuin_restore_bindings
            preexec_functions=(${before_exec[@]+"${before_exec[@]}"})
            precmd_functions=(${before_cmd[@]+"${before_cmd[@]}"})
            BLE_ONLOAD=(${before_ble[@]+"${before_ble[@]}"})
            return 1
        fi
        remote_atuin_record_bindings
        REMOTE_SSH_ATUIN_PREEXEC_HOOKS=()
        REMOTE_SSH_ATUIN_PRECMD_HOOKS=()
        REMOTE_SSH_ATUIN_BLE_HOOKS=()
        REMOTE_SSH_ATUIN_FUNCTIONS=()
        REMOTE_SSH_ATUIN_BINDINGS_INSTALLED=()
        for hook in ${preexec_functions[@]+"${preexec_functions[@]}"}; do
            remote_atuin_contains "$hook" ${before_exec[@]+"${before_exec[@]}"} || REMOTE_SSH_ATUIN_PREEXEC_HOOKS+=("$hook")
        done
        for hook in ${precmd_functions[@]+"${precmd_functions[@]}"}; do
            remote_atuin_contains "$hook" ${before_cmd[@]+"${before_cmd[@]}"} || REMOTE_SSH_ATUIN_PRECMD_HOOKS+=("$hook")
        done
        for hook in ${BLE_ONLOAD[@]+"${BLE_ONLOAD[@]}"}; do
            remote_atuin_contains "$hook" ${before_ble[@]+"${before_ble[@]}"} || REMOTE_SSH_ATUIN_BLE_HOOKS+=("$hook")
        done
        while IFS= read -r hook; do
            remote_atuin_contains "$hook" ${before_functions[@]+"${before_functions[@]}"} || REMOTE_SSH_ATUIN_FUNCTIONS+=("$hook")
        done < <(compgen -A function)
        for i in "${!REMOTE_SSH_ATUIN_BINDINGS_BEFORE[@]}"; do
            entry="${REMOTE_SSH_ATUIN_BINDINGS_BEFORE[$i]}"
            entry="${entry#*|}"; previous="${entry#*|}"
            [[ "$previous" != 'unknown|' && "$previous" != "${REMOTE_SSH_ATUIN_BINDINGS_AFTER[$i]}" ]] || continue
            REMOTE_SSH_ATUIN_BINDINGS_INSTALLED[i]="${REMOTE_SSH_ATUIN_BINDINGS_AFTER[$i]}"
        done
        REMOTE_SSH_ATUIN_INITIALIZED=1
        unset REMOTE_SSH_ATUIN_FAILED_INIT_GUARD
        REMOTE_SSH_ATUIN_ACTIVE=1
    fi
    if declare -F remote_history_use_atuin >/dev/null; then remote_history_use_atuin; fi
}

export ATUIN_CONFIG_DIR="${REMOTE_DOTS_DIR}/atuin"

if [[ -n "${BASH_VERSION:-}" ]]; then
    remote_atuin_bash_init || {
        remote_atuin_remove_hooks
        declare -F remote_history_use_bash >/dev/null && remote_history_use_bash
    }
    if [[ "${REMOTE_SSH_ATUIN_ACTIVE:-0}" == 1 ]]; then remote_atuin_auto_import_once; fi
    if declare -F remote_fzf_history_bind >/dev/null; then remote_fzf_history_bind; fi
    return 0
fi

if [[ -n "${ZSH_VERSION:-}" && "${REMOTE_SSH_ENABLE_ATUIN:-1}" == 1 ]] && command -v atuin >/dev/null 2>&1; then
    remote_atuin_auto_import_once
    eval "$(command atuin init zsh)"
fi
