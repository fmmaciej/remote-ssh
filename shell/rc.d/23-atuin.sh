# shellcheck shell=bash

# Bash uses bash-preexec if available.
# Zsh uses native Atuin integration.

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
