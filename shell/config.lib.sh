# shellcheck shell=bash
# shellcheck source=/dev/null

remote_ssh_config_lib_dir() {
  local script_path="${BASH_SOURCE[0]}"

  case "$script_path" in
    */*) script_path="${script_path%/*}" ;;
    *) script_path="." ;;
  esac
  cd -- "$script_path" && pwd
}

REMOTE_SSH_CONFIG_LIB_DIR="$(remote_ssh_config_lib_dir)/config"

. "$REMOTE_SSH_CONFIG_LIB_DIR/entries.sh"
. "$REMOTE_SSH_CONFIG_LIB_DIR/path.sh"
. "$REMOTE_SSH_CONFIG_LIB_DIR/parse.sh"
. "$REMOTE_SSH_CONFIG_LIB_DIR/markers.sh"
. "$REMOTE_SSH_CONFIG_LIB_DIR/load.sh"

unset REMOTE_SSH_CONFIG_LIB_DIR
