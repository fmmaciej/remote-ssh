# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/guide/common.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/guide/shell_snapshot.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/guide/tools.sh"
# shellcheck disable=SC1091
. "$TOOLS_COMMANDS_DIR/guide/sections.sh"

remote_ssh_cmd_guide_main() {
  local section="${1:-all}"

  case "$section" in
    all) remote_ssh_cmd_guide_print_all ;;
    commands) remote_ssh_cmd_guide_print_commands ;;
    aliases) remote_ssh_cmd_guide_print_aliases ;;
    functions) remote_ssh_cmd_guide_print_functions ;;
    paths) remote_ssh_cmd_guide_print_paths ;;
    git) remote_ssh_cmd_guide_print_git ;;
    tools) remote_ssh_cmd_guide_print_tools ;;
    starship) remote_ssh_cmd_guide_print_starship ;;
    -h|--help)
      remote_ssh_cmd_guide_usage
      return 1
      ;;
    *)
      remote_ssh_cmd_guide_usage
      return 1
      ;;
  esac
}
