# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/ssh/common.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/ssh/status/agent.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/ssh/setup.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/ssh/status.sh"

remote_ssh_cmd_ssh_usage() {
  cat <<'EOF'
Usage: remote-ssh ssh <command> [args]

Commands:
  setup          Enable bundled SSH alias includes
  status [host]  Report SSH config and agent state
EOF
}

remote_ssh_cmd_ssh_main() {
  local subcommand="${1:-}"

  case "$subcommand" in
    '' | -h | --help)
      remote_ssh_cmd_ssh_usage
      ;;
    setup)
      shift
      remote_ssh_cmd_ssh_setup "$@"
      ;;
    status)
      shift
      remote_ssh_cmd_ssh_status "$@"
      ;;
    *)
      printf 'Unknown remote-ssh ssh command: %s\n' "$subcommand" >&2
      remote_ssh_cmd_ssh_usage >&2
      return 1
      ;;
  esac
}
