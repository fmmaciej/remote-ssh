# shellcheck shell=bash
# shellcheck disable=SC2015

ensure_this_file_sourced
remote_ssh_cmd_list_usage() { printf 'Usage: remote-ssh list [--installed | --all]\n'; }
remote_ssh_cmd_list_render() {
  local mode="$1" tool shown=0
  if [[ "$MS_REPORT_LEGACY_HINTS" == 1 ]]; then printf 'Legacy hints ignored for tool selection.\n'; fi
  printf '%-16s %-18s %-12s %s\n' TOOL MEMBERSHIP SUPPORT STATUS
  for tool in ${MS_NAMES[@]+"${MS_NAMES[@]}"}; do
    if [[ "$mode" == installed ]] && ! ms_member_has "$tool"; then continue; fi
    ms_status_load "$tool" list || return 2
    if [[ "$mode" == default && "$MS_STATUS_MEMBERSHIP" == unmanaged && "$MS_STATUS_SUPPORT" == unsupported ]]; then continue; fi
    printf '%-16s %-18s %-12s %s\n' "$tool" "$MS_STATUS_MEMBERSHIP" "$MS_STATUS_SUPPORT" "$MS_STATUS_TEXT"
    shown=1
  done
  ((shown)) || printf 'No tools found.\n'
}
remote_ssh_cmd_list_main() {
  local BASH_ENV='' ENV=''
  export BASH_ENV ENV
  local mode=default help=0 arg output code
  for arg in "$@"; do
    case "$arg" in
      --installed|--all)
        [[ "$mode" == default || "$mode" == "${arg#--}" ]] || { remote_ssh_cmd_list_usage >&2; return 1; }
        mode="${arg#--}" ;;
      -h|--help) help=1 ;;
      *) printf 'Unexpected list argument: %s\n' "$arg" >&2; return 1 ;;
    esac
  done
  if ((help)); then remote_ssh_cmd_list_usage; return 0; fi
  remote_ssh_cmd_require_managed_libs
  ms_report_begin && ms_report_model || { ms_error 'cannot build complete list; retry after resolving state/inventory'; return 1; }
  if output="$(remote_ssh_cmd_list_render "$mode")"; then code=0; else code=$?; fi
  ((code == 0)) && ms_report_end || return 1
  printf '%s\n' "$output"
}
