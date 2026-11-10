# shellcheck shell=bash
# shellcheck disable=SC2034,SC2015

ensure_this_file_sourced

remote_ssh_cmd_uninstall_usage() {
  cat <<'USAGE'
Usage: remote-ssh uninstall [--yes] TOOL [TOOL ...]

Removes all proven own releases of the selected tools and their managed membership.
Foreign or unproved paths remain protected. Without --yes, confirmation requires a terminal.
USAGE
}

remote_ssh_cmd_uninstall_main() {
  local arg tool yes=0 help=0 exe i shown
  local -a requested=() tools=()
  while (($#)); do
    arg="$1"; shift
    case "$arg" in
      --yes) yes=1 ;;
      -h|--help) help=1 ;;
      -*) printf 'Unknown uninstall option: %s\n' "$arg" >&2; return 1 ;;
      *) [[ "$arg" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.+-]*$ ]] || { printf 'Unknown tool: %s\n' "$arg" >&2; return 1; }; requested+=("$arg") ;;
    esac
  done
  if ((help && ${#requested[@]} == 0)); then remote_ssh_cmd_uninstall_usage; return 0; fi
  ((${#requested[@]})) || { remote_ssh_cmd_uninstall_usage >&2; return 1; }
  remote_ssh_cmd_require_managed_libs
  ms_state_load || return 1
  MS_VALUES=()
  for tool in "${requested[@]}"; do
    [[ -f "$TOOLS_DIR/defs/$tool.sh" ]] || ms_row_find tool "$tool" || { printf 'Unknown tool: %s\n' "$tool" >&2; return 1; }
    ms_append_unique "$tool"
  done
  tools=("${MS_VALUES[@]}")
  if ((help)); then remote_ssh_cmd_uninstall_usage; return 0; fi
  ms_uninstall_preflight "${tools[@]}" || { printf 'Cannot inspect protected or unreadable paths; uninstall aborted.\n' >&2; return 1; }
  local -a MS_APPROVED=("${MS_PREFLIGHT[@]}")
  ms_print_selection 'Selected tools:' "${tools[@]}"
  printf 'Owned selectors to remove:\n'
  shown=0
  for ((i=0; i<${#MS_UNINSTALL_LINKS[@]}; i+=5)); do
    if [[ "${MS_UNINSTALL_LINKS[i+2]}" == link ]]; then printf '  %s\n' "${MS_UNINSTALL_LINKS[i+1]}"; shown=1; fi
  done
  ((shown)) || printf '  [none]\n'
  printf 'Owned release scope to remove:\n'
  shown=0
  for ((i=0; i<${#MS_UNINSTALL_ROOTS[@]}; i+=2)); do
    printf '  %s\n' "${MS_UNINSTALL_ROOTS[i+1]}"; shown=1
  done
  ((shown)) || printf '  [none]\n'
  printf 'Managed membership to remove:\n'
  shown=0
  for tool in ${MS_UNINSTALL_TOOLS[@]+"${MS_UNINSTALL_TOOLS[@]}"}; do
    if ms_member_has "$tool"; then printf '  %s\n' "$tool"; shown=1; fi
  done
  ((shown)) || printf '  [none]\n'
  ((${#MS_UNINSTALL_PROTECTED[@]} == 0)) || ms_print_selection 'Protected remains:' "${MS_UNINSTALL_PROTECTED[@]}"
  if ((${#MS_UNINSTALL_TOOLS[@]} == 0)); then printf 'No managed paths to uninstall.\n'; return 0; fi
  exe="$MS_EXECUTABLES"
  ms_lock_plan uninstall "$exe"
  ((yes)) || ms_confirm uninstall || return 1
  ms_create_roots "$exe" && ms_lock_acquire "${MS_REQUIRED_LOCKS[@]}" && ms_state_load || return 1
  ms_lock_plan uninstall "$exe"
  MS_RECOVERY_COMMAND=uninstall
  ms_lock_set_matches && ms_recovery_gate && ms_journal_prepare && ms_uninstall_preflight "${tools[@]}" && ms_snapshot_equal || { printf 'Preflight changed or is protected; retry uninstall.\n' >&2; return 1; }
  if [[ "$MS_ADOPTED" == 0 ]]; then ms_legacy_hints "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools" && ms_migration_commit || return 1; fi
  ms_recovery_gate || return 1
  ms_uninstall_batch "${MS_UNINSTALL_TOOLS[@]}"
}
