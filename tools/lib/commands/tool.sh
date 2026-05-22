# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_tool_usage() {
  cat <<'EOF' >&2
Usage:
  remote-ssh tool install <tool ...>
  remote-ssh tool list
EOF
}

remote_ssh_cmd_tool_print_lines() {
  local title="$1"
  shift

  printf '%s\n' "$title"
  if (($# == 0)); then
    printf '  [none]\n'
    return 0
  fi

  printf '  %s\n' "$@"
}

remote_ssh_cmd_tool_print_profiles() {
  local profile tool
  local -a tools

  printf 'Install profiles:\n'
  for profile in "${INSTALL_PROFILES[@]}"; do
    tools=()
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && tools+=("$tool")
    done < <(install_profile_tools "$profile")
    printf '  %-5s %s\n' "$profile" "${tools[*]}"
  done
}

remote_ssh_cmd_tool_list() {
  local tool
  local -a expected=() installed=() unsupported=()

  if expected_tools_exists; then
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && expected+=("$tool")
    done < <(read_expected_tools)
  fi

  while IFS= read -r tool; do
    [[ -n "$tool" ]] && installed+=("$tool")
  done < <(managed_installed_tools)

  while IFS= read -r tool; do
    [[ -n "$tool" ]] && unsupported+=("$tool")
  done < <(current_unsupported_default_tools)

  printf 'remote-ssh tool list\n\n'
  remote_ssh_cmd_tool_print_profiles
  printf '\n'
  remote_ssh_cmd_tool_print_lines "Default tools:" "${DEFAULT_TOOLS[@]}"
  printf '\n'
  printf 'Expected tools config: %s\n' "$(expected_tools_file)"
  remote_ssh_cmd_tool_print_lines "Expected tools:" "${expected[@]}"
  printf '\n'
  remote_ssh_cmd_tool_print_lines "Managed installed tools:" "${installed[@]}"
  printf '\n'
  remote_ssh_cmd_tool_print_lines "Unsupported default tools on this platform:" "${unsupported[@]}"
}

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
    list)
      (($# == 0)) || {
        remote_ssh_cmd_tool_usage
        return 1
      }
      remote_ssh_cmd_tool_list
      ;;
    -h|--help)
      remote_ssh_cmd_tool_usage
      ;;
    *)
      remote_ssh_cmd_tool_usage
      return 1
      ;;
  esac
}
