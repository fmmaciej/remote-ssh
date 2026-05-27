# shellcheck shell=bash

remote_ssh_welcome_color_enabled() {
  [[ -z "${NO_COLOR:-}" ]] || return 1
  ! remote_ssh_welcome_bool_disabled "${REMOTE_SSH_WELCOME_COLOR:-1}"
}

remote_ssh_welcome_banner_enabled() {
  ! remote_ssh_welcome_bool_disabled "${REMOTE_SSH_WELCOME_BANNER:-1}"
}

remote_ssh_welcome_debug_enabled() {
  ! remote_ssh_welcome_bool_disabled "${REMOTE_SSH_WELCOME_DEBUG:-0}" &&
    [[ -n "${REMOTE_SSH_WELCOME_DEBUG:-}" ]]
}
