# shellcheck shell=bash

remote_ssh_update_check_enabled() {
  case "${REMOTE_SSH_UPDATE_CHECK:-1}" in
    0 | false | no | off) return 1 ;;
    *) return 0 ;;
  esac
}
