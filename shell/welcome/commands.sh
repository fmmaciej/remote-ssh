# shellcheck shell=bash

remote_ssh_welcome_load_commands() {
  local repo_dir

  repo_dir="${REMOTE_ENV_DIR:-$(remote_ssh_welcome_repo_dir)}"
  REMOTE_ENV_DIR="$repo_dir"
  export REMOTE_ENV_DIR

  # shellcheck source=/dev/null
  . "$repo_dir/tools/lib/env.sh" 2>/dev/null || return 1
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/commands.lib.sh" 2>/dev/null || return 1
}

remote_ssh_welcome_print_tools() {
  local tool checked=0 ok=0

  remote_ssh_cmd_require_install_libs >/dev/null 2>&1 || {
    printf 'tools:   0 checked / 0 ok\n'
    remote_ssh_welcome_issue tools
    return 0
  }

  if ! read_expected_tools_for_current_platform; then
    printf 'tools:   0 checked / 0 ok\n'
    remote_ssh_welcome_issue tools
    return 0
  fi

  checked="${#REMOTE_SSH_EXPECTED_TOOLS[@]}"
  for tool in "${REMOTE_SSH_EXPECTED_TOOLS[@]}"; do
    if remote_ssh_tool_status_load "$tool" "$TOOLS_DIR/defs" >/dev/null 2>&1 &&
      [[ "$REMOTE_SSH_TOOL_STATUS_PROBLEM" -eq 0 ]]; then
      ok=$((ok + 1))
    fi
  done

  printf 'tools:   %s checked / %s ok\n' "$checked" "$ok"
  if ((checked == 0 || ok < checked || ${#REMOTE_SSH_UNKNOWN_TOOLS[@]} > 0)); then
    remote_ssh_welcome_issue tools
  fi
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
