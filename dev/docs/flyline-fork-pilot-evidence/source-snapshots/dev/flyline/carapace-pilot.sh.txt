# shellcheck shell=bash
# Developer pilot only: adapted from carapace-bin 1.8.2's Bash initializer.
# Upstream: https://github.com/carapace-sh/carapace-bin (MIT).
# No command discovery or generated initialization at shell startup.

_pilot_carapace_complete() {
    local -x COMP_LINE="$COMP_LINE" COMP_POINT="$COMP_POINT"
    local -x COMP_TYPE="${COMP_TYPE:-9}" COMP_WORDBREAKS="$COMP_WORDBREAKS"
    local -x CARAPACE_BRIDGES='' CARAPACE_SHELL=bash
    local -x CARAPACE_SHELL_ALIASES CARAPACE_SHELL_BUILTINS CARAPACE_SHELL_FUNCTIONS
    local -x CARAPACE_SHELL_JOBS CARAPACE_SHELL_VARIABLES
    CARAPACE_SHELL_ALIASES="$(compgen -a)"
    CARAPACE_SHELL_BUILTINS="$(compgen -b)"
    CARAPACE_SHELL_FUNCTIONS="$(compgen -A function)"
    CARAPACE_SHELL_JOBS="$(jobs 2>/dev/null | while read -r line; do
        [[ $line =~ \[([0-9]+)\] ]] && printf '%%%s\n' "${BASH_REMATCH[1]}"
    done)"
    CARAPACE_SHELL_VARIABLES="$(compgen -v)"
    local command="${COMP_WORDS[0]}" data nospace status
    local compline="${COMP_LINE:0:COMP_POINT}"
    COMPREPLY=()
    data=$(printf '%s\n' "${compline}''" | xargs carapace "$command" bash 2>/dev/null)
    status=$?
    if [[ $status != 0 ]]; then
        data=$(printf '%s\n' "${compline}'" | xargs carapace "$command" bash 2>/dev/null)
        status=$?
        if [[ $status != 0 ]]; then
            data=$(printf '%s\n' "${compline}\"" | xargs carapace "$command" bash 2>/dev/null)
            status=$?
        fi
    fi
    if [[ $status != 0 || $data != *$'\001'* ]]; then
        # Bash handles fallback filenames; retain its quoting for spaces.
        compopt +o noquote -o filenames
        return 0
    fi
    IFS=$'\001' read -r -d '' nospace data <<< "$data"
    mapfile -t COMPREPLY < <(printf '%s\n' "$data")
    unset 'COMPREPLY[-1]'
    local IFS=$'\n'
    [[ -n ${COMPREPLY[*]} ]] || COMPREPLY=()
    if ((${#COMPREPLY[@]})); then
        compopt -o noquote
        [[ $nospace != true ]] || compopt -o nospace
    else
        compopt +o noquote -o filenames
    fi
    return 0
}
