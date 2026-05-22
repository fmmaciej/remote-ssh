# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_install_usage() {
  cat <<'EOF'
Usage:
  remote-ssh install [tool ...]
  remote-ssh install --profile <mini|quick|full> [--yes]
  remote-ssh install --full [--yes]

Installs selected pinned tools and saves the selected set in:
  ${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools

Without tool arguments, installs the saved expected tool set. Use --profile to
install a named profile. --full is an alias for --profile full.
EOF
}

remote_ssh_cmd_install_print_list() {
  local title="$1"
  shift

  printf '%s\n' "$title"
  if (($# == 0)); then
    printf '  [none]\n'
    return 0
  fi

  printf '  %s\n' "$@"
}

remote_ssh_cmd_install_confirm() {
  local source_label="$1"
  local answer

  if ! [[ -t 0 ]]; then
    printf 'remote-ssh install requires confirmation for %s. Use --yes for non-interactive installs.\n' "$source_label" >&2
    return 1
  fi

  printf '\nInstall %s? [y/N] ' "$source_label"
  read -r answer
  case "$answer" in
    y|Y|yes|YES) return 0 ;;
    *) printf 'Aborted.\n' >&2; return 1 ;;
  esac
}

remote_ssh_cmd_install_main() {
  remote_ssh_cmd_require_install_libs

  local repo_dir="$1"
  shift

  local arg full=0 yes=0 profile="" source_label="selected"
  local -a requested=() tools=() skipped=()
  local tool

  while (($# > 0)); do
    arg="$1"
    case "$arg" in
      --full)
        full=1
        shift
        ;;
      --profile)
        if (($# < 2)) || [[ "$2" == -* ]]; then
          printf 'remote-ssh install --profile requires one of: mini, quick, full\n' >&2
          return 1
        fi
        profile="$2"
        shift 2
        ;;
      --profile=*)
        profile="${arg#--profile=}"
        if [[ -z "$profile" ]]; then
          printf 'remote-ssh install --profile requires one of: mini, quick, full\n' >&2
          return 1
        fi
        shift
        ;;
      --yes)
        yes=1
        shift
        ;;
      --skip-unsupported)
        # Unsupported tools are skipped by default. The flag stays explicit for
        # bootstrap scripts and documentation.
        shift
        ;;
      -h|--help)
        remote_ssh_cmd_install_usage
        return 0
        ;;
      -*)
        printf 'Unknown remote-ssh install option: %s\n' "$arg" >&2
        remote_ssh_cmd_install_usage >&2
        return 1
        ;;
      *)
        requested+=("$arg")
        shift
        ;;
    esac
  done

  if ((full == 1)); then
    if [[ -n "$profile" ]]; then
      printf 'remote-ssh install does not accept both --full and --profile.\n' >&2
      return 1
    fi
    profile="full"
  fi

  if [[ -n "$profile" ]]; then
    if ! install_profile_known "$profile"; then
      printf 'Unknown remote-ssh install profile: %s\n' "$profile" >&2
      printf 'Known profiles: mini quick full\n' >&2
      return 1
    fi
    if ((${#requested[@]} > 0)); then
      printf 'remote-ssh install --profile does not accept explicit tool arguments.\n' >&2
      return 1
    fi
  fi

  log_info "Begin."
  install_check_requirements

  if [[ -n "$profile" ]]; then
    source_label="${profile} profile platform-supported set"
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && requested+=("$tool")
    done < <(current_install_profile_tools "$profile")
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && skipped+=("$tool")
    done < <(current_unsupported_install_profile_tools "$profile")
    tools=("${requested[@]}")

  elif ((${#requested[@]} == 0)); then
    source_label="saved expected tools"
    if ! read_expected_tools_for_current_platform; then
      printf 'No expected tools config found: %s\n' "$(expected_tools_file)" >&2
      printf 'Run: remote-ssh install --profile quick --yes\n' >&2
      printf 'Or install a selected set, for example: remote-ssh install fd rg fzf\n' >&2
      return 1
    fi
    tools=("${REMOTE_SSH_EXPECTED_TOOLS[@]}")
    skipped=("${REMOTE_SSH_UNSUPPORTED_TOOLS[@]}")
    if ((${#REMOTE_SSH_UNKNOWN_TOOLS[@]} > 0)); then
      remote_ssh_cmd_install_print_list "Unknown expected tools:" "${REMOTE_SSH_UNKNOWN_TOOLS[@]}" >&2
    fi
  else
    filter_tools_for_current_platform "${requested[@]}"
    tools=("${REMOTE_SSH_SUPPORTED_TOOLS[@]}")
    skipped=("${REMOTE_SSH_UNSUPPORTED_TOOLS[@]}")
    if ((${#REMOTE_SSH_UNKNOWN_TOOLS[@]} > 0)); then
      remote_ssh_cmd_install_print_list "Unknown tools:" "${REMOTE_SSH_UNKNOWN_TOOLS[@]}" >&2
      return 1
    fi
  fi

  ((${#tools[@]} > 0)) || {
    printf 'No supported tools selected for this platform.\n' >&2
    return 1
  }

  remote_ssh_cmd_install_print_list "Selected tools (${source_label}):" "${tools[@]}"
  if ((${#skipped[@]} > 0)); then
    printf '\n'
    remote_ssh_cmd_install_print_list "Skipped unsupported tools:" "${skipped[@]}"
  fi

  if ((yes == 0 && ${#requested[@]} > 0)); then
    remote_ssh_cmd_install_confirm "$source_label" || return 1
  fi

  install_tools "${tools[@]}"

  log_info "Configuring environment..."
  install_shell_dir
  install_bin_dir
  install_dots_dir
  write_expected_tools "${tools[@]}"

  log_info "Done."
  printf 'Expected tools saved: %s\n' "$(expected_tools_file)"
  install_print_post_install "$repo_dir"
}
