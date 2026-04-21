# shellcheck shell=bash

# This is needed before Atuin init for bash.

if [[ -z "${BASH_VERSION:-}" ]]; then
    return 0
fi

case $- in
    *i*) ;;
    *) return 0 ;;
esac

REMOTE_SSH_BASH_PREEXEC_SH="${REMOTE_ENV_DIR}/tools/vendors/bash-preexec.sh"

if [[ ! -r "$REMOTE_SSH_BASH_PREEXEC_SH" ]]; then
    return 0
fi

# Avoid loading twice.
if [[ -n "${bash_preexec_imported:-}" ]]; then
    return 0
fi

# shellcheck source=/dev/null
source "$REMOTE_SSH_BASH_PREEXEC_SH"
