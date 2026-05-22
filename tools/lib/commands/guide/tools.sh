# shellcheck shell=bash
# shellcheck disable=SC2153

ensure_this_file_sourced

remote_ssh_cmd_guide_default_tool_report() {
  local repo_dir

  repo_dir="$(remote_ssh_cmd_guide_repo_dir)"
  [[ "$repo_dir" == "$(cd "$REPO_DIR" && pwd)" ]] || {
    printf '[failed to inspect default tools]\n'
    return 1
  }
  remote_ssh_cmd_require_install_libs

  case "$1" in
    supported) current_default_tools ;;
    unsupported) current_unsupported_default_tools ;;
  esac
}

remote_ssh_cmd_guide_print_install_profiles() {
  local profile tool
  local -a tools

  printf 'Install profiles\n'
  for profile in "${INSTALL_PROFILES[@]}"; do
    tools=()
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && tools+=("$tool")
    done < <(install_profile_tools "$profile")
    printf '  %-5s remote-ssh install --profile %s\n' "$profile" "$profile"
    printf '        %s\n' "${tools[*]}"
  done
}

remote_ssh_cmd_guide_print_tools() {
  local supported unsupported

  remote_ssh_cmd_require_install_libs

  cat <<'EOF'
Tools
  install      remote-ssh install
  install mini remote-ssh install --profile mini
  install quick remote-ssh install --profile quick
  install all  remote-ssh install --full
  list         remote-ssh tool list
  check        remote-ssh check --strict
  doctor       remote-ssh doctor
  prune        remote-ssh prune
  prune apply  remote-ssh prune --apply

EOF

  remote_ssh_cmd_guide_print_install_profiles
  printf '\n'
  printf 'Default tools on this platform\n'

  if supported="$(remote_ssh_cmd_guide_default_tool_report supported 2>/dev/null)"; then
    remote_ssh_cmd_guide_print_prefixed_lines "$supported"
  else
    printf '  [failed to inspect default tools]\n'
  fi

  printf '\nUnsupported default tools on this platform\n'
  if unsupported="$(remote_ssh_cmd_guide_default_tool_report unsupported 2>/dev/null)"; then
    remote_ssh_cmd_guide_print_prefixed_lines "$unsupported"
  else
    printf '  [failed to inspect unsupported tools]\n'
  fi
}
