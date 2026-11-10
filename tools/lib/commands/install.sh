# shellcheck shell=bash
# shellcheck disable=SC2034,SC2015

ensure_this_file_sourced

remote_ssh_cmd_install_usage() {
  cat <<'USAGE'
Usage:
  remote-ssh install [--yes] TOOL [TOOL ...]
  remote-ssh install --profile mini|quick|full [--yes]

Adds selected pinned tools to this installation's managed set.
Without --yes, confirmation requires a terminal. A profile is a one-time selection.
USAGE
}

remote_ssh_cmd_install_main() {
  local repo_dir="$1" yes=0 help=0 profile="" profiles=0 arg tool exe
  shift
  local -a requested=() tools=() skipped=()
  while (($#)); do
    arg="$1"; shift
    case "$arg" in
      --yes) yes=1 ;;
      -h|--help) help=1 ;;
      --profile)
        (($#)) && [[ "$1" != -* ]] || { remote_ssh_cmd_install_usage >&2; return 1; }
        profile="$1"; shift; profiles=$((profiles + 1)) ;;
      --profile=*) profile="${arg#--profile=}"; profiles=$((profiles + 1)) ;;
      -*) printf 'Unknown install option: %s\n' "$arg" >&2; return 1 ;;
      *) requested+=("$arg") ;;
    esac
  done
  ((profiles <= 1)) || { printf 'Select --profile only once.\n' >&2; return 1; }
  if ((profiles)); then
    case "$profile" in mini|quick|full) ;; *) printf 'Unknown install profile: %s\n' "$profile" >&2; return 1 ;; esac
    ((${#requested[@]} == 0)) || { printf 'A profile cannot be combined with tool names.\n' >&2; return 1; }
  fi
  for tool in ${requested[@]+"${requested[@]}"}; do
    [[ "$tool" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.+-]*$ && -f "$TOOLS_DIR/defs/$tool.sh" ]] || { printf 'Unknown tool: %s\n' "$tool" >&2; return 1; }
  done
  if ((help)); then remote_ssh_cmd_install_usage; return 0; fi
  if ((profiles == 0 && ${#requested[@]} == 0)); then remote_ssh_cmd_install_usage >&2; return 1; fi
  remote_ssh_cmd_require_managed_libs
  check_req_tools || return 1
  if ((profiles)); then
    case "$profile" in mini) requested=("${MINI_TOOLS[@]}") ;; quick) requested=("${QUICK_TOOLS[@]}") ;; full) requested=("${DEFAULT_TOOLS[@]}") ;; esac
  fi
  MS_VALUES=()
  for tool in "${requested[@]}"; do ms_append_unique "$tool"; done
  requested=("${MS_VALUES[@]}")
  filter_tools_for_current_platform "${requested[@]}" || return 1
  ((${#REMOTE_SSH_UNKNOWN_TOOLS[@]} == 0)) || { ms_print_selection 'Unknown tools:' "${REMOTE_SSH_UNKNOWN_TOOLS[@]}" >&2; return 1; }
  tools=("${REMOTE_SSH_SUPPORTED_TOOLS[@]+"${REMOTE_SSH_SUPPORTED_TOOLS[@]}"}")
  skipped=("${REMOTE_SSH_UNSUPPORTED_TOOLS[@]+"${REMOTE_SSH_UNSUPPORTED_TOOLS[@]}"}")
  ((${#tools[@]})) || { printf 'No supported tools selected.\n' >&2; return 1; }
  install_cli_preflight && ms_state_load && ms_install_preflight "${tools[@]}" || return 1
  local -a MS_APPROVED=("${MS_PREFLIGHT[@]}")
  exe="$MS_EXECUTABLES"
  [[ -L "$MS_BIN/remote-ssh" && -x "$INSTALL_CLI_SOURCE" ]] || exe=1
  ms_lock_plan install "$exe"
  ms_print_selection 'Selected tools:' "${tools[@]}"
  ((${#skipped[@]} == 0)) || ms_print_selection 'Skipped unsupported tools:' "${skipped[@]}"
  printf 'Install paths\n  prefix: %s\n  bin: %s\n' "$MS_PREFIX" "$MS_BIN"
  ((yes)) || ms_confirm install || return 1
  ms_create_roots "$exe" && ms_lock_acquire "${MS_REQUIRED_LOCKS[@]}" && ms_state_load || return 1
  exe="$MS_EXECUTABLES"
  [[ -L "$MS_BIN/remote-ssh" && -x "$INSTALL_CLI_SOURCE" ]] || exe=1
  ms_lock_plan install "$exe"
  MS_RECOVERY_COMMAND=install
  ms_lock_set_matches && ms_recovery_gate && ms_journal_prepare && install_cli_check_destination && ms_install_preflight "${tools[@]}" && ms_snapshot_equal || {
    printf 'Preflight changed or is protected; retry install.\n' >&2; return 1;
  }
  if [[ "$MS_ADOPTED" == 0 ]]; then
    ms_legacy_hints "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" && ms_migration_commit || return 1
  fi
  ms_recovery_gate || return 1
  MS_OPERATION=install MS_PUBLISH_CLI=1
  ms_install_batch "${tools[@]}" || return 1
  printf 'Done.\n'
  install_print_post_install "$repo_dir"
}
