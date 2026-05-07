# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_install_main() {
  remote_ssh_cmd_require_install_libs

  local repo_dir="$1"
  shift

  local -a tools=("$@")
  local tool

  if ((${#tools[@]} == 0)); then
    tools=()
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && tools+=("$tool")
    done < <(current_default_tools)
  fi

  log_info "Begin."
  install_check_requirements
  if (($# == 0)); then
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && log_info "Skipping unsupported default tool on this platform: $tool"
    done < <(current_unsupported_default_tools)
  fi
  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  install_shell_dir
  install_bin_dir
  install_dots_dir

  log_info "Done."
  install_print_post_install "$repo_dir"
}
