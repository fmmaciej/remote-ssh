# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_update_usage() {
  cat <<'EOF'
Usage:
  remote-ssh update
  remote-ssh update check [--quiet] [--write-cache]

Commands:
  update  Git pull this checkout, then run install
  check   Check whether the configured upstream branch has changed
EOF
}

remote_ssh_cmd_update_run() {
  local repo_dir="$1"
  shift

  (($# == 0)) || {
    remote_ssh_cmd_update_usage >&2
    return 1
  }

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required for remote-ssh update.\n' >&2
    return 127
  }

  [[ -d "$repo_dir/.git" ]] || {
    printf '[ERROR] %s is not a Git checkout.\n' "$repo_dir" >&2
    return 1
  }

  git -C "$repo_dir" pull --ff-only
  remote_ssh_cmd_install_main "$repo_dir"
}

# shellcheck source=/dev/null
. "$TOOLS_COMMANDS_DIR/update/check.sh"

remote_ssh_cmd_update_main() {
  local repo_dir="$1"
  shift

  case "${1:-}" in
    '')
      remote_ssh_cmd_update_run "$repo_dir"
      ;;
    check)
      shift
      remote_ssh_cmd_update_check_main "$repo_dir" "$@"
      ;;
    -h | --help)
      remote_ssh_cmd_update_usage
      ;;
    *)
      printf 'Unknown remote-ssh update command: %s\n' "$1" >&2
      remote_ssh_cmd_update_usage >&2
      return 1
      ;;
  esac
}
