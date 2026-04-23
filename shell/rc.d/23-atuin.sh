# shellcheck shell=bash

# Bash uses bash-preexec if available.
# Zsh uses native Atuin integration.
# In remote-ssh Bash sessions, persistent shell history is intentionally owned
# by Atuin; standard Bash history file writes are disabled separately.

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

if ! command -v atuin >/dev/null 2>&1; then
    return 0
fi

export ATUIN_CONFIG_DIR="${REMOTE_DOTS_DIR}/atuin"

# Optional toggle for easier debugging or emergency disable.
if [[ "${REMOTE_SSH_ENABLE_ATUIN:-1}" != "1" ]]; then
    return 0
fi

remote_atuin_auto_import_once

if [[ -n "${BASH_VERSION:-}" ]]; then
    # For bash, prefer loading only when bash-preexec is present.
    if [[ -n "${bash_preexec_imported:-}" ]]; then
        eval "$(command atuin init bash --disable-ctrl-r)"
    fi
    return 0
fi

if [[ -n "${ZSH_VERSION:-}" ]]; then
    eval "$(command atuin init zsh)"
    return 0
fi
