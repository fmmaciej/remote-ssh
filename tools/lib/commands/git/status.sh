# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/model.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/diagnose.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/hints.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/render.sh"

remote_ssh_cmd_git_status_usage() {
  cat <<'EOF'
Usage: remote-ssh git status [ssh-host]

Shows the Git author config, origin remote, SSH agent state, and the SSH
account that will be used for Git operations.

If ssh-host is omitted, the command tries to infer it from origin.
EOF
}

remote_ssh_cmd_git_status() {
  local ssh_host="${1:-}"

  case "${1:-}" in
    -h|--help)
      remote_ssh_cmd_git_status_usage
      return 0
      ;;
  esac
  (($# <= 1)) || {
    remote_ssh_cmd_git_status_usage >&2
    return 1
  }

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required.\n' >&2
    return 1
  }

  remote_ssh_cmd_git_status_collect "$ssh_host"
  remote_ssh_cmd_git_status_render
}
