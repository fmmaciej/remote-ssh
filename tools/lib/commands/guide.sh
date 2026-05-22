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
  [[ $# -gt 0 ]] && shift || true

  case "$section" in
    all) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_all ;;
    commands) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_commands ;;
    aliases) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_aliases ;;
    functions) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_functions ;;
    paths) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_paths ;;
    git) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_git ;;
    tools) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_tools ;;
    scripts) (($# <= 1)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_scripts "${1:-}" ;;
    starship) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_starship ;;
    post-install) (($# == 0)) || { remote_ssh_cmd_guide_usage; return 1; }; remote_ssh_cmd_guide_print_post_install ;;
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
