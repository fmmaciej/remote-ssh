# shellcheck shell=bash

ensure_this_file_sourced

ms_check_path_contains_bin() {
  local part remaining="${PATH-}"
  [[ -d "$MS_BIN" && -n "${PATH+x}" ]] || return 1
  while :; do
    part="${remaining%%:*}"
    if [[ -d "${part:-.}" && "${part:-.}" -ef "$MS_BIN" ]]; then return 0; fi
    case "$remaining" in *:*) remaining="${remaining#*:}" ;; *) break ;; esac
  done
  return 1
}

# Git status must not refresh an index or invoke a configured fsmonitor. No
# diff/textconv, hooks, shell rc, payloads, or loadable libraries are executed.
ms_check_git() {
  GIT_OPTIONAL_LOCKS=0 git -c core.fsmonitor=false -c core.untrackedCache=false -c diff.autoRefreshIndex=false -c core.hooksPath=/dev/null -C "$1" "${@:2}"
}

ms_check_environment() {
  local repo="$1" script="$2" requested="$3" failed=0 branch commit dirty git_status helper
  printf 'Environment\n  platform: %s\n  prefix: %s\n  bin: %s\n' "$MS_REPORT_PLATFORM" "$MS_PREFIX" "$MS_BIN"
  if check_req_tools; then printf '  runtime: ok\n'; else printf '  runtime: failed\n'; failed=1; fi
  printf '\nRepository\n  path: %s\n  script: %s\n' "$repo" "$script"
  if [[ -n "$requested" ]]; then
    printf '  env: %s\n' "$requested"
    if [[ -d "$requested" && "$requested" -ef "$script" ]]; then printf '  env status: ok\n'
    else printf '  env status: mismatch\n'; failed=1; fi
  else printf '  env status: derived\n'; fi
  if ms_check_git "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch="$(ms_check_git "$repo" symbolic-ref --short HEAD 2>/dev/null || :)"
    commit="$(ms_check_git "$repo" rev-parse --short HEAD 2>/dev/null)" || return 2
    git_status="$(ms_check_git "$repo" status --porcelain --untracked-files=normal 2>/dev/null)" || return 2
    dirty=no; [[ -z "$git_status" ]] || dirty=yes
    printf '  git: ok\n  branch: %s\n  commit: %s\n  dirty: %s\n' "${branch:-[detached]}" "$commit" "$dirty"
  else printf '  git: missing-or-invalid\n'; failed=1; fi
  printf '\nPATH\n  bin: %s\n' "$MS_BIN"
  if ms_check_path_contains_bin; then printf '  status: ok\n'
  else printf '  status: missing-from-PATH (executable checks below determine failure)\n'; fi
  printf '\nShell rc\n  file: %s/shell/rc.sh\n' "$repo"
  if [[ -f "$repo/shell/rc.sh" && -r "$repo/shell/rc.sh" ]] &&
    BASH_ENV='' ENV='' bash --noprofile --norc -n "$repo/shell/rc.sh" >/dev/null 2>&1; then printf '  syntax: ok\n'
  else printf '  syntax: failed\n'; failed=1; fi
  printf '\nOptional helpers\n'
  for helper in python3 ssh sk; do
    if command -v "$helper" >/dev/null 2>&1; then printf '  %s: ok\n' "$helper"
    else printf '  %s: missing-optional\n' "$helper"; fi
  done
  ((failed == 0))
}

ms_check_asset_requirements() {
  local tool="$1" asset checksum
  [[ "$MS_STATUS_SUPPORT" == supported ]] || return 0
  ms_select_install_asset "$tool" || return 2
  asset="$MS_SELECTED_ASSET"
  case "$asset" in
    *.zip) command -v unzip >/dev/null 2>&1 || { printf '  capability: missing unzip\n'; return 1; } ;;
    *.tar.xz)
      # BSD tar has built-in xz; GNU tar starts the xz utility.
      if tar --version 2>/dev/null | grep -q 'GNU tar'; then
        command -v xz >/dev/null 2>&1 || { printf '  capability: missing xz\n'; return 1; }
      fi ;;
  esac
  checksum="$(asset_checksum "$asset" ${CHECKSUMS[@]+"${CHECKSUMS[@]}"} 2>/dev/null || :)"
  if [[ -n "$checksum" ]] && ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    printf '  capability: missing sha256sum/shasum\n'; return 1
  fi
}

ms_check_fzf_hint() {
  if [[ "$MS_FZF_HINT" == 1 ]] || ms_member_has fzf; then
    printf '\nfzf retirement\n  status: migration-needed (informational)\n'
    printf '  install: remote-ssh install sk\n  verify: remote-ssh check sk\n'
    printf '  verify pickers in a new remote-ssh shell, then: remote-ssh uninstall fzf\n'
    printf '  guide: %s/docs/install.md#migrating-from-fzf-to-skim\n' "$1"
  fi
}
