# shellcheck shell=bash

remote_ssh_welcome_load_commands() {
  local BASH_ENV='' ENV=''
  export BASH_ENV ENV
  local repo_dir

  repo_dir="${REMOTE_ENV_DIR:-$(remote_ssh_welcome_repo_dir)}"
  REMOTE_ENV_DIR="$repo_dir"
  export REMOTE_ENV_DIR

  # shellcheck source=/dev/null
  . "$repo_dir/tools/lib/status.lib.sh" 2>/dev/null || return 1
}

remote_ssh_welcome_print_tools() {
  local BASH_ENV='' ENV=''
  export BASH_ENV ENV
  local checked=0

  if ! declare -F ms_report_begin >/dev/null || ! ms_report_begin; then
    printf 'tools:   unavailable (run remote-ssh check)\n'
    remote_ssh_welcome_issue tools
    return 0
  fi
  if [[ "$MS_ADOPTED" == 0 ]]; then
    printf 'tools:   uninitialized (run remote-ssh check)\n'
    return 0
  fi
  local i=0
  while ((i < ${#MS_ROWS[@]})); do
    [[ "${MS_ROWS[i]}" != member ]] || checked=$((checked + 1))
    i=$((i + 2 + MS_ROWS[i+1]))
  done
  if ! ms_report_end; then
    printf 'tools:   unavailable (run remote-ssh check)\n'; remote_ssh_welcome_issue tools; return 0
  fi
  printf 'tools:   %s managed (remote-ssh check for health)\n' "$checked"
  return 0
}

remote_ssh_welcome_requirement_ok() {
  local reqs="$1" req

  [[ -n "$reqs" ]] || return 0
  while IFS= read -r req; do
    req="$(remote_ssh_welcome_trim "$req")"
    [[ -n "$req" ]] || continue
    command -v "$req" >/dev/null 2>&1 || return 1
  done < <(printf '%s\n' "$reqs" | tr ',' '\n')
}

remote_ssh_welcome_path_ok() {
  local rel_path="$1"

  [[ -n "$rel_path" ]] || return 0
  [[ -e "${REMOTE_ENV_DIR}/${rel_path}" ]]
}

remote_ssh_welcome_print_scripts() {
  local checked=0 ok=0
  local name _kind requirements _purpose _example entrypoint backend _docs _use_when

  while IFS='|' read -r name _kind requirements _purpose _example entrypoint backend _docs _use_when; do
    [[ -n "$name" ]] || continue
    checked=$((checked + 1))
    if remote_ssh_welcome_path_ok "$entrypoint" &&
      remote_ssh_welcome_path_ok "$backend" &&
      remote_ssh_welcome_requirement_ok "$requirements"; then
      ok=$((ok + 1))
    fi
  done < <(remote_ssh_cmd_scripts_entries)

  printf 'scripts: %s checked / %s ok\n' "$checked" "$ok"
  if ((checked == 0 || ok < checked)); then
    remote_ssh_welcome_issue scripts
  fi
}
