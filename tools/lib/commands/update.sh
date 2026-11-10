# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_update_usage() {
  cat <<'USAGE'
Usage:
  remote-ssh update
  remote-ssh update check [--quiet] [--write-cache]

Refreshes the checkout, then repairs this installation's managed tool set.
The informational check command does not refresh or install tools.
USAGE
}

remote_ssh_cmd_update_run() {
  local repo_dir="$1"; shift
  (($# == 0)) || { remote_ssh_cmd_update_usage >&2; return 1; }
  command -v git >/dev/null 2>&1 || { printf 'git is required for update.\n' >&2; return 127; }
  remote_ssh_cmd_require_managed_libs
  ms_update_run "$repo_dir"
}

# shellcheck source=/dev/null
. "$TOOLS_COMMANDS_DIR/update/check.sh"

remote_ssh_cmd_update_main() {
  local repo_dir="$1"; shift
  case "${1:-}" in
    '') remote_ssh_cmd_update_run "$repo_dir" ;;
    check) shift; remote_ssh_cmd_update_check_main "$repo_dir" "$@" ;;
    -h|--help) (($# == 1)) || { printf 'Unexpected argument with update help.\n' >&2; remote_ssh_cmd_update_usage >&2; return 1; }; remote_ssh_cmd_update_usage ;;
    *) printf 'Unexpected update argument: %s\n' "$1" >&2; remote_ssh_cmd_update_usage >&2; return 1 ;;
  esac
}
