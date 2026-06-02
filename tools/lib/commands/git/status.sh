# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/model.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/git/status/render.sh"

remote_ssh_cmd_git_status_usage() {
  cat <<'EOF'
Usage: remote-ssh git status

Shows Git identity config, the remote-ssh session override, and origin remote.
EOF
}

remote_ssh_cmd_git_status() {
  case "${1:-}" in
    -h|--help)
      remote_ssh_cmd_git_status_usage
      return 0
      ;;
  esac
  (($# == 0)) || {
    remote_ssh_cmd_git_status_usage >&2
    return 1
  }

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required.\n' >&2
    return 1
  }

  remote_ssh_cmd_git_status_collect
  remote_ssh_cmd_git_status_render
}
