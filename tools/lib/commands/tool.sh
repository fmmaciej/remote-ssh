# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_tool_main() {
  remote_ssh_cmd_require_install_libs

  local subcommand="${1:-}"
  shift || true

  case "$subcommand" in
    install)
      (($# > 0)) || {
        printf 'Usage: remote-ssh tool install <tool ...>\n' >&2
        return 1
      }
      install_check_requirements
      install_tools "$@"
      ;;
    *)
      remote_ssh_usage >&2
      return 1
      ;;
  esac
}
