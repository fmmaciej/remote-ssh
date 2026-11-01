# shellcheck shell=bash

[[ -n "${BASH_VERSION:-}" && $- == *i* ]] || return 0
[[ -z "${REMOTE_SSH_HISTORY_REQUEST+x}" ]] || return 0

# Process-local, never exported: a child Bash selects its own backend.
REMOTE_SSH_HISTORY_REQUEST=bash
if [[ "${__atuin_initialized:-}" == true ]]; then
    REMOTE_SSH_HISTORY_REQUEST=external
    return 0
fi
[[ "${REMOTE_SSH_ENABLE_ATUIN:-1}" == 1 ]] || return 0

# Ignore aliases/functions and stale hashes when selecting the initial backend.
remote_atuin_available() {
    local executable
    executable="$(builtin type -P atuin)" || return 1
    if [[ ! -f "$executable" || ! -x "$executable" ]]; then
        hash -d atuin 2>/dev/null || true
        executable="$(builtin type -P atuin)" || return 1
    fi
    [[ -f "$executable" && -x "$executable" ]]
}
remote_atuin_available || return 0

if [[ -z "${bash_preexec_imported:-}" ]]; then
    [[ -r "${REMOTE_ENV_DIR}/tools/vendors/bash-preexec.sh" ]] || return 0
    # Keep this before prompt integrations choose their preexec backend.
    # shellcheck source=/dev/null
    source "${REMOTE_ENV_DIR}/tools/vendors/bash-preexec.sh"
fi
[[ -n "${bash_preexec_imported:-}" ]] || return 0
REMOTE_SSH_HISTORY_REQUEST=atuin
