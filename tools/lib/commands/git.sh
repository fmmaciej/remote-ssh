# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/common.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/setup.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status.sh"

remote_ssh_cmd_git_usage() {
  cat <<'EOF'
Usage: remote-ssh git <command> [args]

Commands:
  setup              Enable bundled Git defaults
  status             Report Git identity, session override, and origin
EOF
}

remote_ssh_cmd_git_main() {
  local subcommand="${1:-}"

  case "$subcommand" in
    ''|-h|--help)
      remote_ssh_cmd_git_usage
      ;;
    setup)
      shift
      remote_ssh_cmd_git_setup "$@"
      ;;
    status)
      shift
      remote_ssh_cmd_git_status "$@"
      ;;
    *)
      printf 'Unknown remote-ssh git command: %s\n' "$subcommand" >&2
      remote_ssh_cmd_git_usage >&2
      return 1
      ;;
  esac
}
