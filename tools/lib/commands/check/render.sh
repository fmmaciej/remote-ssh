# shellcheck shell=bash

ensure_this_file_sourced

ms_check_render() {
  local repo="$1" script="$2" requested="$3" tool i failed=0 code
  shift 3
  printf 'remote-ssh check\n\n'
  if ms_check_environment "$repo" "$script" "$requested"; then :
  else code=$?; ((code != 2)) || return 2; failed=1; fi
  if [[ "$MS_REPORT_LEGACY_HINTS" == 1 ]]; then printf '\nLegacy hints ignored for tool selection.\n'; fi
  printf '\nTools (selected scope)\n'
  if (($# == 0)); then printf '  No managed tools. Choose tools with remote-ssh install TOOL ...\n'; fi
  for tool in "$@"; do
    ms_status_load "$tool" check || return 2
    printf '%s\n  membership: %s\n  support: %s\n' "$tool" "$MS_STATUS_MEMBERSHIP" "$MS_STATUS_SUPPORT"
    printf '  expected: %s\n  observed: VERSION=%s layout=%s\n' "$MS_STATUS_EXPECTED" "$MS_STATUS_VERSION" "$MS_STATUS_LAYOUT"
    printf '  local: %s\n  target: %s\n  path: %s\n  status: %s\n' "$MS_STATUS_LOCAL" "$MS_STATUS_TARGET" "$MS_STATUS_PATH" "$MS_STATUS_TEXT"
    for ((i=0; i<${#MS_STATUS_ALIASES[@]}; i+=4)); do
      printf '  alias: %s status=%s target=%s path=%s\n' "${MS_STATUS_ALIASES[i]}" "${MS_STATUS_ALIASES[i+1]}" "${MS_STATUS_ALIASES[i+2]}" "${MS_STATUS_ALIASES[i+3]}"
    done
    if ms_check_asset_requirements "$tool"; then :
    else code=$?; ((code != 2)) || return 2; failed=1; fi
    if ((MS_STATUS_PROBLEM)); then
      failed=1
      if [[ "$MS_STATUS_SUPPORT" == retired ]]; then
        printf '  next: inspect protected data; remote-ssh uninstall %s requires live ownership proof\n' "$tool"
      else printf '  next: remote-ssh install %s; managed repairs also use remote-ssh update\n' "$tool"; fi
      printf '  PATH: ensure %s wins before external tool directories; protected collisions need manual inspection\n' "$MS_BIN"
    fi
  done
  ms_check_fzf_hint "$repo"
  ((failed == 0))
}
