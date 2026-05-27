# shellcheck shell=bash
# shellcheck source=/dev/null

remote_ssh_welcome_loader_dir() {
  local script_path="${BASH_SOURCE[0]}"

  case "$script_path" in
    */*) script_path="${script_path%/*}" ;;
    *) script_path="." ;;
  esac
  cd -- "$script_path" && pwd
}

REMOTE_SSH_WELCOME_LOADER_DIR="$(remote_ssh_welcome_loader_dir)"
REMOTE_SSH_WELCOME_MODULE_DIR="$REMOTE_SSH_WELCOME_LOADER_DIR/welcome"

. "$REMOTE_SSH_WELCOME_LOADER_DIR/update-check.lib.sh"

. "$REMOTE_SSH_WELCOME_MODULE_DIR/base.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/toggles.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/issues.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/banner.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/host.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/update.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/commands.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/hw.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/sw.sh"
. "$REMOTE_SSH_WELCOME_MODULE_DIR/runner.sh"

unset REMOTE_SSH_WELCOME_MODULE_DIR
unset REMOTE_SSH_WELCOME_LOADER_DIR
