# shellcheck shell=bash
# shellcheck source=/dev/null

remote_ssh_update_check_lib_dir() {
  local script_path="${BASH_SOURCE[0]}"

  case "$script_path" in
    */*) script_path="${script_path%/*}" ;;
    *) script_path="." ;;
  esac
  cd -- "$script_path" && pwd
}

REMOTE_SSH_UPDATE_CHECK_LIB_DIR="$(remote_ssh_update_check_lib_dir)/update-check"

. "$REMOTE_SSH_UPDATE_CHECK_LIB_DIR/toggle.sh"
. "$REMOTE_SSH_UPDATE_CHECK_LIB_DIR/state.sh"
. "$REMOTE_SSH_UPDATE_CHECK_LIB_DIR/time.sh"

unset REMOTE_SSH_UPDATE_CHECK_LIB_DIR
