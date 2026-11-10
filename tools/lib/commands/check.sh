# shellcheck shell=bash
# shellcheck disable=SC2015
# shellcheck source=/dev/null

ensure_this_file_sourced
. "$TOOLS_COMMANDS_DIR/check/environment.sh"
. "$TOOLS_COMMANDS_DIR/check/render.sh"

remote_ssh_cmd_check_usage() { printf 'Usage: remote-ssh check [TOOL ...]\n'; }
remote_ssh_cmd_check_main() {
  local BASH_ENV='' ENV=''
  export BASH_ENV ENV
  local repo="$1" script="$2" requested="$3" arg help=0 tool output code
  shift 3
  local -a tools=()
  for arg in "$@"; do
    case "$arg" in
      -h|--help) help=1 ;;
      -*) printf 'Unexpected check option: %s\n' "$arg" >&2; return 1 ;;
      *) tools+=("$arg") ;;
    esac
  done
  if ((help && ${#tools[@]} == 0)); then remote_ssh_cmd_check_usage; return 0; fi
  remote_ssh_cmd_require_managed_libs
  ms_report_begin && ms_report_model || { ms_error 'cannot build complete check; retry after resolving state/inventory'; return 1; }
  MS_VALUES=()
  for tool in ${tools[@]+"${tools[@]}"}; do
    ms_name "$tool" && ms_status_known "$tool" || { printf 'Unknown tool: %s\n' "$tool" >&2; return 1; }
    ms_append_unique "$tool"
  done
  tools=("${MS_VALUES[@]+"${MS_VALUES[@]}"}")
  if ((help)); then ms_report_end || return 1; remote_ssh_cmd_check_usage; return 0; fi
  if ((${#tools[@]} == 0)); then
    for tool in ${MS_NAMES[@]+"${MS_NAMES[@]}"}; do ms_member_has "$tool" && tools+=("$tool"); done
  fi
  if output="$(ms_check_render "$repo" "$script" "$requested" ${tools[@]+"${tools[@]}"})"; then code=0; else code=$?; fi
  ((code != 2)) && ms_report_end || { ms_error 'cannot render reliable check'; return 1; }
  printf '%s\n' "$output"
  return "$code"
}
