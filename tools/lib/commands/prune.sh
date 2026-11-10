# shellcheck shell=bash
# shellcheck disable=SC2015
# shellcheck disable=SC2034

ensure_this_file_sourced
remote_ssh_cmd_prune_usage() { printf 'Usage: remote-ssh prune [--apply]\n'; }

ms_prune_catalog() {
  local entry tool
  MS_PRUNE_TOOLS=()
  ms_inventory_children "$TOOLS_DIR/defs" || return 1
  for entry in ${MS_INVENTORY[@]+"${MS_INVENTORY[@]}"}; do
    [[ "$entry" == *.sh ]] || continue
    [[ -f "$entry" && ! -L "$entry" && -r "$entry" ]] || return 1
    tool="${entry##*/}" tool="${tool%.sh}"
    ms_name "$tool" && load_defs "$TOOLS_DIR/defs" "$tool" || return 1
    MS_PRUNE_TOOLS+=("$TOOL_NAME")
  done
}
ms_prune_known_name() {
  local tool
  for tool in ${MS_PRUNE_TOOLS[@]+"${MS_PRUNE_TOOLS[@]}"}; do
    case "$1" in "$tool"-*) return 0 ;; esac
  done
  return 1
}

ms_prune_protected() {
  local root="$1" target
  ms_claimed_path "$root" && return 0
  for target in ${MS_PRUNE_TARGETS[@]+"${MS_PRUNE_TARGETS[@]}"}; do
    case "$target" in "$root/"*) return 0 ;; esac
  done
  return 1
}

ms_prune_collect() {
  local link target status
  [[ -d "$MS_BIN" && ! -L "$MS_BIN" && -r "$MS_BIN" && -x "$MS_BIN" ]] || return 1
  ms_prune_catalog && ms_inventory_live && ms_claims_collect prune || return 1
  MS_PRUNE_TARGETS=()
  # Resolve EVERY producer result before accepting any candidate, even links
  # which protect a different release. Failure cannot become a partial picture.
  for link in ${MS_LIVE_LINKS[@]+"${MS_LIVE_LINKS[@]}"}; do
    if target="$(remote_ssh_link_target_path "$link" && printf '\001')"; then
      target="${target%$'\001'}" target="${target%$'\n'}"
      MS_PRUNE_TARGETS+=("$target")
    else status=$?; ((status == 1)) || return 1; fi
  done
}

# Executed in the registered child immediately before rm. It does not run
# recovery or write a state generation, even when an unrelated batch is pending.
ms_prune_delete_guard() {
  local root="$1" prefix="$MS_PREFIX" bin="$MS_BIN" status
  ms_state_load && [[ "$prefix" == "$MS_PREFIX" && "$bin" == "$MS_BIN" ]] &&
    ms_prune_collect && [[ "${root%/*}" == "$MS_PREFIX" ]] &&
    ms_prune_known_name "${root##*/}" && remote_ssh_release_validate "$root" || return 1
  if ms_prune_protected "$root"; then return 1; else status=$?; ((status == 1)); fi
}

ms_prune_render() {
  local apply="$1" dir status found=0
  local -a releases=("${MS_LIVE_RELEASES[@]+"${MS_LIVE_RELEASES[@]}"}")
  if ((apply)); then printf 'remote-ssh prune --apply\n'; else printf 'remote-ssh prune (dry-run)\n'; fi
  for dir in ${releases[@]+"${releases[@]}"}; do
    if ms_prune_known_name "${dir##*/}"; then :
    else status=$?; ((status == 1)) || return 1; continue; fi
    if ! remote_ssh_release_validate "$dir"; then printf 'protected: %s (legacy or invalid ownership record)\n' "$dir"; continue; fi
    if ms_prune_protected "$dir"; then continue
    else status=$?; ((status == 1)) || return 1; fi
    found=1
    if ((apply)); then
      ms_lock_mutate_guarded ms_prune_delete_guard 1 "$dir" rm -rf -- "$dir" || return 1
      printf 'removed: %s\n' "$dir"
    else printf 'candidate: %s\n' "$dir"; fi
  done
  ((found)) || printf 'No prune candidates.\n'
}

remote_ssh_cmd_prune_main() {
  local BASH_ENV='' ENV=''
  export BASH_ENV ENV
  local apply=0 help=0 arg output
  for arg in "$@"; do
    case "$arg" in --apply) apply=1 ;; -h|--help) help=1 ;; *) printf 'Unknown prune argument: %s\n' "$arg" >&2; return 1 ;; esac
  done
  if ((help)); then remote_ssh_cmd_prune_usage; return 0; fi
  remote_ssh_cmd_require_managed_libs
  ms_report_begin && ms_prune_collect || { ms_error "prune aborted: cannot inspect $INSTALL_PREFIX / $INSTALL_BIN_DIR or complete claims"; return 1; }
  if ((apply)) && [[ -d "$MS_PREFIX" ]]; then
    ms_lock_acquire "$MS_PREFIX" && ms_state_load && ms_prune_collect || return 1
    ms_prune_render 1
  else
    output="$(ms_prune_render 0)" && ms_report_end || return 1
    printf '%s\n' "$output"
  fi
}
