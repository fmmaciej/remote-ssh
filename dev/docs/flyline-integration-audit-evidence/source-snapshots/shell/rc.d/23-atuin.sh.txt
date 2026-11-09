# shellcheck shell=bash

case $- in *i*) ;; *) return 0 ;; esac
# Return before probes, import, bindings, or history changes on rcrc.
if [[ -n "${BASH_VERSION:-}" && -n "${REMOTE_SSH_HISTORY_BACKEND+x}" ]]; then return 0; fi

remote_atuin_auto_import_once() {
    local marker_dir marker_file
    [[ "${REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT:-1}" == 1 ]] || return 0
    marker_dir="${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh"
    marker_file="${marker_dir}/atuin-import-auto.done"
    [[ ! -f "$marker_file" ]] || return 0
    mkdir -p "$marker_dir" || return 0
    command atuin import auto >/dev/null 2>&1 || return 0
    : > "$marker_file"
}

remote_atuin_eval_init() { builtin eval "$1"; }

remote_atuin_bash_init() {
    local init helper saved_bind='' statement valid=1 aliases_enabled=0
    local -a before_exec=(${preexec_functions[@]+"${preexec_functions[@]}"})
    local -a before_cmd=(${precmd_functions[@]+"${precmd_functions[@]}"})
    local -a before_ble=(${BLE_ONLOAD[@]+"${BLE_ONLOAD[@]}"})
    local -a bindings=()
    # Reject an unreplaceable user function before even requesting init code.
    # The disposable child cannot alter the parent's function or attributes.
    if builtin declare -F bind >/dev/null; then
        (builtin unset -f bind) 2>/dev/null || return 1
        saved_bind="$(builtin declare -f bind)" || return 1
    fi
    init="$(command atuin init bash --disable-up-arrow --disable-ctrl-r --disable-ai)" || return 1
    [[ -n "$init" ]] || return 1
    if builtin shopt -q expand_aliases; then aliases_enabled=1; fi
    builtin shopt -u expand_aliases || return 1
    # The pinned initializer writes private dispatch macros even with both
    # default groups disabled. Defer these writes until eval/validation succeed:
    # Bash 3.2 cannot snapshot arbitrary existing bind -x commands for rollback.
    # This queue is local to this one startup attempt, never a reload protocol.
    # shellcheck disable=SC2329 # Invoked by the evaluated pinned initializer.
    if function bind() {
        local arg quoted
        for arg; do
            case "$arg" in
                -p|-P|-s|-S|-X|-v|-V|-q|-l)
                    builtin bind "$@"; return $? ;;
            esac
        done
        printf -v quoted '%q ' "$@"
        bindings+=("builtin bind $quoted")
    }; then
        :
    else
        valid=0
    fi
    if [[ "$valid" == 1 ]] && remote_atuin_eval_init "$init"; then
        for helper in __atuin_preexec __atuin_precmd __atuin_history atuin-bind; do
            if ! declare -F "$helper" >/dev/null; then valid=0; break; fi
        done
        [[ "${__atuin_initialized:-}" == true &&
            " ${preexec_functions[*]} " == *' __atuin_preexec '* &&
            " ${precmd_functions[*]} " == *' __atuin_precmd '* ]] || valid=0
        if [[ "$valid" == 1 && -z "${ATUIN_NOBIND:-}" ]]; then
            # Keep vi-command / and Ctrl-R (redo), plus ordinary Up/k.
            atuin-bind -m emacs '\C-r' atuin-search-emacs &&
                atuin-bind -m vi-insert '\C-r' atuin-search-viins || valid=0
        fi
    else
        valid=0
    fi
    # Redefinition keeps a pre-existing export attribute; do not unset first.
    # Alias expansion remains off while parsing the saved function definition.
    if [[ -n "$saved_bind" ]]; then
        builtin eval "$saved_bind" || valid=0
    else
        builtin unset -f bind || valid=0
    fi
    if [[ "$aliases_enabled" == 1 ]]; then
        builtin shopt -s expand_aliases || valid=0
    else
        builtin shopt -u expand_aliases || valid=0
    fi
    # Check the queued Readline operations in an inherited keymap first. A bad
    # application must not leave an earlier Ctrl-R write in the parent, even
    # without skim or readable Bash 3.2 shell-command bindings.
    if [[ "$valid" == 1 ]] && ! (
        for statement in "${bindings[@]}"; do eval "$statement" || exit 1; done
    ); then valid=0; fi
    if [[ "$valid" == 1 ]]; then
        for statement in "${bindings[@]}"; do
            eval "$statement" || { valid=0; break; }
        done
    fi
    [[ "$valid" != 1 ]] || return 0
    # Preserve callbacks/HISTFILE. Preflight catches deterministic bind errors.
    # A transient parent-replay failure is best-effort: Bash 3.2 cannot recover
    # already overwritten shell bindings; skim can reclaim editable Ctrl-R.
    # No default Up/k/vi-command bindings were requested by this initializer.
    preexec_functions=(${before_exec[@]+"${before_exec[@]}"})
    precmd_functions=(${before_cmd[@]+"${before_cmd[@]}"})
    BLE_ONLOAD=(${before_ble[@]+"${before_ble[@]}"})
    return 1
}

if [[ -n "${BASH_VERSION:-}" ]]; then
    # Direct module users must run the early selector as well; full rc always
    # reaches it before Starship. Do not load preexec late here.
    if [[ "${__atuin_initialized:-}" == true ]]; then
        REMOTE_SSH_HISTORY_BACKEND=external
        return 0
    fi
    export ATUIN_CONFIG_DIR="${REMOTE_DOTS_DIR}/atuin"
    if [[ "${REMOTE_SSH_HISTORY_REQUEST:-bash}" == atuin ]] && remote_atuin_bash_init; then
        REMOTE_SSH_HISTORY_BACKEND=atuin
        HISTFILE=
        remote_atuin_auto_import_once
    else
        REMOTE_SSH_HISTORY_BACKEND=bash
        if declare -F remote_skim_history_bind >/dev/null; then remote_skim_history_bind; fi
    fi
    return 0
fi

# Preserve the existing direct-module Zsh integration; rc.sh itself is Bash-only.
export ATUIN_CONFIG_DIR="${REMOTE_DOTS_DIR}/atuin"
if [[ -n "${ZSH_VERSION:-}" && "${REMOTE_SSH_ENABLE_ATUIN:-1}" == 1 ]] && command -v atuin >/dev/null 2>&1; then
    remote_atuin_auto_import_once
    eval "$(command atuin init zsh)"
fi
